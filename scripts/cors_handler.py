"""
CORS Handler for AWS Amplify

This script is used to add CORS headers to the Flask application when deployed on AWS Amplify.
"""
from flask import Flask, request, make_response


def setup_cors(app):
    """Set up CORS headers for all routes"""
    
    @app.after_request
    def add_cors_headers(response):
        """Add CORS headers to all responses"""
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    @app.route('/health')
    def health_check():
        """Health check endpoint for AWS Amplify"""
        return {'status': 'healthy', 'environment': 'aws-amplify'}, 200
    
    @app.route('/cors-test')
    def test_cors():
        """Test CORS endpoint"""
        return {'cors': 'enabled', 'message': 'CORS headers are being applied correctly'}, 200
    
    @app.route('/<path:path>', methods=['OPTIONS'])
    @app.route('/', methods=['OPTIONS'])
    def options_handler(path=None):
        """Handle OPTIONS requests for CORS preflight requests"""
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.headers['Access-Control-Max-Age'] = '3600'
        return response