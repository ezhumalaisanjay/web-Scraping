#!/bin/bash
# Start application script for LinkedIn Business Intelligence Extractor
# Compatible with AWS Amplify deployment

echo "Starting LinkedIn Business Intelligence Extractor application..."

# Load environment variables if .env file exists
if [ -f .env ]; then
    echo "Loading environment variables from .env file"
    export $(grep -v '^#' .env | xargs)
fi

# Set default port if not defined
if [ -z "$PORT" ]; then
    echo "PORT not defined, using default port 8080"
    export PORT=8080
else
    echo "Using configured PORT: $PORT"
fi

# Set Python path if not defined
if [ -z "$PYTHONPATH" ]; then
    echo "Setting PYTHONPATH to current directory"
    export PYTHONPATH=$(pwd)
fi

# Start application with gunicorn
echo "Starting application with gunicorn on port $PORT"
gunicorn --bind 0.0.0.0:$PORT --workers 3 --timeout 120 --access-logfile=- --error-logfile=- main:app

# Exit with gunicorn's exit code
exit $?