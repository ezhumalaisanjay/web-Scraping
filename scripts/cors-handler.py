#!/usr/bin/env python3
"""
CORS Handler for AWS Amplify

This script is used to add CORS headers to the Flask application when deployed on AWS Amplify.
"""

from functools import wraps
from flask import Flask, request, jsonify, current_app

def setup_cors(app):
    """Set up CORS headers for all routes"""
    @app.after_request
    def add_cors_headers(response):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Health check endpoint for AWS Amplify"""
        return jsonify({
            'status': 'healthy',
            'service': 'LinkedIn Business Intelligence Extractor',
            'version': '1.0.0'
        })
    
    @app.route('/api/test-cors', methods=['GET'])
    def test_cors():
        """Test CORS endpoint"""
        return jsonify({'cors': 'enabled'})
    
    # Handle OPTIONS requests
    @app.route('/', methods=['OPTIONS'])
    @app.route('/<path:path>', methods=['OPTIONS'])
    def options_handler(path=None):
        response = current_app.make_default_options_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response