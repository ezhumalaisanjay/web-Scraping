#!/bin/bash
# AWS Amplify Pre-Deploy Hook Script
# Executed before the build phase

echo "Running pre-deployment tasks for LinkedIn Business Intelligence Extractor..."

# Ensure we have the right Python version
echo "Setting up Python environment..."
python --version

# Create necessary directories
echo "Creating required directories..."
mkdir -p static/css
mkdir -p static/js
mkdir -p static/images
mkdir -p templates
mkdir -p logs

# Verify the presence of critical files
echo "Verifying critical files..."
required_files=("main.py" "routes/__init__.py" "scripts/cors_handler.py")
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "ERROR: Required file $file is missing!"
        exit 1
    fi
done

# Set up environment variables if needed
if [ ! -f ".env" ]; then
    echo "Creating .env file with default settings..."
    echo "FLASK_APP=main.py" > .env
    echo "FLASK_ENV=production" >> .env
    echo "PORT=8080" >> .env
    echo "PYTHONPATH=$(pwd)" >> .env
fi

# Check for LinkedIn credentials
if [ -n "$LINKEDIN_EMAIL" ] && [ -n "$LINKEDIN_PASSWORD" ]; then
    echo "LinkedIn credentials found in environment"
else
    echo "NOTICE: LinkedIn credentials not found in environment variables"
    echo "Authentication with LinkedIn will not be available"
fi

# Make scripts executable
echo "Setting executable permissions for scripts..."
chmod +x scripts/*.sh
chmod +x amplify-hooks/*.sh

echo "Pre-deployment tasks completed successfully"
exit 0