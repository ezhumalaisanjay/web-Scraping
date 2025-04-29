"""
Main routes for LinkedIn Business Intelligence Extractor
"""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Create blueprint
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@main_bp.route('/index')
@main_bp.route('/index.html')
def index():
    """Render the main landing page"""
    return render_template('index.html', redirect_url=request.args.get('redirect', '/'))

@main_bp.route('/scrape/', methods=['GET', 'POST'])
@main_bp.route('/scrape', methods=['GET', 'POST'])
def scrape_form():
    """Handle both form display and submission"""
    if request.method == 'GET':
        return render_template('linkedin_form.html')
    else:
        url = request.form.get('url')
        mode = request.form.get('mode', 'direct')
        use_auth = request.form.get('use_auth', 'false') == 'true'
        
        if not url:
            flash('Please enter a URL', 'error')
            return redirect(url_for('main.scrape_form'))
            
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        try:
            from scraper import scrape_website
            result = scrape_website(url)
            return render_template('results.html', url=url, data=result)
        except Exception as e:
            flash(str(e), 'error')
            return redirect(url_for('main.scrape_form'))

@main_bp.route('/extract')
def extract_data():
    """Render the LinkedIn extraction form page"""
    return render_template('linkedin_form.html')

@main_bp.route('/about')
def about():
    """Render the about page"""
    return render_template('about.html')

@main_bp.route('/batch/')
@main_bp.route('/batch')
def batch():
    """Render the batch processing page"""
    return render_template('batch_form.html')

@main_bp.route('/health')
def health_check():
    """Health check endpoint for AWS Amplify"""
    return jsonify({
        'status': 'healthy',
        'service': 'LinkedIn Business Intelligence Extractor',
        'version': '1.0.0'
    })

@main_bp.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return redirect(url_for('static', filename=filename))