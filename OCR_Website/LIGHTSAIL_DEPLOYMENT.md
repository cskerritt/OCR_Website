# Deploying OCR Website to Amazon Lightsail

This guide provides step-by-step instructions for deploying the OCR Website application to Amazon Lightsail.

## Prerequisites

1. An AWS account with access to Lightsail
2. A domain name (optional but recommended)
3. Basic knowledge of Linux, Docker, and AWS

## Step 1: Create a Lightsail Instance

1. Log in to the AWS Management Console and navigate to Lightsail: https://lightsail.aws.amazon.com

2. Click "Create instance"

3. Choose an instance location (AWS Region) that is closest to your users

4. Select the Linux/Unix platform and choose "OS Only" with "Ubuntu 22.04 LTS"

5. Choose an instance plan:
   - For small to medium usage: 2 GB RAM, 1 vCPU, 60 GB SSD ($10/month)
   - For heavier usage: 4 GB RAM, 2 vCPU, 80 GB SSD ($20/month)

6. Name your instance (e.g., "ocr-website-production")

7. Click "Create instance"

## Step 2: Configure Networking

1. Once your instance is running, go to the "Networking" tab

2. Create a static IP and attach it to your instance:
   - Click "Create static IP"
   - Select the region and your instance
   - Name your static IP (e.g., "ocr-website-ip")
   - Click "Create"

3. Configure firewall rules:
   - Under "Firewall", add rules to allow HTTP (port 80) and HTTPS (port 443)
   - Make sure SSH (port 22) is also allowed

4. If you have a domain name, set up DNS:
   - Go to your domain registrar's website
   - Create an A record pointing to your static IP address
   - Optionally, create a CNAME record for "www" pointing to your domain

## Step 3: Connect to Your Instance

1. From the Lightsail dashboard, select your instance

2. Click "Connect using SSH" to open a browser-based SSH session, or

3. Use the SSH key to connect from your terminal:
   - Download the SSH key from the "Account" page in Lightsail
   - Save it to your local machine (e.g., as "LightsailDefaultKey.pem")
   - Set the correct permissions: `chmod 400 LightsailDefaultKey.pem`
   - Connect using: `ssh -i LightsailDefaultKey.pem ubuntu@your-static-ip`

## Step 4: Install Dependencies

Once connected to your instance, install the required dependencies:

```bash
# Update package lists
sudo apt-get update

# Install Git
sudo apt-get install -y git

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu
rm get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.25.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Log out and log back in for the docker group to take effect
exit
```

Reconnect to your instance after logging out.

## Step 5: Clone the Repository

```bash
# Clone the repository
git clone https://github.com/yourusername/OCR_Website.git
cd OCR_Website

# Create required directories
mkdir -p uploads ocr_cache logs/caddy
```

## Step 6: Configure the Application

1. Update the Caddyfile with your domain name:

```bash
# Replace yourdomain.com with your actual domain
sed -i "s/yourdomain.com/your-actual-domain.com/g" Caddyfile

# Replace the email address for Let's Encrypt
sed -i "s/your-email@example.com/your-actual-email@example.com/g" Caddyfile
```

2. Generate a secure secret key and configure environment variables:

```bash
# Create environment file from template
cp .env.example .env

# Generate a random secret key
export SECRET_KEY=$(openssl rand -hex 32)
echo "SECRET_KEY=$SECRET_KEY" >> .env

# Configure mail settings (replace with your actual email settings)
echo "MAIL_USERNAME=your-email@gmail.com" >> .env
echo "MAIL_PASSWORD=your-app-password" >> .env
echo "MAIL_DEFAULT_SENDER=your-email@gmail.com" >> .env

echo "Generated SECRET_KEY: $SECRET_KEY"
echo "Remember to update the mail settings in .env file"
```

## Step 7: Deploy the Application

```bash
# Build and start the Docker containers
docker-compose up -d --build

# Check if the containers are running
docker-compose ps

# Initialize the database (run this after the containers are up)
docker-compose exec flask python -c "
from app import app, db
with app.app_context():
    db.create_all()
    print('Database tables created successfully!')
"
```

## Step 8: Test the Deployment

1. Open your domain in a web browser (or use the static IP if you don't have a domain)

2. Test the OCR functionality by uploading a PDF file

3. Check the logs if you encounter any issues:

```bash
# View logs from all containers
docker-compose logs

# View logs from a specific container
docker-compose logs flask
docker-compose logs caddy
```

## Step 9: Set Up Automatic Updates (Optional)

Create a script to automatically update the application:

```bash
cat > update.sh << 'EOF'
#!/bin/bash
cd /home/ubuntu/OCR_Website
git pull
docker-compose up -d --build
EOF

chmod +x update.sh
```

Set up a cron job to run the update script weekly:

```bash
(crontab -l 2>/dev/null; echo "0 0 * * 0 /home/ubuntu/OCR_Website/update.sh >> /home/ubuntu/update.log 2>&1") | crontab -
```

## Step 10: Set Up Monitoring (Optional)

1. Install a monitoring tool like Netdata:

```bash
bash <(curl -Ss https://my-netdata.io/kickstart.sh)
```

2. Access the monitoring dashboard at `http://your-static-ip:19999`

## Troubleshooting

### If the application doesn't start:

1. Check the Docker logs:
```bash
docker-compose logs
```

2. Verify that the required ports are open:
```bash
sudo netstat -tulpn | grep -E '80|443'
```

3. Check if Docker containers are running:
```bash
docker ps
```

### If Caddy can't obtain SSL certificates:

1. Make sure your domain's DNS is properly configured
2. Check if port 80 and 443 are open in your firewall
3. Check Caddy logs:
```bash
docker-compose logs caddy
```

## Maintenance

### Backing up data:

```bash
# Backup the uploads and cache directories
tar -czvf ocr-website-data-$(date +%Y%m%d).tar.gz uploads ocr_cache
```

### Updating the application:

```bash
# Pull the latest changes
git pull

# Rebuild and restart the containers
docker-compose up -d --build
```

### Monitoring disk space:

```bash
# Check disk usage
df -h

# Check the size of the application directories
du -sh uploads ocr_cache
```

## Security Considerations

1. Set up a firewall using UFW:
```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

2. Set up automatic security updates:
```bash
sudo apt-get install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

3. Consider setting up fail2ban to protect against brute force attacks:
```bash
sudo apt-get install -y fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```
