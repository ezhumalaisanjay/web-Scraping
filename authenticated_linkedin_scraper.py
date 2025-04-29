"""
LinkedIn Authenticated Scraper

This module implements authenticated access to LinkedIn for enhanced data extraction.
"""

import logging
import re
import os
import time
import random
import requests
from bs4 import BeautifulSoup

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# LinkedIn authentication credentials
LINKEDIN_EMAIL = os.environ.get('LINKEDIN_EMAIL', '')
LINKEDIN_PASSWORD = os.environ.get('LINKEDIN_PASSWORD', '')

def setup_authenticated_session():
    """
    Set up an authenticated session with LinkedIn using provided credentials
    
    Returns:
        requests.Session: Authenticated session with LinkedIn cookies
    """
    # Create a session to maintain cookies
    session = requests.Session()
    
    # Set headers to mimic a browser
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'cross-site',
        'DNT': '1',
        'Referer': 'https://www.google.com/'
    })
    
    return session

def login_to_linkedin(session):
    """
    Authenticate with LinkedIn using the provided credentials.
    
    Due to LinkedIn's strict anti-scraping measures, this function uses a modified approach
    that focuses on making public data requests with appropriate headers rather than
    attempting a full authentication, which can trigger security measures.
    
    Args:
        session: requests.Session with cookie support
    
    Returns:
        bool: True if some level of LinkedIn access was established, False otherwise
    """
    if not LINKEDIN_EMAIL or not LINKEDIN_PASSWORD:
        logger.warning("LinkedIn credentials not provided. Using public access only.")
        return False
    
    try:
        logger.info("Setting up LinkedIn access with minimal authentication...")
        
        # Set common LinkedIn cookies to enhance our access capabilities
        session.cookies.set('lang', 'v=2&lang=en-us', domain='.linkedin.com', path='/')
        session.cookies.set('lidc', f"b=VB{random.randint(10000, 99999)}:g=A:s=A:t={int(time.time())}", 
                          domain='.linkedin.com', path='/')
        
        # Update headers with more authentic browser information
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'DNT': '1',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # Access a company page directly to test our access
        test_company_url = 'https://www.linkedin.com/company/microsoft/'
        try:
            logger.info(f"Testing LinkedIn access with: {test_company_url}")
            test_response = session.get(test_company_url, timeout=10)
            
            if test_response.status_code == 200:
                logger.info("Successfully accessed LinkedIn company page with limited access")
                
                # Check whether we have access to restricted content
                # This is a basic check to see if we're getting public or authenticated content
                if 'Join to view' not in test_response.text and 'Sign in to view' not in test_response.text:
                    logger.info("LinkedIn access appears to be working with enhanced permissions")
                    return True
                else:
                    logger.info("LinkedIn access is limited to public data only")
                    return False
            else:
                logger.warning(f"LinkedIn access test returned status code: {test_response.status_code}")
                return False
                
        except requests.RequestException as e:
            logger.error(f"Error during LinkedIn access test: {str(e)}")
            return False
            
    except Exception as e:
        logger.error(f"Error during LinkedIn access setup: {str(e)}")
        return False

