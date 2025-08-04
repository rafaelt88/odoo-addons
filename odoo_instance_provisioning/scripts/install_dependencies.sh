#!/bin/bash

# Installation script for Odoo Instance Provisioning Module
# Usage: ./install_dependencies.sh

set -e

echo "🚀 Installing dependencies for Odoo Instance Provisioning Module"
echo "================================================================="

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "❌ This script should not be run as root. Please run as the odoo user."
   exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Install Python dependencies
echo "📦 Installing Python dependencies..."

if command_exists pip3; then
    PIP_CMD="pip3"
elif command_exists pip; then
    PIP_CMD="pip"
else
    echo "❌ pip not found. Please install pip first."
    exit 1
fi

echo "Using: $PIP_CMD"

# Install required Python packages
echo "Installing psycopg2-binary..."
$PIP_CMD install psycopg2-binary --user

echo "Installing requests..."
$PIP_CMD install requests --user

# Optional Docker installation (for container management)
read -p "🐳 Do you want to install Docker Python library? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Installing docker..."
    $PIP_CMD install docker --user
    echo "✅ Docker Python library installed"
else
    echo "⚠️  Docker library skipped. Container features will not be available."
fi

# Check Docker daemon
if command_exists docker; then
    echo "🐳 Docker daemon found"
    
    # Check if user can access Docker
    if docker info >/dev/null 2>&1; then
        echo "✅ Docker access confirmed"
    else
        echo "⚠️  Docker found but user cannot access it."
        echo "   You may need to add user to docker group:"
        echo "   sudo usermod -aG docker $USER"
        echo "   Then logout and login again."
    fi
else
    echo "⚠️  Docker daemon not found. Please install Docker if you want container features."
    echo "   Ubuntu/Debian: sudo apt-get install docker.io"
    echo "   CentOS/RHEL: sudo yum install docker"
fi

# Check PostgreSQL
if command_exists psql; then
    echo "🐘 PostgreSQL client found"
    
    # Test connection
    if sudo -u postgres psql -c "SELECT version();" >/dev/null 2>&1; then
        echo "✅ PostgreSQL server accessible"
    else
        echo "⚠️  PostgreSQL client found but server not accessible"
        echo "   Please ensure PostgreSQL server is running and configured properly"
    fi
else
    echo "⚠️  PostgreSQL client not found"
    echo "   Ubuntu/Debian: sudo apt-get install postgresql-client"
    echo "   CentOS/RHEL: sudo yum install postgresql"
fi

# Check Nginx/Apache for reverse proxy
if command_exists nginx; then
    echo "🌐 Nginx found"
elif command_exists apache2 || command_exists httpd; then
    echo "🌐 Apache found"
else
    echo "⚠️  No web server found. You'll need Nginx or Apache for reverse proxy"
    echo "   Ubuntu/Debian: sudo apt-get install nginx"
    echo "   CentOS/RHEL: sudo yum install nginx"
fi

echo ""
echo "🎉 Dependency installation completed!"
echo ""
echo "📋 Next steps:"
echo "1. Restart your Odoo server"
echo "2. Update the app list in Odoo"
echo "3. Install the 'Odoo Instance Provisioning' module"
echo "4. Configure system parameters in Settings"
echo ""
echo "📖 For detailed configuration, see README.md"
