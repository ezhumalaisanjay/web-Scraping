import os
import logging
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for, make_response
from scraper import scrape_website
from linkedin_finder import extract_linkedin_url, find_and_extract_linkedin_about
# Use enhanced LinkedIn scraper that can handle 999 status code errors
from enhanced_linkedin_scraper import extract_all_company_data

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Set LinkedIn credentials from environment variables 
os.environ['LINKEDIN_EMAIL'] = os.environ.get('LINKEDIN_EMAIL', '')
os.environ['LINKEDIN_PASSWORD'] = os.environ.get('LINKEDIN_PASSWORD', '')

# Add CORS headers
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response

# Handle OPTIONS method for all routes
@app.route('/', defaults={'path': ''}, methods=['OPTIONS'])
@app.route('/<path:path>', methods=['OPTIONS'])
def handle_options(path):
    response = make_response()
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response

@app.route('/', methods=['GET'])
def index():
    """Render the main page with URL input form"""
    return render_template('index.html')

@app.route('/scrape', methods=['GET'])
def scrape_form():
    """Render the scraping form page"""
    return render_template('index.html')

@app.route('/batch', methods=['GET'])
def batch():
    """Render the batch processing page"""
    return render_template('batch.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    """Handle website scraping requests"""
    url = request.form.get('url')
    mode = request.form.get('mode', 'direct')  # Default to direct scraping
    use_auth = request.form.get('use_auth', 'false') == 'true'
    
    if not url:
        flash('Please enter a valid URL', 'danger')
        return redirect(url_for('index'))
    
    # Add http:// prefix if not present
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    logger.debug(f"Scraping URL: {url} in mode: {mode}, use_auth: {use_auth}")
    
    try:
        # Use authenticated scraping for LinkedIn if requested
        if use_auth and ('linkedin.com' in url):
            logger.info(f"Using authenticated scraping for LinkedIn URL: {url}")
            enhanced_data = extract_all_company_data(url)
            
            # Create result structure compatible with our templates
            result = {
                'company_name': "LinkedIn Company",
                'description': "Data extracted with LinkedIn authentication",
                'linkedin_data': enhanced_data
            }
            
            # Try to get a better company name
            if enhanced_data.get('people', {}).get('leaders'):
                for leader in enhanced_data['people']['leaders']:
                    if 'title' in leader and ('CEO' in leader['title'] or 'Founder' in leader['title']):
                        company_name = leader['name'].split(' at ')[-1] if ' at ' in leader['name'] else None
                        if company_name:
                            result['company_name'] = company_name
            
            flash('Successfully extracted LinkedIn data using authentication', 'success')
            return render_template('results.html', 
                                  data=result, 
                                  url=url,
                                  authenticated=True)
        
        # Direct scraping mode (LinkedIn or any website)
        elif mode == 'direct':
            result = scrape_website(url)
            if result is None:
                flash('Failed to extract data from the website', 'danger')
                return redirect(url_for('index'))
            
            return render_template('results.html', data=result, url=url)
        
        # Find LinkedIn URL from company website and then scrape
        elif mode == 'find_linkedin':
            logger.info(f"Finding LinkedIn URL from website: {url}")
            linkedin_result = find_and_extract_linkedin_about(url)
            
            if not linkedin_result["success"]:
                flash(f'Failed to find LinkedIn profile: {linkedin_result["message"]}', 'danger')
                return redirect(url_for('index'))
            
            # We have LinkedIn data - prepare for display
            result = linkedin_result["company_data"]
            linkedin_url = linkedin_result["linkedin_url"]
            
            # If we found a LinkedIn URL and authentication is enabled, use authenticated scraping
            if use_auth and linkedin_url:
                logger.info(f"Using authenticated scraping for found LinkedIn URL: {linkedin_url}")
                enhanced_data = extract_all_company_data(linkedin_url)
                
                # Merge the enhanced data with existing data
                if 'linkedin_data' not in result:
                    result['linkedin_data'] = {}
                
                # Add enhanced data
                if enhanced_data.get('posts'):
                    result['linkedin_data']['posts'] = enhanced_data['posts']
                if enhanced_data.get('jobs'):
                    result['linkedin_data']['jobs'] = enhanced_data['jobs']
                if enhanced_data.get('people'):
                    result['linkedin_data']['people'] = enhanced_data['people']
                
                flash(f'Successfully found and extracted LinkedIn profile with authentication: {linkedin_url}', 'success')
            else:
                flash(f'Successfully found and extracted LinkedIn profile: {linkedin_url}', 'success')
            
            return render_template('results.html', 
                                  data=result, 
                                  url=url, 
                                  linkedin_url=linkedin_url,
                                  source_website=url,
                                  authenticated=use_auth)
        
        else:
            flash(f'Invalid scraping mode: {mode}', 'danger')
            return redirect(url_for('index'))
    
    except Exception as e:
        logger.error(f"Error scraping website: {str(e)}")
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('index'))

