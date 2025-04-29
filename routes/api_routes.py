"""
API routes for LinkedIn Business Intelligence Extractor
"""
from flask import Blueprint, request, jsonify
from scraper import scrape_website
from linkedin_finder import extract_linkedin_url, find_and_extract_linkedin_about
from enhanced_linkedin_scraper import extract_all_company_data
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Create blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/scrape', methods=['POST'])
def scrape():
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
            
            # Try to get a better company name from the data
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

@api_bp.route('/find_linkedin', methods=['POST'])
def find_linkedin():
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

@api_bp.route('/batch', methods=['POST'])
def batch_process():
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
            
            # Process based on mode
            if mode == 'find_linkedin':
                # Find LinkedIn URL and extract data
                result = find_and_extract_linkedin_about(url)
                
                if result["success"]:
                    results.append({
                        'success': True,
                        'website_url': url,
                        'linkedin_url': result["linkedin_url"],
                        'data': result["company_data"]
                    })
                else:
                    results.append({
                        'success': False,
                        'website_url': url,
                        'error': result["message"]
                    })
            
            # Direct scraping mode
            elif mode == 'direct':
                # Direct scraping of the URL (LinkedIn or regular website)
                if 'linkedin.com' in url and use_auth:
                    enhanced_data = extract_all_company_data(url)
                    results.append({
                        'success': True,
                        'url': url,
                        'data': {
                            'company_name': "LinkedIn Company",
                            'description': "Data extracted with LinkedIn authentication",
                            'linkedin_data': enhanced_data,
                            'authenticated': True
                        }
                    })
                else:
                    # Regular scraping for non-LinkedIn URLs
                    result = scrape_website(url)
                    if result is not None:
                        results.append({
                            'success': True,
                            'url': url,
                            'data': result
                        })
                    else:
                        results.append({
                            'success': False,
                            'url': url,
                            'error': 'Failed to extract data from website'
                        })
            
            else:
                results.append({
                    'success': False,
                    'url': url,
                    'error': f'Invalid mode: {mode}'
                })
            
        except Exception as e:
            logger.error(f"Batch error for URL {url}: {str(e)}")
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

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for AWS Amplify"""
    return jsonify({
        'status': 'healthy',
        'service': 'LinkedIn Business Intelligence Extractor API',
        'version': '1.0.0'
    })