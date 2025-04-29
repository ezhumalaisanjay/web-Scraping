#!/bin/bash

# Start Flask application with gunicorn after AWS Amplify deployment
echo "Starting Flask application with gunicorn"

# Make this script executable
chmod +x /var/app/current/.platform/hooks/postdeploy/01_start_application.sh

# Activate virtual environment
source /var/app/venv/bin/activate

# Change to application directory
cd /var/app/current

# Start gunicorn in the background
gunicorn --bind 0.0.0.0:8080 --workers 3 main:app --daemon

echo "Application started in the background with gunicorn"