from flask import Flask
from flask_cors import CORS
import os
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
CORS(app)

# Set LinkedIn credentials from environment variables 
os.environ['LINKEDIN_EMAIL'] = os.environ.get('LINKEDIN_EMAIL', '')
os.environ['LINKEDIN_PASSWORD'] = os.environ.get('LINKEDIN_PASSWORD', '')

# Register blueprints
from routes.main_routes import main_bp
from routes.api_routes import api_bp
from routes.scrape_routes import scrape_bp

app.register_blueprint(main_bp)
app.register_blueprint(api_bp)
app.register_blueprint(scrape_bp)

# This is required for the gunicorn command to work properly
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)