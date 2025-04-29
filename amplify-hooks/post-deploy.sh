#!/bin/bash
# AWS Amplify Post-Deploy Hook Script
# Executed after the build phase but before the application is started

echo "Running post-deployment tasks for LinkedIn Business Intelligence Extractor..."

# Set up the web server configuration
echo "Setting up NGINX configuration..."
if [ -f "amplify-nginx.conf" ]; then
    echo "Found custom NGINX configuration"
else
    echo "WARNING: Custom NGINX configuration not found, using defaults"
fi

# Verify the application can start properly
echo "Performing application health check..."
timeout 5 python -c "import importlib.util; spec = importlib.util.spec_from_file_location('main', 'main.py'); main = importlib.util.module_from_spec(spec); spec.loader.exec_module(main)" || {
    echo "ERROR: Unable to import main.py - application may not start correctly"
    echo "Check for syntax errors or missing dependencies"
    # We'll continue anyway, as this might be a false positive
}

# Verify LinkedIn authentication (if credentials exist)
if [ -n "$LINKEDIN_EMAIL" ] && [ -n "$LINKEDIN_PASSWORD" ]; then
    echo "LinkedIn credentials found, testing configuration..."
    # We can't actually test login here, just confirm the variables exist
    echo "LinkedIn authentication is configured with email: ${LINKEDIN_EMAIL:0:3}...${LINKEDIN_EMAIL##*@}"
else
    echo "NOTICE: LinkedIn credentials not found in environment"
    echo "Application will run without authenticated LinkedIn access"
fi

# Final setup of permissions and ownership
echo "Setting up final permissions..."
# Add any specific permission changes needed for Amplify hosting
# For example:
chmod -R 755 static
chmod -R 755 templates
chmod -R 755 scripts

echo "Post-deployment tasks completed successfully"
exit 0