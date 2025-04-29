#!/bin/bash
# Setup script that runs before the application is deployed

# Install system dependencies if needed
echo "Installing system dependencies..."

# Create necessary directories
mkdir -p /tmp/logs

# Set proper permissions
chmod -R 755 /tmp/logs

# Print Python version and installed packages
echo "Python version:"
python --version
echo "Installed packages:"
pip list

echo "Pre-deploy setup completed"