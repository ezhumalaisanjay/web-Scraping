"""
AWS Elastic Beanstalk Application Entry Point

This file serves as the entry point for AWS Elastic Beanstalk.
It imports the Flask application from main.py and makes it available
as 'application' which is the name that AWS EB looks for.
"""

from main import app as application

# This is for AWS Elastic Beanstalk
if __name__ == "__main__":
    # When running locally
    application.run(host="0.0.0.0", port=5000)