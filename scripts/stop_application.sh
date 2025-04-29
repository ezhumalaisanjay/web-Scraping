#!/bin/bash
# Stop application script for LinkedIn Business Intelligence Extractor
# Compatible with AWS Amplify deployment

echo "Stopping LinkedIn Business Intelligence Extractor application..."

# Check if the PID file exists (for traditional setups)
if [ -f ./gunicorn.pid ]; then
    # Get the PID
    PID=$(cat ./gunicorn.pid)
    
    # Check if the process is running
    if ps -p $PID > /dev/null; then
        echo "Stopping application with PID $PID..."
        kill $PID
        
        # Wait for the process to terminate
        sleep 3
        
        # Force kill if still running
        if ps -p $PID > /dev/null; then
            echo "Force stopping application..."
            kill -9 $PID
        fi
        
        echo "Application stopped"
    else
        echo "Application is not running (PID $PID not found)"
    fi
    
    # Remove the PID file
    rm -f ./gunicorn.pid
    echo "Removed PID file"
else
    echo "No PID file found, attempting to find and kill gunicorn processes"
    
    # Find all gunicorn processes running this application
    PIDS=$(pgrep -f "gunicorn.*main:app")
    
    if [ -n "$PIDS" ]; then
        echo "Found gunicorn processes: $PIDS"
        echo "Stopping all gunicorn processes..."
        
        # Send terminate signal
        pkill -f "gunicorn.*main:app"
        
        # Wait for processes to terminate
        sleep 3
        
        # Force kill if any still running
        if pgrep -f "gunicorn.*main:app" > /dev/null; then
            echo "Force stopping remaining processes..."
            pkill -9 -f "gunicorn.*main:app"
        fi
        
        echo "All gunicorn processes stopped"
    else
        echo "No gunicorn processes found running this application"
    fi
fi

echo "Application shutdown completed"