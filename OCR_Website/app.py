import os
import zipfile
import tempfile
import shutil
import logging
import time
import threading
import signal
import multiprocessing
import hashlib
from concurrent.futures import ProcessPoolExecutor, as_completed
from collections import deque
from flask import Flask, render_template, request, send_file, jsonify, Response, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from flask_wtf import FlaskForm
from flask_mail import Mail, Message
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
from itsdangerous import URLSafeTimedSerializer
import ocrmypdf
from pathlib import Path
import PyPDF2  # Add PyPDF2 for PDF page counting
import subprocess  # For calling ghostscript

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Store logs in memory for retrieval
log_buffer = deque(maxlen=100)  # Store last 100 log entries

class LogHandler(logging.Handler):
    def emit(self, record):
        log_entry = self.format(record)
        log_buffer.append({
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'level': record.levelname,
            'message': record.getMessage()
        })

# Add the custom handler to the logger
log_handler = LogHandler()
log_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(log_handler)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 1.5 * 1024 * 1024 * 1024  # Increased to 1.5GB max file size

# Use environment variable for secret key or generate a random one
import secrets
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', secrets.token_hex(16))

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///users.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Mail configuration
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', '587'))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

# Initialize extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
mail = Mail(app)

app.config['CACHE_FOLDER'] = 'ocr_cache'  # Folder to store processed files for caching
app.config['USE_RELOADER'] = False  # Disable auto-reloader to prevent server restart during processing
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}  # Only allow PDF files

# Ensure upload and cache directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['CACHE_FOLDER'], exist_ok=True)
os.makedirs('instance', exist_ok=True)

# User model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(60), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

