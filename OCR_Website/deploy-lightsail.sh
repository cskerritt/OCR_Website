#!/bin/bash

# OCR Website - Amazon Lightsail Deployment Script
# This script automates the deployment process for Amazon Lightsail

set -e

echo "🚀 Starting OCR Website deployment on Amazon Lightsail..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    print_error "This script should not be run as root"
    exit 1
fi

# Update system packages
print_status "Updating system packages..."
sudo apt-get update -y

# Install required packages
print_status "Installing required packages..."
sudo apt-get install -y git curl software-properties-common

# Install Docker if not already installed
if ! command -v docker &> /dev/null; then
    print_status "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    print_warning "Docker installed. You may need to log out and log back in for group changes to take effect."
else
    print_status "Docker is already installed"
fi

# Install Docker Compose if not already installed
if ! command -v docker-compose &> /dev/null; then
    print_status "Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.25.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
else
    print_status "Docker Compose is already installed"
fi

# Create application directory
APP_DIR="/home/$USER/OCR_Website"
if [ ! -d "$APP_DIR" ]; then
    print_status "Cloning repository..."
    git clone https://github.com/yourusername/OCR_Website.git "$APP_DIR"
else
    print_status "Repository already exists, pulling latest changes..."
    cd "$APP_DIR"
    git pull
fi

cd "$APP_DIR"

# Create required directories
print_status "Creating required directories..."
mkdir -p uploads ocr_cache instance logs/caddy

# Set up environment variables
if [ ! -f ".env" ]; then
    print_status "Setting up environment variables..."
    cp .env.example .env
    
    # Generate secure secret key
    SECRET_KEY=$(openssl rand -hex 32)
    sed -i "s/your-secret-key-here/$SECRET_KEY/" .env
    
    print_warning "Please edit .env file to configure your email settings for password reset functionality"
    print_warning "You need to set: MAIL_USERNAME, MAIL_PASSWORD, and MAIL_DEFAULT_SENDER"
else
    print_status "Environment file already exists"
fi

# Configure domain (if provided)
if [ -n "$1" ]; then
    DOMAIN=$1
    print_status "Configuring domain: $DOMAIN"
    
    # Update Caddyfile with the provided domain
    if [ -f "Caddyfile" ]; then
        sed -i "s/yourdomain.com/$DOMAIN/g" Caddyfile
        print_status "Updated Caddyfile with domain: $DOMAIN"
    fi
else
    print_warning "No domain provided. The application will be accessible via IP address only."
    print_warning "To configure a domain later, edit the Caddyfile and restart the containers."
fi

# Build and start the application
print_status "Building and starting the application..."
docker-compose down || true
docker-compose up -d --build

# Wait for the application to start
print_status "Waiting for application to start..."
sleep 30

# Initialize the database
print_status "Initializing database..."
docker-compose exec -T flask python -c "
from app import app, db
with app.app_context():
    db.create_all()
    print('Database tables created successfully!')
" || print_warning "Database initialization failed. This might be normal on first run."

# Check if containers are running
print_status "Checking container status..."
docker-compose ps

# Set up firewall
if command -v ufw &> /dev/null; then
    print_status "Configuring firewall..."
    sudo ufw allow 22/tcp
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    sudo ufw --force enable
else
    print_warning "UFW firewall not available. Please configure firewall manually."
fi

# Create update script
print_status "Creating update script..."
cat > update.sh << 'EOF'
#!/bin/bash
cd /home/ubuntu/OCR_Website
git pull
docker-compose up -d --build
EOF
chmod +x update.sh

# Set up automatic updates (optional)
read -p "Set up automatic weekly updates? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Setting up automatic updates..."
    (crontab -l 2>/dev/null; echo "0 0 * * 0 $APP_DIR/update.sh >> $APP_DIR/update.log 2>&1") | crontab -
    print_status "Automatic updates configured for every Sunday at midnight"
fi

# Final status check
print_status "Final status check..."
if docker-compose ps | grep -q "Up"; then
    print_status "✅ Deployment completed successfully!"
    echo
    echo "🌐 Your OCR Website is now running!"
    echo
    if [ -n "$DOMAIN" ]; then
        echo "   Domain: https://$DOMAIN"
        echo "   Note: SSL certificate will be automatically obtained by Caddy"
    else
        EXTERNAL_IP=$(curl -s http://checkip.amazonaws.com || echo "Unable to determine external IP")
        echo "   IP Address: http://$EXTERNAL_IP"
        echo "   Note: Configure a domain for HTTPS support"
    fi
    echo
    echo "📝 Next steps:"
    echo "   1. Edit .env file to configure email settings"
    echo "   2. Test the application by uploading a PDF"
    echo "   3. Create your first user account"
    echo
    echo "🔧 Useful commands:"
    echo "   View logs: docker-compose logs"
    echo "   Restart: docker-compose restart"
    echo "   Update: ./update.sh"
    echo "   Stop: docker-compose down"
else
    print_error "❌ Deployment failed. Check the logs with: docker-compose logs"
    exit 1
fi