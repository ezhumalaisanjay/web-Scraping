#!/bin/bash
# Post-installation script for LinkedIn Business Intelligence Extractor
# Compatible with AWS Amplify deployment environment

echo "Running post-installation setup for LinkedIn Business Intelligence Extractor..."

# Check if we're in an AWS Amplify environment
if [ -n "$AWS_EXECUTION_ENV" ] || [ -n "$AMPLIFY_APP_ID" ]; then
    echo "Detected AWS Amplify environment"
    APP_DIR="$CODEBUILD_SRC_DIR"
else
    # Fallback for other environments
    APP_DIR=$(pwd)
    echo "Using current directory as app directory: $APP_DIR"
fi

# Create necessary directories
mkdir -p static/css
mkdir -p static/js
mkdir -p static/images

# Install app dependencies (if not already done)
echo "Installing application dependencies..."
pip install --upgrade pip
pip install -e .

# Set environment variables
if [ ! -f ".env" ]; then
    echo "Creating environment file..."
    echo "FLASK_APP=main.py" > .env
    echo "FLASK_ENV=production" >> .env
    echo "PORT=8080" >> .env
    echo "PYTHONPATH=$APP_DIR" >> .env
    
    # Add LinkedIn credentials if provided as environment variables
    if [ ! -z "$LINKEDIN_EMAIL" ] && [ ! -z "$LINKEDIN_PASSWORD" ]; then
        echo "Adding LinkedIn credentials to environment..."
        echo "LINKEDIN_EMAIL=$LINKEDIN_EMAIL" >> .env
        echo "LINKEDIN_PASSWORD=$LINKEDIN_PASSWORD" >> .env
    else
        echo "LinkedIn credentials not found in environment variables"
    fi
else
    echo "Environment file already exists, updating if needed..."
    # Update PYTHONPATH if not already set
    if ! grep -q "PYTHONPATH" .env; then
        echo "PYTHONPATH=$APP_DIR" >> .env
    fi
    # Update PORT if not already set
    if ! grep -q "PORT" .env; then
        echo "PORT=8080" >> .env
    fi
fi

# Make script files executable
echo "Setting executable permissions for scripts..."
chmod +x scripts/*.sh
if [ -d "amplify-hooks" ]; then
    chmod +x amplify-hooks/*.sh
fi

echo "Post-installation setup completed successfully"