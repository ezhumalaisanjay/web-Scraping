#!/bin/bash

# Set up Python environment for Flask application on AWS Amplify
echo "Setting up Python environment for Flask application"

# Create virtual environment if it doesn't exist
if [ ! -d "/var/app/venv" ]; then
    python3 -m venv /var/app/venv
fi

# Activate virtual environment
source /var/app/venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -e .
pip install gunicorn
pip install flask
pip install flask-cors

# Make sure directories exist
mkdir -p /var/app/current/static/css
mkdir -p /var/app/current/static/js
mkdir -p /var/app/current/static/images

echo "Python environment setup complete"