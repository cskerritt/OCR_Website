# PDF OCR Processor

A professional-grade web application for batch PDF OCR processing using OCRmyPDF. This application provides a user-friendly interface for converting image-based PDFs into searchable, text-based documents.

## 🌐 Live Demo

**[View Demo on GitHub Pages](https://cskerritt.github.io/OCR_Website/)**

*Note: The GitHub Pages version is a demonstration of the interface. For full OCR functionality, deploy the application on a server using the instructions below.*

## ✨ Features

- **Batch Processing**: Process multiple PDF files simultaneously
- **Smart Optimization**: Automatically optimizes large PDFs for faster processing
- **Intelligent Caching**: Avoids reprocessing identical files
- **Real-time Progress**: Live progress updates and detailed logging
- **Error Handling**: Comprehensive error reporting and recovery
- **User Authentication**: Secure user accounts and session management
- **Parallel Processing**: Utilizes multiple CPU cores for optimal performance
- **Responsive Design**: Works on desktop and mobile devices
- **Dark Mode**: Toggle between light and dark themes
- **Modern Interface**: Drag-and-drop file upload with intuitive UI

## 🚀 Quick Start

### Option 1: Docker Deployment (Recommended)

```bash
git clone https://github.com/cskerritt/OCR_Website.git
cd OCR_Website
docker-compose up -d
```

### Option 2: Manual Installation

```bash
# Install dependencies (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y python3 python3-pip tesseract-ocr ghostscript

# Clone and setup
git clone https://github.com/cskerritt/OCR_Website.git
cd OCR_Website
pip3 install -r requirements.txt

# Run the application
python3 app.py
```

## Deployment to AWS Lightsail

### Prerequisites

1. AWS account with Lightsail access
2. Domain name (optional but recommended for production)
3. Basic knowledge of Linux, Docker, and AWS

### Setup AWS Lightsail

1. Create a new Lightsail instance:
   - Go to the AWS Lightsail console: https://lightsail.aws.amazon.com
   - Click "Create instance"
   - Select a Linux/Unix platform (Ubuntu 22.04 LTS recommended)
   - Choose an instance plan (at least 2 GB RAM recommended)
   - Name your instance and click "Create instance"

2. Configure networking:
   - Go to the "Networking" tab of your instance
   - Create a static IP and attach it to your instance
   - Add custom firewall rules to open ports 80 and 443

3. Set up your domain (optional):
   - Configure your domain's DNS to point to the static IP of your Lightsail instance
   - Wait for DNS propagation (can take up to 24 hours)

### Deploy the Application

1. Connect to your Lightsail instance via SSH:
   ```
   ssh ubuntu@your-instance-ip
   ```

2. Clone this repository:
   ```
   git clone https://github.com/cskerritt/OCR_Website.git
   cd OCR_Website
   ```

3. Run the deployment script:
   ```
   ./lightsail-deploy.sh
   ```

4. Follow the prompts to enter your domain name and email for SSL certificates

5. The script will:
   - Install Docker and Docker Compose
   - Configure Caddy with your domain
   - Build and start the Docker containers

### Monitoring and Maintenance

- Check container status:
  ```
  docker-compose ps
  ```

- View logs:
  ```
  docker-compose logs
  ```

- Restart the application:
  ```
  docker-compose restart
  ```

- Update the application:
  ```
  git pull
  docker-compose up -d --build
  ```

## Local Development

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Run the application:
   ```
   python app.py
   ```

3. Access the application at the URL shown in the terminal (the app will automatically find an available port)

## Prerequisites

- Python 3.7 or higher
- OCRmyPDF installed on your system
- Ghostscript (used for PDF optimization)
- Required Python packages (listed in requirements.txt)

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd <repository-directory>
```

2. Install the required Python packages:
```bash
pip install -r requirements.txt
```

3. Make sure OCRmyPDF and Ghostscript are installed on your system:
```bash
# For macOS
brew install ocrmypdf ghostscript

# For Ubuntu/Debian
sudo apt-get install ocrmypdf ghostscript

# For Windows
pip install ocrmypdf
# Download and install Ghostscript from https://www.ghostscript.com/download.html
```

## Usage

1. Start the Flask application:
```bash
python app.py
```

2. Open your web browser and navigate to `http://localhost:5000`

3. Drag and drop PDF files or click to select files

4. Click the "Process Files" button to start OCR processing

5. Once processing is complete, click the "Download Processed Files" button to get your OCR'ed PDFs

## Notes

- The application has a file size limit of 1.5GB combined for all files
- Only PDF files are accepted
- Processing time depends on the size and number of files
- Temporary files are automatically cleaned up after processing
- Large PDF files are automatically optimized before OCR processing
- Processed files are cached to improve performance for repeated uploads

## Version History

- v1.1.0 - Added dark mode, improved mobile responsiveness, added cancel processing functionality, improved error handling
- v1.0.0 - Initial release

## License

MIT License