# Document Review models for Expert Witness Reports
class DocumentReviewSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    case_name = db.Column(db.String(200), nullable=False)
    case_number = db.Column(db.String(100))
    expert_name = db.Column(db.String(100), nullable=False)
    expert_title = db.Column(db.String(200))
    review_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    # Relationship to documents
    documents = db.relationship('ReviewedDocument', backref='session', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"DocumentReviewSession('{self.case_name}', '{self.expert_name}')"

class ReviewedDocument(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('document_review_session.id'), nullable=False)
    
    # Document metadata
    original_filename = db.Column(db.String(500), nullable=False)
    document_title = db.Column(db.String(500))
    document_type = db.Column(db.String(100))  # Medical Record, Legal Document, Report, etc.
    document_date = db.Column(db.Date)
    document_author = db.Column(db.String(200))
    document_source = db.Column(db.String(200))  # Hospital, Clinic, Attorney, etc.
    
    # File information
    file_size_mb = db.Column(db.Float)
    page_count = db.Column(db.Integer)
    file_path = db.Column(db.String(1000))  # Path in uploaded structure
    
    # OCR and processing info
    ocr_processed = db.Column(db.Boolean, default=False)
    processing_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    has_text = db.Column(db.Boolean, default=False)
    
    # Expert review information
    review_notes = db.Column(db.Text)
    relevance_rating = db.Column(db.Integer)  # 1-5 scale
    key_findings = db.Column(db.Text)
    
    def __repr__(self):
        return f"ReviewedDocument('{self.original_filename}', '{self.document_type}')"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Forms
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is already taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already taken. Please choose a different one.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RequestResetForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError('There is no account with that email. You must register first.')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')

# Document Review Forms
class DocumentReviewSessionForm(FlaskForm):
    case_name = StringField('Case Name', validators=[DataRequired(), Length(min=2, max=200)])
    case_number = StringField('Case Number', validators=[Length(max=100)])
    expert_name = StringField('Expert Name', validators=[DataRequired(), Length(min=2, max=100)])
    expert_title = StringField('Expert Title/Credentials', validators=[Length(max=200)])
    submit = SubmitField('Create Review Session')

class DocumentEditForm(FlaskForm):
    document_title = StringField('Document Title', validators=[Length(max=500)])
    document_type = StringField('Document Type', validators=[Length(max=100)])
    document_date = StringField('Document Date (YYYY-MM-DD)')
    document_author = StringField('Document Author', validators=[Length(max=200)])
    document_source = StringField('Document Source', validators=[Length(max=200)])
    review_notes = TextAreaField('Review Notes')
    relevance_rating = SelectField('Relevance Rating', choices=[(1, '1 - Not Relevant'), (2, '2 - Slightly Relevant'), (3, '3 - Moderately Relevant'), (4, '4 - Very Relevant'), (5, '5 - Highly Relevant')], coerce=int)
    key_findings = TextAreaField('Key Findings')
    submit = SubmitField('Update Document')

# Helper functions
def get_reset_token(user, expires_sec=1800):
    s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return s.dumps({'user_id': user.id})

def verify_reset_token(token, expires_sec=1800):
    s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        user_id = s.loads(token, max_age=expires_sec)['user_id']
    except:
        return None
    return User.query.get(user_id)

def send_reset_email(user):
    token = get_reset_token(user)
    msg = Message('Password Reset Request',
                  sender=app.config['MAIL_DEFAULT_SENDER'],
                  recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('reset_token', token=token, _external=True)}

If you did not make this request then simply ignore this email and no changes will be made.
'''
    mail.send(msg)

# Global variable to track processing status
processing_status = {
    'current_file': None,
    'current_file_index': 0,
    'total_files': 0,
    'started_at': None,
    'is_processing': False,
    'current_page': 0,
    'total_pages': 0,
    'last_activity': None
}

# Global variable to store processing results for recovery after server restart
processing_results = {
    'last_process_id': None,
    'results': None,
    'is_complete': False,
    'timestamp': None,
    'cancel_requested': False
}

# Global variable to track active processing threads
active_processing_threads = {}

def allowed_file(filename):
    """Check if a file has an allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def optimize_large_pdf(input_path, output_path, size_threshold_mb=100):
    """Optimize large PDF files to improve OCR processing speed"""
    file_size_mb = os.path.getsize(input_path) / (1024 * 1024)

    # Only optimize if file is larger than threshold
    if file_size_mb > size_threshold_mb:
        logger.info(f"File size {file_size_mb:.2f}MB exceeds {size_threshold_mb}MB threshold. Optimizing before OCR.")

        # Create a temp file for the optimized PDF
        temp_optimized = tempfile.mktemp(suffix='.pdf')

        try:
            # Use ghostscript to downsample images and optimize the PDF
            cmd = [
                'gs', '-sDEVICE=pdfwrite', '-dCompatibilityLevel=1.4',
                '-dPDFSETTINGS=/ebook',  # Lower quality for faster processing
                '-dNOPAUSE', '-dQUIET', '-dBATCH',
                f'-sOutputFile={temp_optimized}',
                input_path
            ]

            logger.info(f"Running optimization command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                # Check if optimization actually helped
                new_size_mb = os.path.getsize(temp_optimized) / (1024 * 1024)
                reduction = ((file_size_mb - new_size_mb) / file_size_mb) * 100

                logger.info(f"Optimization complete. Original: {file_size_mb:.2f}MB, New: {new_size_mb:.2f}MB (Reduced by {reduction:.1f}%)")

                if reduction > 10:  # Only use optimized version if it's significantly smaller
                    shutil.move(temp_optimized, output_path)
                    return output_path, True
                else:
                    logger.info("Optimization didn't significantly reduce file size. Using original.")
                    shutil.copy2(input_path, output_path)
                    os.remove(temp_optimized)
                    return output_path, False
            else:
                logger.warning(f"Optimization failed: {result.stderr}")
                shutil.copy2(input_path, output_path)
                return output_path, False
        except Exception as e:
            logger.error(f"Error during PDF optimization: {str(e)}")
            if os.path.exists(temp_optimized):
                os.remove(temp_optimized)
            shutil.copy2(input_path, output_path)
            return output_path, False
    else:
        # File is small enough, just copy it
        shutil.copy2(input_path, output_path)
        return output_path, False

def get_file_hash(file_path):
    """Generate a hash for a file to use as a cache key"""
    hash_md5 = hashlib.md5()

    # Also use file size and modification time in hash to detect changes
    file_stat = os.stat(file_path)
    size_mod = f"{file_stat.st_size}_{file_stat.st_mtime}"
    hash_md5.update(size_mod.encode())

    # For files smaller than 100MB, include file content in hash
    if file_stat.st_size < 100 * 1024 * 1024:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)

    return hash_md5.hexdigest()

def check_cache(file_path, filename):
    """Check if file has been processed before and is in cache"""
    try:
        file_hash = get_file_hash(file_path)
        cache_key = f"{file_hash}_{filename}"
        cache_path = os.path.join(app.config['CACHE_FOLDER'], cache_key)

        if os.path.exists(cache_path):
            logger.info(f"Cache hit for {filename}")
            return cache_path, True

        logger.info(f"Cache miss for {filename}")
        return cache_path, False
    except Exception as e:
        logger.error(f"Error checking cache: {str(e)}")
        return None, False

# Function to process a single PDF file (to be used with multiprocessing)
def process_single_pdf(file_info):
    """Process a single PDF file with OCR and return the result"""
    input_path, output_path, filename, timeout = file_info
    result = {
        'filename': filename,
        'success': False,
        'output_path': output_path,
        'error': None,
        'optimized': False,
        'from_cache': False
    }

    try:
        # First check if we have this file in cache
        cache_path, cache_hit = check_cache(input_path, filename)

        if cache_hit and cache_path:
            # File found in cache, just copy it to output
            shutil.copy2(cache_path, output_path)
            result['success'] = True
            result['from_cache'] = True
            return result

        # First, try to optimize large PDFs
        temp_dir = tempfile.mkdtemp()
        optimized_path = os.path.join(temp_dir, filename)

        input_path, was_optimized = optimize_large_pdf(input_path, optimized_path)
        result['optimized'] = was_optimized

        # Try to OCR the file with optimized settings for speed
        ocrmypdf.ocr(
            input_path,
            output_path,
            deskew=True,
            skip_text=True,
            force_ocr=False,
            optimize=0,
            clean=False,
            fast_web_view=0,
            max_image_mpixels=0,
            progress_bar=False,
            jobs=1,  # Use 1 core per file since we're parallelizing at the file level
            skip_big=100,  # Skip very large images (helps with speed)
            pdfa_image_compression="jpeg",  # Use faster compression
            jpeg_quality=70,  # Lower quality for faster processing
            png_quality=70
        )
        result['success'] = True

        # If successful, save to cache for future use
        if cache_path and result['success']:
            try:
                shutil.copy2(output_path, cache_path)
                logger.info(f"Saved {filename} to cache")
            except Exception as cache_error:
                logger.error(f"Error saving to cache: {str(cache_error)}")
    except ocrmypdf.exceptions.PriorOcrFoundError:
        # File already has OCR
        shutil.copy2(input_path, output_path)
        result['success'] = True
        result['error'] = "File already has OCR"

        # Save to cache
        if cache_path:
            try:
                shutil.copy2(output_path, cache_path)
                logger.info(f"Saved {filename} to cache (already OCR'd)")
            except Exception as cache_error:
                logger.error(f"Error saving to cache: {str(cache_error)}")
    except Exception as e:
        # Handle any errors
        result['error'] = str(e)
        # If any error occurs, copy the original file
        try:
            shutil.copy2(input_path, output_path)
            result['success'] = True  # Mark as success since we're providing the original file
        except Exception as copy_error:
            result['error'] += f" (Copy failed: {str(copy_error)})"
    finally:
        # Clean up temp directory
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except:
            pass

    return result

def process_pdfs(input_dir, file_path_mapping=None, timeout=1800):  # Default timeout of 30 minutes
    output_dir = tempfile.mkdtemp()
    processed_files = []
    errors = []
    results = []  # Store all processing results to return

    # Log the start of processing
    logger.info(f"Starting OCR processing for files in {input_dir}")
    pdf_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.pdf')]
    file_count = len(pdf_files)
    processing_status['total_files'] = file_count
    logger.info(f"Found {file_count} PDF files to process")

    # Check if processing was canceled
    if processing_results.get('cancel_requested', False):
        logger.info("Processing canceled before starting OCR")
        return [], output_dir, ["Processing canceled by user"], [], {'cpu_cores': 0}, file_path_mapping

    # Determine the optimal number of processes to use
    max_workers = min(multiprocessing.cpu_count(), file_count, 4)  # Use up to 4 cores or number of files
    logger.info(f"Using {max_workers} CPU cores for parallel processing")

    # Store processing stats
    processing_stats = {
        'cpu_cores': max_workers
    }

    # Prepare the file information for parallel processing
    process_args = []
    for idx, filename in enumerate(pdf_files):
        # Check if processing was canceled
        if processing_results.get('cancel_requested', False):
            logger.info("Processing canceled while preparing files")
            return [], output_dir, ["Processing canceled by user"], [], processing_stats, file_path_mapping

        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, filename)

        file_size = os.path.getsize(input_path) / (1024 * 1024)  # Size in MB
        logger.info(f"Preparing file {idx+1}/{file_count}: {filename} ({file_size:.2f} MB)")

        process_args.append((input_path, output_path, filename, timeout))

    # Process files in parallel using ProcessPoolExecutor
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {executor.submit(process_single_pdf, arg): arg for arg in process_args}

        # Update processing status as each file completes
        for idx, future in enumerate(as_completed(future_to_file)):
            # Check if processing was canceled
            if processing_results.get('cancel_requested', False):
                logger.info("Processing canceled during OCR processing")
                executor.shutdown(wait=False)  # Try to shut down the executor without waiting
                return processed_files, output_dir, ["Processing canceled by user"], results, processing_stats, file_path_mapping

            arg = future_to_file[future]
            filename = arg[2]

            # Update processing status
            processing_status['current_file'] = filename
            processing_status['current_file_index'] = idx + 1
            processing_status['is_processing'] = True
            processing_status['last_activity'] = time.time()

            try:
                result = future.result()
                results.append(result)

                if result['success']:
                    processed_files.append(result['output_path'])
                    logger.info(f"Successfully processed file {idx+1}/{file_count}: {filename}")
                else:
                    logger.error(f"Error processing {filename}: {result['error']}")
                    errors.append(f"{filename}: {result['error']}")
            except Exception as e:
                logger.error(f"Exception during parallel processing of {filename}: {str(e)}")
                errors.append(f"{filename}: {str(e)}")

    # Reset processing status
    processing_status['is_processing'] = False

    logger.info(f"Completed processing all files. Successful: {len(processed_files)}, Errors: {len(errors)}")
    return processed_files, output_dir, errors, results, processing_stats, file_path_mapping

def count_pdf_pages(pdf_path):
    """Count the number of pages in a PDF file."""
    try:
        logger.info(f"Counting pages in {os.path.basename(pdf_path)}")
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            page_count = len(pdf_reader.pages)
            logger.info(f"File {os.path.basename(pdf_path)} has {page_count} pages")
            return page_count
    except Exception as e:
        logger.error(f"Error counting pages in {pdf_path}: {str(e)}")
        return 0

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', title='Dashboard')

@app.route('/process', methods=['POST'])
@login_required
def process_files():
    if 'files[]' not in request.files:
        logger.warning("No files provided in request")
        return jsonify({'error': 'No files provided'}), 400

    files = request.files.getlist('files[]')
    if not files:
        logger.warning("No files selected for processing")
        return jsonify({'error': 'No files selected'}), 400

    try:
        # Generate a unique process ID
        process_id = hashlib.md5(str(time.time()).encode()).hexdigest()
        processing_results['last_process_id'] = process_id
        processing_results['is_complete'] = False
        processing_results['cancel_requested'] = False
        processing_results['timestamp'] = time.time()

        # Create temporary directory for input files
        input_dir = tempfile.mkdtemp()
        file_info = []
        total_pages = 0

        logger.info(f"Starting to process {len(files)} files (Process ID: {process_id})")

        # Validate files
        valid_files = []
        for file in files:
            if file.filename and allowed_file(file.filename):
                valid_files.append(file)
            else:
                logger.warning(f"Skipping file with invalid extension: {file.filename}")

        if not valid_files:
            logger.warning("No valid PDF files provided")
            shutil.rmtree(input_dir, ignore_errors=True)
            return jsonify({'error': 'No valid PDF files provided. Only PDF files are accepted.'}), 400

        # Store original file paths for preserving folder structure
        file_path_mapping = {}
        
        for idx, file in enumerate(valid_files):
            # Preserve original folder structure from webkitRelativePath
            original_path = file.filename
            filename = secure_filename(os.path.basename(file.filename))
            
            # Check if file includes folder structure
            if '/' in original_path:
                # Preserve folder structure
                folder_parts = original_path.split('/')
                # Secure all folder parts
                secure_parts = [secure_filename(part) for part in folder_parts[:-1]]
                secure_parts.append(filename)
                
                folder_path = os.path.join(input_dir, *secure_parts[:-1])
                os.makedirs(folder_path, exist_ok=True)
                file_path = os.path.join(input_dir, *secure_parts)
                relative_path = os.path.join(*secure_parts)
            else:
                file_path = os.path.join(input_dir, filename)
                relative_path = filename
            
            file.save(file_path)
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # Size in MB
            logger.info(f"Saved file {idx+1}/{len(valid_files)}: {relative_path} ({file_size:.2f} MB)")

            # Store mapping for ZIP creation
            file_path_mapping[file_path] = relative_path
            
            # Count pages in the PDF
            page_count = count_pdf_pages(file_path)
            total_pages += page_count
            file_info.append({
                'name': filename,
                'path': relative_path,
                'page_count': page_count,
                'size_mb': round(file_size, 2)
            })

        logger.info(f"All files uploaded. Starting OCR processing for {len(valid_files)} files with {total_pages} total pages")

        # Start processing in a background thread to prevent blocking
        def process_in_background():
            output_dir = None
            try:
                # Check if processing was canceled
                if processing_results['cancel_requested']:
                    logger.info(f"Processing canceled for process ID: {process_id}")
                    processing_results['results'] = {
                        'error': 'Processing was canceled by the user',
                        'success': False,
                        'process_id': process_id
                    }
                    processing_results['is_complete'] = True
                    return

                # Process PDFs - Note the additional return values
                processed_files, output_dir, errors, results, processing_stats, original_mapping = process_pdfs(input_dir, file_path_mapping)

                # Check if processing was canceled during PDF processing
                if processing_results['cancel_requested']:
                    logger.info(f"Processing canceled for process ID: {process_id}")
                    processing_results['results'] = {
                        'error': 'Processing was canceled by the user',
                        'success': False,
                        'process_id': process_id
                    }
                    processing_results['is_complete'] = True
                    return

                if not processed_files:
                    logger.error("No files were processed successfully")
                    processing_results['results'] = {
                        'error': 'No files were processed successfully',
                        'success': False,
                        'process_id': process_id
                    }
                    processing_results['is_complete'] = True
                    return

                # Create zip file
                zip_path = os.path.join(app.config['UPLOAD_FOLDER'], f'processed_files_{process_id}.zip')
                logger.info(f"Creating ZIP archive at {zip_path}")
                with zipfile.ZipFile(zip_path, 'w') as zipf:
                    for file_path in processed_files:
                        # Find the corresponding input file to get original structure
                        input_file_path = None
                        for input_path in original_mapping:
                            if os.path.basename(input_path) == os.path.basename(file_path):
                                input_file_path = input_path
                                break
                        
                        if input_file_path and input_file_path in original_mapping:
                            # Use original folder structure
                            arcname = original_mapping[input_file_path]
                        else:
                            # Fallback to just filename
                            arcname = os.path.basename(file_path)
                        
                        zipf.write(file_path, arcname)
                        logger.info(f"Added to zip: {arcname}")

                zip_size = os.path.getsize(zip_path) / (1024 * 1024)  # Size in MB
                logger.info(f"ZIP archive created successfully. Size: {zip_size:.2f} MB")

                # Calculate optimization statistics
                optimized_count = sum(1 for r in results if r.get('optimized', False))
                from_cache_count = sum(1 for r in results if r.get('from_cache', False))

                # Update file info with processing details
                for result in results:
                    for fi in file_info:
                        if fi['name'] == result.get('filename'):
                            fi['optimized'] = result.get('optimized', False)
                            fi['from_cache'] = result.get('from_cache', False)
                            break

                # Store the results for retrieval
                processing_results['results'] = {
                    'message': 'Processing complete',
                    'download_url': f'/download/{process_id}',
                    'errors': errors if errors else None,
                    'file_info': file_info,
                    'total_pages': total_pages,
                    'stats': {
                        'optimized_files': optimized_count,
                        'from_cache': from_cache_count,
                        'total_files': len(file_info),
                        'cpu_cores': processing_stats['cpu_cores']
                    },
                    'process_id': process_id,
                    'success': True
                }
                processing_results['is_complete'] = True
                logger.info(f"Processing completed successfully for process ID: {process_id}")
            except Exception as e:
                logger.error(f"Unexpected error in background processing: {str(e)}")
                processing_results['results'] = {
                    'error': f'An unexpected error occurred: {str(e)}',
                    'success': False,
                    'process_id': process_id
                }
                processing_results['is_complete'] = True
            finally:
                # Cleanup temporary directories
                try:
                    logger.info("Cleaning up temporary directories")
                    shutil.rmtree(input_dir, ignore_errors=True)
                    if output_dir:
                        shutil.rmtree(output_dir, ignore_errors=True)
                except Exception as e:
                    logger.error(f"Error during cleanup: {str(e)}")

                # Remove thread reference
                if process_id in active_processing_threads:
                    del active_processing_threads[process_id]

        # Start the background processing thread
        processing_thread = threading.Thread(target=process_in_background)
        processing_thread.daemon = True
        processing_thread.start()

        # Store thread reference for potential cancellation
        active_processing_threads[process_id] = processing_thread

        return jsonify({
            'message': 'Processing started',
            'process_id': process_id
        })

    except Exception as e:
        logger.error(f"Unexpected error starting process: {str(e)}")
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

@app.route('/process-status/<process_id>', methods=['GET'])
@login_required
def process_status(process_id):
    """Get the status of a processing job"""
    if not processing_results['last_process_id']:
        return jsonify({'error': 'No processing job found'}), 404

    if processing_results['last_process_id'] != process_id:
        return jsonify({'error': 'Process ID not found'}), 404

    if processing_results['is_complete']:
        return jsonify(processing_results['results'])
    else:
        return jsonify({
            'message': 'Processing in progress',
            'process_id': process_id,
            'elapsed_seconds': time.time() - processing_results['timestamp'],
            'cancel_requested': processing_results['cancel_requested']
        })

@app.route('/cancel-process/<process_id>', methods=['POST'])
@login_required
def cancel_process(process_id):
    """Cancel a running processing job"""
    if not processing_results['last_process_id']:
        return jsonify({'error': 'No processing job found'}), 404

    if processing_results['last_process_id'] != process_id:
        return jsonify({'error': 'Process ID not found'}), 404

    if processing_results['is_complete']:
        return jsonify({'error': 'Process already completed'}), 400

    # Mark the process as canceled
    processing_results['cancel_requested'] = True
    logger.info(f"Cancel requested for process ID: {process_id}")

    # If we have a thread reference, try to terminate it
    if process_id in active_processing_threads:
        thread = active_processing_threads[process_id]
        if thread and thread.is_alive():
            # We can't forcefully terminate a thread in Python,
            # but we can set a flag that the thread should check
            logger.info(f"Signaling thread to terminate for process ID: {process_id}")

    return jsonify({
        'success': True,
        'message': 'Cancel request received. Processing will stop as soon as possible.'
    })

@app.route('/download/<process_id>')
@login_required
def download(process_id):
    """Download the processed files for a specific process ID"""
    zip_path = os.path.join(app.config['UPLOAD_FOLDER'], f'processed_files_{process_id}.zip')
    if not os.path.exists(zip_path):
        logger.warning(f"Download requested but no processed files found for process ID: {process_id}")
        return jsonify({'error': 'No processed files found'}), 404

    logger.info(f"Download initiated for processed files (Process ID: {process_id})")
    return send_file(zip_path, as_attachment=True, download_name='processed_files.zip')

# Deprecated but maintained for backward compatibility
@app.route('/download')
@login_required
def download_legacy():
    """Legacy download endpoint for backward compatibility"""
    if not processing_results['last_process_id']:
        return jsonify({'error': 'No processed files found'}), 404

    return download(processing_results['last_process_id'])

@app.route('/logs')
def get_logs():
    """Return the latest logs as JSON"""
    return jsonify(list(log_buffer))

@app.route('/status')
def get_status():
    """Return the current processing status"""
    status_info = dict(processing_status)

    # Add time elapsed if processing
    if status_info['started_at'] and status_info['is_processing']:
        status_info['elapsed_seconds'] = time.time() - status_info['started_at']

        # Check for possible hang (no activity for more than 2 minutes)
        if (time.time() - status_info['last_activity']) > 120:
            status_info['possible_hang'] = True
        else:
            status_info['possible_hang'] = False

    return jsonify(status_info)

@app.route('/clear-cache')
def clear_cache():
    """Clear the OCR cache to free up disk space"""
    try:
        cache_dir = app.config['CACHE_FOLDER']
        if os.path.exists(cache_dir):
            file_count = len(os.listdir(cache_dir))

            # Remove files from the cache directory
            for filename in os.listdir(cache_dir):
                file_path = os.path.join(cache_dir, filename)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                except Exception as e:
                    logger.error(f"Error deleting cache file {filename}: {str(e)}")

            logger.info(f"Cache cleared. Removed {file_count} files.")
            return jsonify({"success": True, "message": f"Cache cleared. Removed {file_count} files."})
        else:
            return jsonify({"success": False, "message": "Cache directory not found"})
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        return jsonify({"success": False, "message": f"Error clearing cache: {str(e)}"})

def cleanup_old_cache_files(max_age_days=7, max_size_mb=5000):
    """Remove old files from cache to prevent excessive disk usage"""
    try:
        cache_dir = app.config['CACHE_FOLDER']
        if not os.path.exists(cache_dir):
            return

        # Calculate cutoff time for file age
        cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)

        # Calculate current cache size
        total_size = 0
        file_info = []

        for filename in os.listdir(cache_dir):
            file_path = os.path.join(cache_dir, filename)
            if os.path.isfile(file_path):
                file_stat = os.stat(file_path)
                file_size = file_stat.st_size / (1024 * 1024)  # Size in MB
                modify_time = file_stat.st_mtime

                file_info.append({
                    'path': file_path,
                    'size': file_size,
                    'modified': modify_time
                })

                total_size += file_size

        logger.info(f"Current cache size: {total_size:.2f}MB, {len(file_info)} files")

        # Remove old files first
        removed_count = 0
        removed_size = 0

        # First pass: remove files older than cutoff time
        for file in file_info[:]:
            if file['modified'] < cutoff_time:
                try:
                    os.remove(file['path'])
                    removed_size += file['size']
                    removed_count += 1
                    file_info.remove(file)
                except Exception as e:
                    logger.error(f"Error removing old cache file: {str(e)}")

        # Second pass: If still over size limit, remove largest files until under limit
        if (total_size - removed_size) > max_size_mb:
            # Sort by size, largest first
            file_info.sort(key=lambda x: x['size'], reverse=True)

            for file in file_info:
                if (total_size - removed_size) <= max_size_mb:
                    break

                try:
                    os.remove(file['path'])
                    removed_size += file['size']
                    removed_count += 1
                except Exception as e:
                    logger.error(f"Error removing large cache file: {str(e)}")

        if removed_count > 0:
            logger.info(f"Cache cleanup: Removed {removed_count} files ({removed_size:.2f}MB)")

    except Exception as e:
        logger.error(f"Error during cache cleanup: {str(e)}")

# Run cache cleanup on startup
cleanup_old_cache_files()

@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(e):
    logger.error(f"File too large error: {str(e)}")
    return jsonify({
        'error': 'File size exceeds the limit (1.5GB combined). Please upload smaller files or fewer files at once.'
    }), 413

# Authentication routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password_hash=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('login'))
    return render_template('reset_request.html', title='Reset Password', form=form)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    user = verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password_hash = hashed_password
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', title='Reset Password', form=form)

# Document Review Routes for Expert Witness Reports
@app.route('/document_reviews')
@login_required
def document_reviews():
    """Display all document review sessions for the current user"""
    sessions = DocumentReviewSession.query.filter_by(user_id=current_user.id).order_by(DocumentReviewSession.created_at.desc()).all()
    return render_template('document_reviews.html', title='Document Reviews', sessions=sessions)

@app.route('/create_review_session', methods=['GET', 'POST'])
@login_required
def create_review_session():
    """Create a new document review session"""
    form = DocumentReviewSessionForm()
    if form.validate_on_submit():
        session = DocumentReviewSession(
            user_id=current_user.id,
            case_name=form.case_name.data,
            case_number=form.case_number.data,
            expert_name=form.expert_name.data,
            expert_title=form.expert_title.data
        )
        db.session.add(session)
        db.session.commit()
        flash(f'Document review session created for case: {form.case_name.data}', 'success')
        return redirect(url_for('review_session_details', session_id=session.id))
    return render_template('create_review_session.html', title='Create Review Session', form=form)

@app.route('/review_session/<int:session_id>')
@login_required
def review_session_details(session_id):
    """Display details of a specific document review session"""
    session = DocumentReviewSession.query.filter_by(id=session_id, user_id=current_user.id).first_or_404()
    documents = ReviewedDocument.query.filter_by(session_id=session_id).order_by(ReviewedDocument.original_filename).all()
    
    # Calculate statistics
    total_documents = len(documents)
    total_pages = sum(doc.page_count or 0 for doc in documents)
    ocr_processed = sum(1 for doc in documents if doc.ocr_processed)
    
    stats = {
        'total_documents': total_documents,
        'total_pages': total_pages,
        'ocr_processed': ocr_processed,
        'avg_relevance': round(sum(doc.relevance_rating or 0 for doc in documents) / max(total_documents, 1), 1)
    }
    
    return render_template('review_session_details.html', title=f'Review: {session.case_name}', 
                         session=session, documents=documents, stats=stats)

@app.route('/edit_document/<int:document_id>', methods=['GET', 'POST'])
@login_required
def edit_document(document_id):
    """Edit document metadata and review information"""
    document = ReviewedDocument.query.get_or_404(document_id)
    
    # Verify user owns this document's session
    session = DocumentReviewSession.query.filter_by(id=document.session_id, user_id=current_user.id).first_or_404()
    
    form = DocumentEditForm(obj=document)
    if form.validate_on_submit():
        form.populate_obj(document)
        # Parse document date if provided
        if form.document_date.data:
            try:
                from datetime import datetime
                document.document_date = datetime.strptime(form.document_date.data, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid date format. Please use YYYY-MM-DD format.', 'warning')
                return render_template('edit_document.html', title='Edit Document', form=form, document=document)
        
        db.session.commit()
        flash(f'Document "{document.original_filename}" updated successfully', 'success')
        return redirect(url_for('review_session_details', session_id=document.session_id))
    
    # Pre-populate date field
    if document.document_date:
        form.document_date.data = document.document_date.strftime('%Y-%m-%d')
    
    return render_template('edit_document.html', title='Edit Document', form=form, document=document)

@app.route('/export_document_list/<int:session_id>')
@login_required
def export_document_list(session_id):
    """Export document list for expert witness reports"""
    session = DocumentReviewSession.query.filter_by(id=session_id, user_id=current_user.id).first_or_404()
    documents = ReviewedDocument.query.filter_by(session_id=session_id).order_by(ReviewedDocument.original_filename).all()
    
    # Group documents by type
    grouped_docs = {}
    for doc in documents:
        doc_type = doc.document_type or 'Other Documents'
        if doc_type not in grouped_docs:
            grouped_docs[doc_type] = []
        grouped_docs[doc_type].append(doc)
    
    return render_template('export_document_list.html', title='Documents Reviewed Export', 
                         session=session, grouped_docs=grouped_docs, documents=documents)

@app.route('/link_processing_to_session', methods=['POST'])
@login_required
def link_processing_to_session():
    """Link recently processed files to a document review session"""
    data = request.get_json()
    session_id = data.get('session_id')
    file_info = data.get('file_info', [])
    
    if not session_id or not file_info:
        return jsonify({'error': 'Missing session_id or file_info'}), 400
    
    # Verify session belongs to user
    session = DocumentReviewSession.query.filter_by(id=session_id, user_id=current_user.id).first()
    if not session:
        return jsonify({'error': 'Session not found'}), 404
    
    try:
        documents_created = 0
        for file_data in file_info:
            # Check if document already exists in this session
            existing = ReviewedDocument.query.filter_by(
                session_id=session_id,
                original_filename=file_data.get('name')
            ).first()
            
            if not existing:
                # Create new document record
                document = ReviewedDocument(
                    session_id=session_id,
                    original_filename=file_data.get('name'),
                    file_path=file_data.get('path', file_data.get('name')),
                    page_count=file_data.get('page_count'),
                    file_size_mb=file_data.get('size_mb'),
                    ocr_processed=True,
                    has_text=True
                )
                db.session.add(document)
                documents_created += 1
        
        db.session.commit()
        return jsonify({'success': True, 'message': f'{documents_created} documents added to review session'})
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error linking documents to session: {str(e)}")
        return jsonify({'error': 'Failed to link documents'}), 500

@app.route('/get_user_sessions')
@login_required
def get_user_sessions():
    """Get document review sessions for the current user"""
    sessions = DocumentReviewSession.query.filter_by(user_id=current_user.id).order_by(DocumentReviewSession.created_at.desc()).all()
    session_data = [
        {
            'id': session.id,
            'case_name': session.case_name,
            'case_number': session.case_number,
            'expert_name': session.expert_name
        }
        for session in sessions
    ]
    return jsonify({'sessions': session_data})

# Initialize database
def create_tables():
    with app.app_context():
        db.create_all()

# Call create_tables when the module is imported
create_tables()

if __name__ == '__main__':
    # Check if running in Docker/production
    if os.environ.get('FLASK_ENV') == 'production':
        # In production, the application is run by Gunicorn
        app.config['SERVER_NAME'] = None
    else:
        # In development, find an available port and run the Flask development server
        import socket
        from contextlib import closing

        def find_free_port():
            with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
                s.bind(('', 0))
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                return s.getsockname()[1]

        port = int(os.environ.get('PORT', find_free_port()))
        print(f"Starting server on port {port}")
        app.run(host='0.0.0.0', debug=True, port=port, use_reloader=app.config['USE_RELOADER'])