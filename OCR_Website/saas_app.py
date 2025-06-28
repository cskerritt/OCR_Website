import os
import zipfile
import tempfile
import shutil
import logging
from datetime import datetime
from flask import Flask, render_template, request, send_file, jsonify, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import ocrmypdf
from pathlib import Path
import stripe

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this in production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['STRIPE_PUBLIC_KEY'] = 'your-stripe-public-key'
app.config['STRIPE_SECRET_KEY'] = 'your-stripe-secret-key'

stripe.api_key = app.config['STRIPE_SECRET_KEY']

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# User model
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    credits = db.Column(db.Integer, default=0)
    subscription_status = db.Column(db.String(20), default='free')
    stripe_customer_id = db.Column(db.String(120), unique=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Usage history model
class UsageHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    files_processed = db.Column(db.Integer)
    credits_used = db.Column(db.Integer)

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

def process_pdfs(input_dir, user):
    output_dir = tempfile.mkdtemp()
    processed_files = []
    errors = []
    file_count = 0
    
    for filename in os.listdir(input_dir):
        if filename.lower().endswith('.pdf'):
            if user.credits <= 0 and user.subscription_status != 'premium':
                errors.append("Insufficient credits. Please purchase more credits or upgrade to premium.")
                break
                
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, filename)
            
            try:
                logger.info(f"Processing file: {filename}")
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
                    progress_bar=False
                )
                processed_files.append(output_path)
                file_count += 1
                logger.info(f"Successfully processed: {filename}")
                
                # Deduct credits if not premium
                if user.subscription_status != 'premium':
                    user.credits -= 1
                    db.session.commit()
                
            except ocrmypdf.exceptions.PriorOcrFoundError:
                logger.info(f"File already has OCR: {filename}")
                shutil.copy2(input_path, output_path)
                processed_files.append(output_path)
                file_count += 1
            except Exception as e:
                logger.error(f"Error processing {filename}: {str(e)}")
                errors.append(f"{filename}: {str(e)}")
                shutil.copy2(input_path, output_path)
                processed_files.append(output_path)
                file_count += 1
    
    # Record usage
    usage = UsageHistory(
        user_id=user.id,
        files_processed=file_count,
        credits_used=file_count if user.subscription_status != 'premium' else 0
    )
    db.session.add(usage)
    db.session.commit()
    
    return processed_files, output_dir, errors

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('saas_index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    usage_history = UsageHistory.query.filter_by(user_id=current_user.id).order_by(UsageHistory.timestamp.desc()).limit(10)
    return render_template('dashboard.html', user=current_user, usage_history=usage_history)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        
        flash('Invalid email or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('register'))
        
        user = User(email=email)
        user.set_password(password)
        user.credits = 10  # Free credits for new users
        
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        return redirect(url_for('dashboard'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/process', methods=['POST'])
@login_required
def process_files():
    if 'files[]' not in request.files:
        return jsonify({'error': 'No files provided'}), 400
    
    files = request.files.getlist('files[]')
    if not files:
        return jsonify({'error': 'No files selected'}), 400
    
    # Check credits
    if current_user.subscription_status != 'premium' and current_user.credits < len(files):
        return jsonify({'error': f'Insufficient credits. You need {len(files)} credits but have {current_user.credits}'}), 400
    
    try:
        input_dir = tempfile.mkdtemp()
        for file in files:
            if file.filename:
                filename = secure_filename(file.filename)
                file_path = os.path.join(input_dir, filename)
                file.save(file_path)
                logger.info(f"Saved uploaded file: {filename}")
        
        processed_files, output_dir, errors = process_pdfs(input_dir, current_user)
        
        if not processed_files:
            return jsonify({'error': 'No files were processed successfully'}), 400
        
        zip_path = os.path.join(app.config['UPLOAD_FOLDER'], f'processed_files_{current_user.id}.zip')
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for file_path in processed_files:
                arcname = os.path.basename(file_path)
                zipf.write(file_path, arcname)
                logger.info(f"Added to zip: {arcname}")
        
        return jsonify({
            'message': 'Processing complete',
            'download_url': url_for('download'),
            'credits_remaining': current_user.credits,
            'errors': errors if errors else None
        })
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500
    finally:
        try:
            shutil.rmtree(input_dir, ignore_errors=True)
            shutil.rmtree(output_dir, ignore_errors=True)
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

@app.route('/download')
@login_required
def download():
    zip_path = os.path.join(app.config['UPLOAD_FOLDER'], f'processed_files_{current_user.id}.zip')
    if not os.path.exists(zip_path):
        return jsonify({'error': 'No processed files found'}), 404
    return send_file(zip_path, as_attachment=True, download_name='processed_files.zip')

@app.route('/pricing')
def pricing():
    return render_template('pricing.html')

@app.route('/buy_credits', methods=['POST'])
@login_required
def buy_credits():
    try:
        credit_amount = int(request.form.get('amount', 100))
        
        # Create Stripe checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'unit_amount': credit_amount * 10,  # $0.10 per credit
                    'product_data': {
                        'name': 'OCR Credits',
                        'description': f'{credit_amount} OCR processing credits',
                    },
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=request.host_url + 'payment_success',
            cancel_url=request.host_url + 'dashboard',
            client_reference_id=str(current_user.id),
            metadata={'credits': credit_amount}
        )
        
        return jsonify({'id': checkout_session.id})
    except Exception as e:
        return jsonify({'error': str(e)}), 403

@app.route('/payment_success')
@login_required
def payment_success():
    # Note: In production, you should verify the payment with Stripe webhook
    flash('Payment successful! Credits have been added to your account.')
    return redirect(url_for('dashboard'))

@app.route('/subscribe', methods=['POST'])
@login_required
def subscribe():
    try:
        # Create Stripe checkout session for subscription
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': 'price_H5ggYwtDq8ej8h',  # Your Stripe price ID for subscription
                'quantity': 1,
            }],
            mode='subscription',
            success_url=request.host_url + 'subscription_success',
            cancel_url=request.host_url + 'dashboard',
            client_reference_id=str(current_user.id)
        )
        
        return jsonify({'id': checkout_session.id})
    except Exception as e:
        return jsonify({'error': str(e)}), 403

@app.route('/subscription_success')
@login_required
def subscription_success():
    current_user.subscription_status = 'premium'
    db.session.commit()
    flash('Successfully subscribed to premium plan!')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5001) 