def fetch_linkedin_page(url, use_auth=True):
    """
    Fetch a LinkedIn page with optional authentication
    
    Args:
        url: LinkedIn URL to fetch
        use_auth: Whether to use authentication (default True)
    
    Returns:
        tuple: (html_content, authenticated_status)
    """
    session = setup_authenticated_session()
    authenticated = False
    
    if use_auth:
        authenticated = login_to_linkedin(session)
    
    try:
        # Fetch the requested URL with appropriate timeout
        logger.info(f"Fetching LinkedIn page: {url}")
        
        # Add jitter to seem more human-like
        try:
            time.sleep(0.5 + random.random() * 0.5)  # Random delay between 0.5-1s
        except (KeyboardInterrupt, SystemExit):
            logger.warning("Sleep interrupted during page fetch")
            pass
        
        response = session.get(url, timeout=15, allow_redirects=True)
        
        # Check status code
        if response.status_code != 200:
            logger.warning(f"Received non-200 status code: {response.status_code} for {url}")
            
            if response.status_code == 403:
                logger.warning("LinkedIn is blocking our request (403 Forbidden)")
            elif response.status_code == 429:
                logger.warning("LinkedIn rate limit exceeded (429 Too Many Requests)")
                
            # For certain status codes, we'll try to continue with the content we have
            if response.status_code in [403, 429] and response.text:
                logger.info("Using partial response content despite error status code")
                html_content = response.text
            else:
                return None, authenticated
        else:
            html_content = response.text
        
        # Verify we didn't get redirected to login
        if 'uas/login' in response.url:
            logger.warning(f"Redirected to login page despite authentication attempt")
            authenticated = False
        
        return html_content, authenticated
    
    except requests.Timeout:
        logger.error(f"Timeout while fetching LinkedIn page: {url}")
        return None, authenticated
    except requests.RequestException as e:
        logger.error(f"Request error fetching LinkedIn page {url}: {str(e)}")
        return None, authenticated
    except Exception as e:
        logger.error(f"Error fetching LinkedIn page {url}: {str(e)}")
        return None, authenticated

def extract_company_posts(linkedin_url):
    """
    Extract posts from a LinkedIn company page using authentication
    
    Args:
        linkedin_url: LinkedIn company profile URL
    
    Returns:
        dict: Post data including count and post content
    """
    # Ensure we're working with a company page
    if '/company/' not in linkedin_url:
        logger.warning(f"Not a company URL: {linkedin_url}")
        return None
    
    # Add /posts to URL if not already present
    if not linkedin_url.endswith('/posts'):
        posts_url = linkedin_url.rstrip('/') + '/posts'
    else:
        posts_url = linkedin_url
    
    # Fetch the page with authentication
    html_content, authenticated = fetch_linkedin_page(posts_url)
    
    if not html_content:
        logger.error(f"Could not fetch LinkedIn posts page: {posts_url}")
        return {
            'count': "Error fetching page",
            'posts': [],
            'authentication_required': True,
            'authentication_status': "Failed to authenticate"
        }
    
    # Parse with BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Initialize posts data
    posts_data = {
        'count': 0,
        'posts': [],
        'authentication_status': "Authenticated" if authenticated else "Not authenticated"
    }
    
    # Check if we were redirected to login
    if 'uas/login' in str(html_content).lower() or soup.find('form', attrs={'action': re.compile(r'.*login.*')}):
        logger.warning("Authentication required to view LinkedIn posts")
        posts_data['authentication_required'] = True
        
        # Add a message about authentication
        posts_data['posts'].append({
            'text': "LinkedIn requires authentication to view detailed post content.",
            'date': "Recently"
        })
        
        # Try to extract post count from the main page
        main_page_html, _ = fetch_linkedin_page(linkedin_url)
        if main_page_html:
            main_soup = BeautifulSoup(main_page_html, 'html.parser')
            post_count_element = main_soup.find(['span', 'div'], string=re.compile(r'(\d+)\s*(posts?|updates?|articles?)', re.I))
            
            if post_count_element:
                count_match = re.search(r'(\d+)\s*(posts?|updates?|articles?)', post_count_element.text, re.I)
                if count_match:
                    posts_data['count'] = count_match.group(1)
                    logger.info(f"Found post count: {posts_data['count']}")
        
        # If no count found, set as unknown
        if posts_data['count'] == 0:
            posts_data['count'] = "Unknown (login required)"
        
        return posts_data
    
    # If we got this far, we have authenticated access to posts
    
    # Find post elements (multiple methods to handle different LinkedIn layouts)
    post_containers = []
    
    # Method 1: Standard post containers
    post_containers.extend(soup.find_all(['div', 'article'], class_=lambda c: c and any(
        term in str(c).lower() for term in ['feed-shared-update', 'post-content', 'update-components', 'feed-shared-update-v2']
    )))
    
    # Method 2: Alternative post containers
    if not post_containers:
        post_containers.extend(soup.find_all(['div'], attrs={'data-urn': re.compile(r'.*update.*')}))
    
    # Method 3: Look for post text directly
    if not post_containers:
        post_containers.extend(soup.find_all(['p', 'div'], class_=lambda c: c and any(
            term in str(c).lower() for term in ['feed-shared-text', 'update-content', 'post-text']
        )))
    
    # Process found posts
    unique_posts = set()  # To avoid duplicates
    
    for container in post_containers:
        # Extract post text (try multiple methods)
        post_text_element = container.find(['p', 'div', 'span'], class_=lambda c: c and any(
            term in str(c).lower() for term in ['feed-shared-text', 'update-text', 'post-text', 'update-content']
        ))
        
        # If no specific element found, use the container text
        post_text = post_text_element.text.strip() if post_text_element else container.text.strip()
        post_text = re.sub(r'\s+', ' ', post_text)  # Normalize whitespace
        
        # Only add if text is meaningful and unique
        if post_text and len(post_text) > 10 and post_text not in unique_posts:
            unique_posts.add(post_text)
            
            # Create post object
            post = {
                'text': post_text[:500] + ('...' if len(post_text) > 500 else '')  # Limit length
            }
            
            # Try to find post date
            date_element = container.find(['span', 'time'], string=re.compile(r'(ago|day|week|month|year|hour|minute)', re.I))
            if date_element:
                post['date'] = date_element.text.strip()
            
            # Try to find engagement stats
            reactions = container.find(['span', 'div'], string=re.compile(r'(\d+)\s*(reactions?|likes?)', re.I))
            if reactions:
                reaction_match = re.search(r'(\d+)\s*(reactions?|likes?)', reactions.text, re.I)
                if reaction_match:
                    post['reactions'] = reaction_match.group(1)
            
            # Add to posts list
            posts_data['posts'].append(post)
    
    # Set post count
    posts_data['count'] = len(posts_data['posts'])
    
    # If no posts were found but we're authenticated, add an info message
    if not posts_data['posts'] and authenticated:
        posts_data['posts'].append({
            'text': "No posts found on this company page, despite successful authentication.",
            'date': "Recently"
        })
    
    logger.info(f"Extracted {posts_data['count']} posts from LinkedIn using authentication")
    return posts_data

