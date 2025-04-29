#!/bin/bash
# Post-deploy script that runs after the application is deployed

# Log deployment completion
echo "Application deployment completed"

# Run any database migrations if needed
# python manage.py db upgrade

# Restart the application if needed
# sudo systemctl restart your-app-service

# Warm up the application by making an initial request
echo "Warming up the application..."
curl -s http://localhost:5000/ > /dev/null

echo "Post-deploy tasks completed"