"""
Scraping routes for LinkedIn Business Intelligence Extractor
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for
from scraper import scrape_website
from linkedin_finder import extract_linkedin_url, find_and_extract_linkedin_about
from enhanced_linkedin_scraper import extract_all_company_data
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Create blueprint
scrape_bp = Blueprint('scrape', __name__)

@scrape_bp.route('/scrape', methods=['GET', 'POST'])
def scrape():
    """Handle website scraping requests"""
    if request.method == 'GET':
        # If accessed directly via GET, redirect to the main page
        return redirect(url_for('main.index'))
        
    url = request.form.get('url')
    mode = request.form.get('mode', 'direct')  # Default to direct scraping
    use_auth = request.form.get('use_auth', 'false') == 'true'
    
    if not url:
        flash('Please enter a valid URL', 'danger')
        return redirect(url_for('main.index'))
    
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
                return redirect(url_for('main.index'))
            
            return render_template('results.html', data=result, url=url)
        
        # Find LinkedIn URL from company website and then scrape
        elif mode == 'find_linkedin':
            logger.info(f"Finding LinkedIn URL from website: {url}")
            linkedin_result = find_and_extract_linkedin_about(url)
            
            if not linkedin_result["success"]:
                flash(f'Failed to find LinkedIn profile: {linkedin_result["message"]}', 'danger')
                return redirect(url_for('main.index'))
            
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
            return redirect(url_for('main.index'))
    
    except Exception as e:
        logger.error(f"Error scraping website: {str(e)}")
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('main.index'))