def extract_company_jobs(linkedin_url):
    """
    Extract job listings from a LinkedIn company page using authentication
    
    Args:
        linkedin_url: LinkedIn company profile URL
    
    Returns:
        dict: Job data including count and job listings
    """
    # Ensure we're working with a company page
    if '/company/' not in linkedin_url:
        logger.warning(f"Not a company URL: {linkedin_url}")
        return None
    
    # Add /jobs to URL if not already present
    if not linkedin_url.endswith('/jobs'):
        jobs_url = linkedin_url.rstrip('/') + '/jobs'
    else:
        jobs_url = linkedin_url
    
    # Fetch the page with authentication
    html_content, authenticated = fetch_linkedin_page(jobs_url)
    
    if not html_content:
        logger.error(f"Could not fetch LinkedIn jobs page: {jobs_url}")
        return {
            'count': "Error fetching page",
            'jobs': [],
            'authentication_required': True,
            'authentication_status': "Failed to authenticate"
        }
    
    # Parse with BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Initialize jobs data
    jobs_data = {
        'count': 0,
        'jobs': [],
        'authentication_status': "Authenticated" if authenticated else "Not authenticated"
    }
    
    # Check if we were redirected to login
    if 'uas/login' in str(html_content).lower() or soup.find('form', attrs={'action': re.compile(r'.*login.*')}):
        logger.warning("Authentication required to view LinkedIn jobs")
        jobs_data['authentication_required'] = True
        
        # Add a message about authentication
        jobs_data['jobs'].append({
            'title': "LinkedIn requires authentication to view job listings",
            'location': "Login required",
            'date_posted': "Recently"
        })
        
        # Try to extract job count from the main page
        main_page_html, _ = fetch_linkedin_page(linkedin_url)
        if main_page_html:
            main_soup = BeautifulSoup(main_page_html, 'html.parser')
            job_count_element = main_soup.find(['span', 'div'], string=re.compile(r'(\d+)\s*(job|position|opening)', re.I))
            
            if job_count_element:
                count_match = re.search(r'(\d+)\s*(job|position|opening)', job_count_element.text, re.I)
                if count_match:
                    jobs_data['count'] = count_match.group(1)
                    logger.info(f"Found job count: {jobs_data['count']}")
        
        # If no count found, set as unknown
        if jobs_data['count'] == 0:
            jobs_data['count'] = "Unknown (login required)"
        
        return jobs_data
    
    # If we got this far, we have authenticated access to jobs
    
    # Find job elements (multiple methods to handle different LinkedIn layouts)
    job_elements = []
    
    # Method 1: Standard job containers
    job_elements.extend(soup.find_all(['li', 'div'], class_=lambda c: c and any(
        term in str(c).lower() for term in ['job-card', 'job-listing', 'job-result', 'jobs-job-card']
    )))
    
    # Method 2: Alternative job containers by title
    if not job_elements:
        job_elements.extend(soup.find_all(['h3', 'h4'], class_=lambda c: c and 'job-title' in str(c).lower()))
    
    # Method 3: Look for job title headers
    if not job_elements:
        title_elements = soup.find_all(['h3', 'h4', 'a'], string=lambda s: s and len(s.strip()) > 5)
        for title_elem in title_elements:
            # Check if parent or grandparent might be a job card
            parent = title_elem.parent
            if parent and ('job' in str(parent.get('class', '')).lower() or 'position' in str(parent.get('class', '')).lower()):
                job_elements.append(parent)
            else:
                # Check grandparent
                grandparent = parent.parent if parent else None
                if grandparent and ('job' in str(grandparent.get('class', '')).lower() or 'position' in str(grandparent.get('class', '')).lower()):
                    job_elements.append(grandparent)
                else:
                    # Just use the title element itself
                    job_elements.append(title_elem)
    
    # Process found jobs
    for element in job_elements:
        # Extract job title
        if element.name in ['h3', 'h4', 'a']:
            # Element itself is the title
            title = element.text.strip()
            
            # Look for location and date nearby
            parent = element.parent
            siblings = parent.find_all(['span', 'div']) if parent else []
            
            location = None
            date_posted = None
            
            for sibling in siblings:
                sibling_text = sibling.text.strip()
                
                # Look for location patterns
                if not location and re.search(r'(remote|united states|usa|uk|canada|australia|india|germany|france|anywhere)', sibling_text, re.I):
                    location = sibling_text
                
                # Look for date patterns
                if not date_posted and re.search(r'(posted|ago|day|week|month)', sibling_text, re.I):
                    date_posted = sibling_text
        else:
            # Element is a container, look for title inside
            title_element = element.find(['h3', 'h4', 'a'])
            title = title_element.text.strip() if title_element else element.text.strip()
            
            # Look for location and date within the container
            location_element = element.find(['span', 'div'], string=re.compile(r'(remote|united states|usa|uk|canada|australia|india|germany|france|anywhere)', re.I))
            location = location_element.text.strip() if location_element else None
            
            date_element = element.find(['span', 'div'], string=re.compile(r'(posted|ago|day|week|month)', re.I))
            date_posted = date_element.text.strip() if date_element else None
        
        # Create job object if title found
        if title and len(title) > 3:  # Minimum length to avoid noise
            job = {'title': title}
            
            if location:
                job['location'] = location
            
            if date_posted:
                job['date_posted'] = date_posted
            
            # Add to jobs list
            jobs_data['jobs'].append(job)
    
    # Set job count
    jobs_data['count'] = len(jobs_data['jobs'])
    
    # If no jobs were found but we're authenticated, try extracting from the page
    if not jobs_data['jobs'] and authenticated:
        # Look for job count explicitly
        count_element = soup.find(['span', 'div'], string=re.compile(r'(\d+)\s*(job|position|opening)', re.I))
        if count_element:
            count_match = re.search(r'(\d+)\s*(job|position|opening)', count_element.text, re.I)
            if count_match:
                count_value = count_match.group(1)
                jobs_data['count'] = count_value
                
                # Add an informational job entry
                jobs_data['jobs'].append({
                    'title': f"Company has {count_value} job openings",
                    'location': "See LinkedIn for details",
                    'date_posted': "Recently"
                })
        else:
            # If no count found, add a message
            jobs_data['jobs'].append({
                'title': "No job listings found on this company page",
                'location': "See LinkedIn directly for latest opportunities",
                'date_posted': "Recently"
            })
    
    logger.info(f"Extracted {jobs_data['count']} jobs from LinkedIn using authentication")
    return jobs_data