@app.route('/api/scrape', methods=['POST'])
def api_scrape():
    """API endpoint for scraping websites"""
    data = request.get_json()
    
    if not data or 'url' not in data:
        return jsonify({
            'success': False,
            'error': 'URL parameter is required'
        }), 400
    
    url = data['url']
    mode = data.get('mode', 'direct')  # Default to direct scraping
    use_auth = data.get('use_auth', False)  # Authentication option
    
    # Add http:// prefix if not present
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    try:
        # Authenticated LinkedIn scraping mode
        if use_auth and ('linkedin.com' in url):
            logger.info(f"API: Using authenticated scraping for LinkedIn URL: {url}")
            enhanced_data = extract_all_company_data(url)
            
            # Create result structure
            result = {
                'company_name': "LinkedIn Company",
                'description': "Data extracted with LinkedIn authentication",
                'linkedin_data': enhanced_data,
                'authenticated': True
            }
            
            # Try to get a better company name
            if enhanced_data.get('people', {}).get('leaders'):
                for leader in enhanced_data['people']['leaders']:
                    if 'title' in leader and ('CEO' in leader['title'] or 'Founder' in leader['title']):
                        company_name = leader['name'].split(' at ')[-1] if ' at ' in leader['name'] else None
                        if company_name:
                            result['company_name'] = company_name
            
            return jsonify({
                'success': True,
                'data': result,
                'url': url,
                'authenticated': True
            })
            
        # Direct scraping mode
        elif mode == 'direct':
            result = scrape_website(url)
            if result is None:
                return jsonify({
                    'success': False,
                    'error': 'Failed to extract data from the website'
                }), 500
            
            return jsonify({
                'success': True,
                'data': result
            })
        
        # Find LinkedIn URL from website and then scrape it
        elif mode == 'find_linkedin':
            linkedin_result = find_and_extract_linkedin_about(url)
            
            if not linkedin_result["success"]:
                return jsonify({
                    'success': False,
                    'error': linkedin_result["message"],
                    'website_url': url,
                    'linkedin_url': linkedin_result.get('linkedin_url')
                }), 404
            
            # If we found a LinkedIn URL and authentication is enabled, use authenticated scraping
            if use_auth and linkedin_result.get("linkedin_url"):
                linkedin_url = linkedin_result["linkedin_url"]
                logger.info(f"API: Using authenticated scraping for found LinkedIn URL: {linkedin_url}")
                enhanced_data = extract_all_company_data(linkedin_url)
                
                # Merge the enhanced data with existing data
                company_data = linkedin_result["company_data"]
                if 'linkedin_data' not in company_data:
                    company_data['linkedin_data'] = {}
                
                # Add enhanced data
                if enhanced_data.get('posts'):
                    company_data['linkedin_data']['posts'] = enhanced_data['posts']
                if enhanced_data.get('jobs'):
                    company_data['linkedin_data']['jobs'] = enhanced_data['jobs']
                if enhanced_data.get('people'):
                    company_data['linkedin_data']['people'] = enhanced_data['people']
                
                return jsonify({
                    'success': True,
                    'website_url': url,
                    'linkedin_url': linkedin_url,
                    'data': company_data,
                    'authenticated': True
                })
            else:
                # Standard non-authenticated response
                return jsonify({
                    'success': True,
                    'website_url': url,
                    'linkedin_url': linkedin_result["linkedin_url"],
                    'data': linkedin_result["company_data"]
                })
            
        else:
            return jsonify({
                'success': False,
                'error': f'Invalid mode: {mode}. Use "direct" or "find_linkedin".'
            }), 400
    
    except Exception as e:
        logger.error(f"API error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
        
@app.route('/api/find_linkedin', methods=['POST'])
def api_find_linkedin():
    """API endpoint just for finding LinkedIn URLs without scraping them"""
    data = request.get_json()
    
    if not data or 'url' not in data:
        return jsonify({
            'success': False,
            'error': 'URL parameter is required'
        }), 400
    
    url = data['url']
    
    # Add http:// prefix if not present
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    try:
        linkedin_url = extract_linkedin_url(url)
        
        if not linkedin_url:
            return jsonify({
                'success': False,
                'error': f'No LinkedIn URL found on website: {url}',
                'website_url': url
            }), 404
        
        return jsonify({
            'success': True,
            'website_url': url,
            'linkedin_url': linkedin_url
        })
    
    except Exception as e:
        logger.error(f"API find LinkedIn error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/batch', methods=['POST'])
def api_batch_process():
    """API endpoint for batch processing multiple URLs"""
    data = request.get_json()
    
    if not data or 'urls' not in data:
        return jsonify({
            'success': False,
            'error': 'URLs parameter is required as an array'
        }), 400
    
    urls = data['urls']
    mode = data.get('mode', 'find_linkedin')  # Default to find_linkedin mode
    use_auth = data.get('use_auth', False)     # Authentication option
    
    if not isinstance(urls, list):
        return jsonify({
            'success': False,
            'error': 'URLs must be provided as an array'
        }), 400
    
    if len(urls) > 20:
        return jsonify({
            'success': False,
            'error': 'Maximum 20 URLs allowed in batch mode'
        }), 400
    
    results = []
    
    for url in urls:
        try:
            # Add http:// prefix if not present
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # Check if this is a LinkedIn URL and authentication is enabled
            if use_auth and 'linkedin.com' in url and mode == 'direct':
                # Use authenticated LinkedIn scraping
                logger.info(f"Batch: Using authenticated scraping for LinkedIn URL: {url}")
                enhanced_data = extract_all_company_data(url)
                
                # Create result structure
                result_data = {
                    'company_name': "LinkedIn Company",
                    'description': "Data extracted with LinkedIn authentication",
                    'linkedin_data': enhanced_data,
                    'authenticated': True
                }
                
                # Try to get a better company name
                if enhanced_data.get('people', {}).get('leaders'):
                    for leader in enhanced_data['people']['leaders']:
                        if 'title' in leader and ('CEO' in leader['title'] or 'Founder' in leader['title']):
                            company_name = leader['name'].split(' at ')[-1] if ' at ' in leader['name'] else None
                            if company_name:
                                result_data['company_name'] = company_name
                
                results.append({
                    'success': True,
                    'url': url,
                    'data': result_data,
                    'authenticated': True
                })
                continue
            
            # Process based on mode
            if mode == 'find_linkedin':
                # Find LinkedIn URL and extract data
                result = find_and_extract_linkedin_about(url)
                
                if result["success"]:
                    linkedin_url = result["linkedin_url"]
                    company_data = result["company_data"]
                    
                    # If authentication is enabled and LinkedIn URL found, enhance with authenticated data
                    if use_auth and linkedin_url:
                        logger.info(f"Batch: Using authenticated scraping for found LinkedIn URL: {linkedin_url}")
                        enhanced_data = extract_all_company_data(linkedin_url)
                        
                        # Merge enhanced data
                        if 'linkedin_data' not in company_data:
                            company_data['linkedin_data'] = {}
                        
                        if enhanced_data.get('posts'):
                            company_data['linkedin_data']['posts'] = enhanced_data['posts']
                        if enhanced_data.get('jobs'):
                            company_data['linkedin_data']['jobs'] = enhanced_data['jobs']
                        if enhanced_data.get('people'):
                            company_data['linkedin_data']['people'] = enhanced_data['people']
                        
                        results.append({
                            'success': True,
                            'website_url': url,
                            'linkedin_url': linkedin_url,
                            'company_data': company_data,
                            'authenticated': True
                        })
                    else:
                        # Regular non-authenticated result
                        results.append({
                            'success': True,
                            'website_url': url,
                            'linkedin_url': linkedin_url,
                            'company_data': company_data
                        })
                else:
                    results.append({
                        'success': False,
                        'website_url': url,
                        'error': result["message"]
                    })
            
            elif mode == 'linkedin_only':
                # Just find LinkedIn URLs without extracting data
                linkedin_url = extract_linkedin_url(url)
                
                if linkedin_url:
                    results.append({
                        'success': True,
                        'website_url': url,
                        'linkedin_url': linkedin_url
                    })
                else:
                    results.append({
                        'success': False,
                        'website_url': url,
                        'error': 'No LinkedIn URL found'
                    })
            
            elif mode == 'direct':
                # Direct scraping of URLs (could be LinkedIn or any website)
                data = scrape_website(url)
                
                if data:
                    results.append({
                        'success': True,
                        'url': url,
                        'data': data
                    })
                else:
                    results.append({
                        'success': False,
                        'url': url,
                        'error': 'Failed to extract data'
                    })
            
            else:
                return jsonify({
                    'success': False,
                    'error': f'Invalid mode: {mode}. Use "find_linkedin", "linkedin_only", or "direct".'
                }), 400
                
        except Exception as e:
            logger.error(f"Batch processing error for URL {url}: {str(e)}")
            results.append({
                'success': False,
                'url': url,
                'error': str(e)
            })
    
    return jsonify({
        'success': True,
        'results': results,
        'total': len(urls),
        'successful': sum(1 for r in results if r.get('success', False)),
        'failed': sum(1 for r in results if not r.get('success', False))
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
