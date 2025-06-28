#!/bin/bash

# This script helps deploy the OCR application to AWS Lightsail

# Install Docker and Docker Compose if not already installed
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
fi

if ! command -v docker-compose &> /dev/null; then
    echo "Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.25.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# Create required directories
mkdir -p logs/caddy
mkdir -p uploads
mkdir -p ocr_cache

# Update domain in Caddyfile
read -p "Enter your domain name (e.g., yourdomain.com): " domain_name
read -p "Enter your email address for Let's Encrypt: " email_address

# Update Caddyfile with domain and email
sed -i "s/your-email@example.com/$email_address/g" Caddyfile
sed -i "s/yourdomain.com/$domain_name/g" Caddyfile

# Generate a secure secret key
echo "Generating a secure secret key..."
SECRET_KEY=$(openssl rand -hex 16)
echo "SECRET_KEY=$SECRET_KEY" > .env
echo "Generated SECRET_KEY: $SECRET_KEY"

# Set up basic security
echo "Setting up basic firewall rules..."
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

# Build and start the application
echo "Building and starting Docker containers..."
docker-compose up -d --build

# Create update script
cat > update.sh << 'EOF'
#!/bin/bash
cd $(dirname "$0")
git pull
docker-compose up -d --build
EOF
chmod +x update.sh

echo "Deployment completed!"
echo "Please make sure to:"
echo "1. Configure your domain's DNS to point to this server's IP"
echo "2. Open ports 80 and 443 in your AWS Lightsail firewall settings"
echo ""
echo "To update the application in the future, run: ./update.sh"
echo "To view logs, run: docker-compose logs"
echo "To monitor the application, run: docker-compose ps"