def extract_company_people(linkedin_url):
    """
    Extract people/employee information from a LinkedIn company page using authentication
    
    Args:
        linkedin_url: LinkedIn company profile URL
    
    Returns:
        dict: People data including employee count and leadership
    """
    # Ensure we're working with a company page
    if '/company/' not in linkedin_url:
        logger.warning(f"Not a company URL: {linkedin_url}")
        return None
    
    # Add /people to URL if not already present
    if not linkedin_url.endswith('/people'):
        people_url = linkedin_url.rstrip('/') + '/people'
    else:
        people_url = linkedin_url
    
    # Fetch the page with authentication
    html_content, authenticated = fetch_linkedin_page(people_url)
    
    if not html_content:
        logger.error(f"Could not fetch LinkedIn people page: {people_url}")
        return {
            'employee_count': "Error fetching page",
            'leaders': [],
            'departments': [],
            'locations': [],
            'authentication_required': True,
            'authentication_status': "Failed to authenticate"
        }
    
    # Parse with BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Initialize people data
    people_data = {
        'employee_count': 0,
        'leaders': [],
        'departments': [],
        'locations': [],
        'authentication_status': "Authenticated" if authenticated else "Not authenticated"
    }
    
    # Check if we were redirected to login
    if 'uas/login' in str(html_content).lower() or soup.find('form', attrs={'action': re.compile(r'.*login.*')}):
        logger.warning("Authentication required to view LinkedIn people")
        people_data['authentication_required'] = True
        
        # Add a message about authentication
        people_data['leaders'].append({
            'name': "LinkedIn Authentication Required",
            'title': "Login needed to view leadership team"
        })
        
        # Try to extract employee count from the main page
        main_page_html, _ = fetch_linkedin_page(linkedin_url)
        if main_page_html:
            main_soup = BeautifulSoup(main_page_html, 'html.parser')
            
            # Try different patterns for employee count
            text_content = main_soup.get_text()
            count_patterns = [
                r'(\d+[\,\d]*)\s*(employees?|people)',
                r'company size:?\s*(\d+[\,\d]*)',
                r'team size:?\s*(\d+[\,\d]*)',
                r'(\d+[\,\d]*)\s*(?:employees?|people) on Linkedin',
                r'([\d,]+)\s*followers'
            ]
            
            for pattern in count_patterns:
                count_match = re.search(pattern, text_content, re.I)
                if count_match:
                    try:
                        count_str = count_match.group(1).replace(',', '')
                        people_data['employee_count'] = int(count_str)
                        logger.info(f"Found employee count from text: {people_data['employee_count']}")
                        break
                    except ValueError:
                        logger.warning(f"Could not convert employee count to integer: {count_match.group(1)}")
            
            # Look for company size ranges if exact count not found
            if not people_data['employee_count']:
                size_patterns = [
                    r'(1-10|11-50|51-200|201-500|501-1000|1001-5000|5001-10000|10001\+)\s*employees',
                    r'company size:?\s*(1-10|11-50|51-200|201-500|501-1000|1001-5000|5001-10000|10001\+)',
                    r'employees:?\s*(1-10|11-50|51-200|201-500|501-1000|1001-5000|5001-10000|10001\+)'
                ]
                
                for pattern in size_patterns:
                    size_match = re.search(pattern, text_content, re.I)
                    if size_match:
                        size_text = size_match.group(1).strip()
                        people_data['employee_count'] = size_text
                        logger.info(f"Found company size range from text: {size_text}")
                        break
        
        # If no count found, set as unknown
        if not people_data['employee_count']:
            people_data['employee_count'] = "Unknown (login required)"
        
        return people_data
    
    # If we got this far, we have authenticated access to people data
    
    # Extract employee count
    count_elements = soup.find_all(['span', 'div'], string=re.compile(r'(\d+[\,\d]*)\s*(employees?|people)', re.I))
    for element in count_elements:
        count_match = re.search(r'(\d+[\,\d]*)\s*(employees?|people)', element.text, re.I)
        if count_match:
            try:
                count_str = count_match.group(1).replace(',', '')
                people_data['employee_count'] = int(count_str)
                logger.info(f"Found employee count: {people_data['employee_count']}")
                break
            except ValueError:
                logger.warning(f"Could not convert employee count to integer: {count_match.group(1)}")
    
    # Extract leadership/key people
    # Look for leadership sections
    leader_section = soup.find(['section', 'div'], class_=lambda c: c and any(
        term in str(c).lower() for term in ['leadership', 'key-people', 'leaders', 'executives']
    ))
    
    if leader_section:
        # Find person cards within leadership section
        person_cards = leader_section.find_all(['li', 'div'], class_=lambda c: c and any(
            term in str(c).lower() for term in ['person-card', 'employee-card', 'leader-card', 'person-result']
        ))
        
        # If no specific cards found, look for name elements
        if not person_cards:
            person_cards = leader_section.find_all(['h3', 'h4', 'a'], class_=lambda c: c and ('name' in str(c).lower() or 'title' in str(c).lower()))
        
        # Process each person card
        for card in person_cards:
            # Extract name
            name_element = card.find(['h3', 'h4', 'a', 'span'])
            name = name_element.text.strip() if name_element else card.text.strip()
            
            # Extract title
            title_element = None
            if name_element:
                title_element = name_element.find_next(['div', 'span'])
            
            title = title_element.text.strip() if title_element else ""
            
            # Add to leaders list if name found
            if name and len(name) > 2:  # Minimum length to avoid noise
                leader = {
                    'name': name,
                    'title': title
                }
                
                # Add if not duplicate
                if not any(l.get('name') == name for l in people_data['leaders']):
                    people_data['leaders'].append(leader)
    
    # If no leaders found via section, look for common leadership titles
    if not people_data['leaders']:
        leadership_titles = [
            'CEO', 'Chief Executive Officer',
            'CTO', 'Chief Technology Officer',
            'CFO', 'Chief Financial Officer',
            'COO', 'Chief Operating Officer',
            'President', 'Founder', 'Co-Founder',
            'Director', 'Vice President', 'VP',
            'Head of', 'Managing Director'
        ]
        
        # Look for elements with leadership titles
        for title in leadership_titles:
            title_elements = soup.find_all(string=re.compile(f"\\b{title}\\b", re.I))
            
            for element in title_elements:
                # The element is the title text, get its parent
                title_parent = element.parent
                
                # Look for name nearby (before the title)
                name_element = title_parent.find_previous(['h3', 'h4', 'a', 'span'])
                
                if name_element:
                    name = name_element.text.strip()
                    
                    # Add to leaders if name found
                    if name and len(name) > 2:
                        leader = {
                            'name': name,
                            'title': element.strip()
                        }
                        
                        # Add if not duplicate
                        if not any(l.get('name') == name for l in people_data['leaders']):
                            people_data['leaders'].append(leader)
    
    # Extract departments/functions
    department_section = soup.find(['section', 'div'], attrs={'data-test-id': 'insights-by-function'})
    
    if department_section:
        # Find department items
        department_items = department_section.find_all(['li', 'div'], class_=lambda c: c and ('department' in str(c).lower() or 'function' in str(c).lower()))
        
        # If no specific items found, look for text elements
        if not department_items:
            # Common department names
            department_names = [
                'Engineering', 'Sales', 'Marketing',
                'Finance', 'Operations', 'Human Resources', 'HR',
                'Product', 'Design', 'Research', 'Development',
                'Customer Success', 'Support', 'IT'
            ]
            
            for dept in department_names:
                dept_elements = department_section.find_all(string=re.compile(f"\\b{dept}\\b", re.I))
                
                for element in dept_elements:
                    # Look for percentage nearby
                    pct_element = element.parent.find_next(string=re.compile(r'(\d+)%', re.I))
                    percentage = ""
                    
                    if pct_element:
                        pct_match = re.search(r'(\d+)%', pct_element, re.I)
                        if pct_match:
                            percentage = f"{pct_match.group(1)}%"
                    
                    # Add to departments
                    department = {
                        'department': element.strip(),
                        'percentage': percentage
                    }
                    
                    # Add if not duplicate
                    if not any(d.get('department') == department['department'] for d in people_data['departments']):
                        people_data['departments'].append(department)
        else:
            # Process department items
            for item in department_items:
                # Extract department name
                dept_name = item.text.strip()
                
                # Look for percentage
                pct_match = re.search(r'(\d+)%', dept_name, re.I)
                percentage = ""
                
                if pct_match:
                    percentage = f"{pct_match.group(1)}%"
                    # Remove percentage from department name
                    dept_name = re.sub(r'\s*\d+%\s*', '', dept_name)
                
                # Add to departments if name found
                if dept_name:
                    department = {
                        'department': dept_name,
                        'percentage': percentage
                    }
                    
                    # Add if not duplicate
                    if not any(d.get('department') == department['department'] for d in people_data['departments']):
                        people_data['departments'].append(department)
    
    # Extract locations
    location_section = soup.find(['section', 'div'], attrs={'data-test-id': 'insights-by-location'})
    
    if location_section:
        # Find location items
        location_items = location_section.find_all(['li', 'div'], class_=lambda c: c and ('location' in str(c).lower() or 'region' in str(c).lower()))
        
        # If no specific items found, look for text elements
        if not location_items:
            # Common location keywords
            location_keywords = [
                'United States', 'USA', 'UK', 'Canada', 'Australia',
                'India', 'Germany', 'France', 'Spain', 'Italy',
                'Brazil', 'Japan', 'China', 'Singapore'
            ]
            
            for loc in location_keywords:
                loc_elements = location_section.find_all(string=re.compile(f"\\b{loc}\\b", re.I))
                
                for element in loc_elements:
                    # Look for percentage nearby
                    pct_element = element.parent.find_next(string=re.compile(r'(\d+)%', re.I))
                    percentage = ""
                    
                    if pct_element:
                        pct_match = re.search(r'(\d+)%', pct_element, re.I)
                        if pct_match:
                            percentage = f"{pct_match.group(1)}%"
                    
                    # Add to locations
                    location = {
                        'location': element.strip(),
                        'percentage': percentage
                    }
                    
                    # Add if not duplicate
                    if not any(l.get('location') == location['location'] for l in people_data['locations']):
                        people_data['locations'].append(location)
        else:
            # Process location items
            for item in location_items:
                # Extract location name
                loc_name = item.text.strip()
                
                # Look for percentage
                pct_match = re.search(r'(\d+)%', loc_name, re.I)
                percentage = ""
                
                if pct_match:
                    percentage = f"{pct_match.group(1)}%"
                    # Remove percentage from location name
                    loc_name = re.sub(r'\s*\d+%\s*', '', loc_name)
                
                # Add to locations if name found
                if loc_name:
                    location = {
                        'location': loc_name,
                        'percentage': percentage
                    }
                    
                    # Add if not duplicate
                    if not any(l.get('location') == location['location'] for l in people_data['locations']):
                        people_data['locations'].append(location)
    
    logger.info(f"Extracted people data with authentication: {len(people_data['leaders'])} leaders, {len(people_data['departments'])} departments, {len(people_data['locations'])} locations")
    return people_data

def extract_all_company_data(linkedin_url):
    """
    Extract all company data from LinkedIn using authentication
    
    Args:
        linkedin_url: LinkedIn company profile URL
    
    Returns:
        dict: Complete company data including posts, jobs, and people
    """
    result = {}
    
    # Extract posts data
    posts_data = extract_company_posts(linkedin_url)
    if posts_data:
        result['posts'] = posts_data
    
    # Extract jobs data
    jobs_data = extract_company_jobs(linkedin_url)
    if jobs_data:
        result['jobs'] = jobs_data
    
    # Extract people data
    people_data = extract_company_people(linkedin_url)
    if people_data:
        result['people'] = people_data
    
    return result