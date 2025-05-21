#!/bin/bash

# Aracannabis Prontuário - Deployment Script
# This script automates the deployment process for the Aracannabis Prontuário application

set -e  # Exit immediately if a command exits with a non-zero status

# Configuration
APP_NAME="aracannabis"
APP_DIR="/var/www/$APP_NAME"
BACKEND_DIR="$APP_DIR/backend"
FRONTEND_DIR="$APP_DIR/frontend"
GIT_REPO="https://github.com/gituser26071977/REDACTED.git"
DOMAIN="your_domain.com"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print status messages
print_status() {
    echo -e "${YELLOW}[*] $1${NC}"
}

# Function to print success messages
print_success() {
    echo -e "${GREEN}[+] $1${NC}"
}

# Function to print error messages
print_error() {
    echo -e "${RED}[-] $1${NC}"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run as root"
    exit 1
fi

# Update system
print_status "Updating system packages..."
apt update && apt upgrade -y
print_success "System updated"

# Install dependencies if not already installed
print_status "Installing dependencies..."
apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib nginx certbot python3-certbot-nginx git nodejs npm

# Create application directory
print_status "Creating application directory..."
mkdir -p $BACKEND_DIR
mkdir -p $FRONTEND_DIR
chown -R www-data:www-data $APP_DIR

# Clone or pull the repository
if [ -d "$APP_DIR/.git" ]; then
    print_status "Updating existing repository..."
    cd $APP_DIR
    git pull
else
    print_status "Cloning repository..."
    rm -rf $APP_DIR
    git clone $GIT_REPO $APP_DIR
fi

# Setup backend
print_status "Setting up backend..."
cd $BACKEND_DIR

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate virtual environment and install dependencies
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    cp .env.example .env
    print_status "Created .env file. Please edit it with your configuration."
    print_status "Press Enter to continue after editing..."
    read
fi

# Setup database
print_status "Setting up database..."
sudo -u postgres psql -c "CREATE DATABASE $APP_NAME;" || true
sudo -u postgres psql -c "CREATE USER ${APP_NAME}_user WITH PASSWORD 'secure_password';" || true
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $APP_NAME TO ${APP_NAME}_user;" || true

# Initialize database
print_status "Initializing database..."
source venv/bin/activate
python -c "from app import create_app; app = create_app(); from models import db; app.app_context().push(); db.create_all()"

# Setup frontend
print_status "Setting up frontend..."
cd $FRONTEND_DIR
npm install
npm run build

# Setup Nginx
print_status "Setting up Nginx..."
cp $APP_DIR/nginx.conf /etc/nginx/sites-available/$APP_NAME
sed -i "s/your_domain.com/$DOMAIN/g" /etc/nginx/sites-available/$APP_NAME

# Enable site if not already enabled
if [ ! -f "/etc/nginx/sites-enabled/$APP_NAME" ]; then
    ln -s /etc/nginx/sites-available/$APP_NAME /etc/nginx/sites-enabled/
fi

# Setup SSL with Certbot
print_status "Setting up SSL..."
certbot --nginx -d $DOMAIN

# Setup systemd service
print_status "Setting up systemd service..."
cp $APP_DIR/aracannabis.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable aracannabis
systemctl restart aracannabis

# Restart Nginx
print_status "Restarting Nginx..."
systemctl restart nginx

print_success "Deployment completed successfully!"
print_success "Your application is now running at https://$DOMAIN"
