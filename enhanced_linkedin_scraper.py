"""
Enhanced LinkedIn Scraper with Advanced Anti-Detection Features

This module implements advanced techniques to access LinkedIn data while avoiding detection
by LinkedIn's anti-scraping measures.
"""

import logging
import re
import os
import time
import random
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# LinkedIn authentication credentials
LINKEDIN_EMAIL = os.environ.get('LINKEDIN_EMAIL', '')
LINKEDIN_PASSWORD = os.environ.get('LINKEDIN_PASSWORD', '')

# List of popular user agents to rotate through
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:114.0) Gecko/20100101 Firefox/123.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
]

# List of accept languages to rotate through
ACCEPT_LANGUAGES = [
    'en-US,en;q=0.9',
    'en-GB,en;q=0.9',
    'en-CA,en;q=0.9,fr-CA;q=0.8',
    'en;q=0.9',
    'en-US;q=0.9,en;q=0.8'
]

# Common referrers to use
REFERRERS = [
    'https://www.google.com/',
    'https://www.bing.com/',
    'https://www.linkedin.com/',
    'https://www.linkedin.com/feed/',
    'https://www.linkedin.com/in/'
]

# Cache to prevent repeated requests for the same URL
CACHE = {}

# Flag to track if LinkedIn is blocking us
LINKEDIN_BLOCKING = False

def get_random_user_agent():
    """Get a random user agent to avoid detection"""
    return random.choice(USER_AGENTS)

def get_random_accept_language():
    """Get a random accept language to avoid detection"""
    return random.choice(ACCEPT_LANGUAGES)

def get_random_referrer():
    """Get a random referrer to avoid detection"""
    return random.choice(REFERRERS)

def setup_session():
    """
    Set up a session with randomized browser fingerprints
    
    Returns:
        requests.Session: Session with anti-detection headers
    """
    global LINKEDIN_BLOCKING
    
    # Create a session to maintain cookies
    session = requests.Session()
    
    # Set headers to mimic a browser with randomized parameters
    session.headers.update({
        'User-Agent': get_random_user_agent(),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': get_random_accept_language(),
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'DNT': '1',
        'Pragma': 'no-cache'
    })
    
    # Set common LinkedIn cookies to enhance our access capabilities
    year_from_now = int(time.time()) + 365 * 24 * 60 * 60
    session.cookies.set('lang', 'v=2&lang=en-us', domain='.linkedin.com', path='/', expires=year_from_now)
    session.cookies.set('lidc', f"b=VB{random.randint(10000, 99999)}:g=A:s=A:t={int(time.time())}", 
                      domain='.linkedin.com', path='/', expires=year_from_now)
    
    # If LinkedIn started blocking us, add some extra protection
    if LINKEDIN_BLOCKING:
        logger.info("LinkedIn blocking detected - adding extra protection measures")
        
        # Add a Cloudflare bypass cookie
        session.cookies.set('cf_clearance', f"{random.randint(10000000000, 99999999999)}-{int(time.time())}-{random.randint(1, 9)}-0-{random.randint(1000, 9999)}", 
                            domain='.linkedin.com', path='/', expires=year_from_now)
        
        # Add more headers that legitimate browsers would have
        session.headers.update({
            'Referer': get_random_referrer(),
            'Sec-Ch-Ua': '"Google Chrome";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"'
        })
    
    return session

def apply_delay():
    """Apply a random delay between requests to appear human-like"""
    # Shorter delay if LinkedIn is already blocking (don't waste time)
    if LINKEDIN_BLOCKING:
        delay = 0.2 + (random.random() * 0.3)  # 0.2-0.5 seconds
    else:
        delay = 1 + (random.random() * 2)  # 1-3 seconds
    
    try:
        time.sleep(delay)
    except (KeyboardInterrupt, SystemExit):
        logger.warning("Sleep interrupted")
        pass

def fetch_linkedin_page(url, use_auth=True, use_cache=True):
    """
    Fetch a LinkedIn page using all anti-detection techniques
    
    Args:
        url: LinkedIn URL to fetch
        use_auth: Whether to use authentication (not fully implemented)
        use_cache: Whether to use cached responses
        
    Returns:
        tuple: (html_content, authenticated_status)
    """
    global LINKEDIN_BLOCKING, CACHE
    
    # Check if this URL is in the cache
    if use_cache and url in CACHE:
        logger.info(f"Using cached response for: {url}")
        return CACHE[url], False
    
    # Create a new session for each request
    session = setup_session()
    authenticated = False  # Currently always assume unauthenticated
    
    # Add referrer if this is not the first page visit
    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    session.headers.update({
        'Referer': base_url if random.random() > 0.5 else get_random_referrer()
    })
    
    # Apply delay to appear more human-like
    apply_delay()
    
    try:
        # Fetch the requested URL with appropriate timeout
        logger.info(f"Fetching LinkedIn page: {url}")
        
        # Try to fetch the page
        response = session.get(url, timeout=10, allow_redirects=True)
        status_code = response.status_code
        
        # Check for blocking status codes
        if status_code == 999 or status_code == 403:
            # LinkedIn has detected us as a bot
            LINKEDIN_BLOCKING = True
            logger.warning(f"LinkedIn blocking detected! Status code: {status_code}")
            
            # Attempt to fetch through a different method - fetch the Google cached version
            logger.info("Attempting to fetch content through Google cache...")
            
            company_name = parsed_url.path.rstrip('/').split('/')[-1]
            google_cache_url = f"https://webcache.googleusercontent.com/search?q=cache:https://www.linkedin.com/company/{company_name}/"
            
            try:
                # Create a new session with different fingerprint
                cache_session = setup_session()
                cache_session.headers.update({
                    'User-Agent': get_random_user_agent(),  # Use a different user agent
                    'Referer': 'https://www.google.com/search',
                })
                
                cache_response = cache_session.get(google_cache_url, timeout=15)
                
                if cache_response.status_code == 200:
                    logger.info("Successfully retrieved content from Google cache")
                    html_content = cache_response.text
                    
                    # Store in cache
                    if use_cache:
                        CACHE[url] = html_content
                    
                    return html_content, False
            
            except Exception as e:
                logger.error(f"Failed to fetch from Google cache: {str(e)}")
                
            # If we reach here, both direct and cache methods failed
            return None, False
        
        # Handle normal response
        elif status_code == 200:
            html_content = response.text
            
            # Check for login redirects
            if 'uas/login' in response.url:
                logger.warning("Redirected to login page")
                authenticated = False
            
            # Store in cache
            if use_cache:
                CACHE[url] = html_content
            
            return html_content, authenticated
        
        else:
            logger.warning(f"Unexpected status code: {status_code}")
            return None, False
    
    except requests.Timeout:
        logger.error(f"Timeout while fetching LinkedIn page: {url}")
        return None, False
    except requests.RequestException as e:
        logger.error(f"Request error fetching LinkedIn page {url}: {str(e)}")
        return None, False
    except Exception as e:
        logger.error(f"Error fetching LinkedIn page {url}: {str(e)}")
        return None, False

def extract_company_about(linkedin_url):
    """
    Extract company overview and about information
    
    Args:
        linkedin_url: LinkedIn company profile URL
        
    Returns:
        dict: Company about information
    """
    if '/company/' not in linkedin_url:
        logger.warning(f"Not a company URL: {linkedin_url}")
        return None
    
    # Make sure the URL is the main company page
    company_url = re.sub(r'/(?:about|people|jobs|posts)/?.*$', '', linkedin_url)
    company_url = company_url.rstrip('/')
    if not company_url.endswith('/about'):
        company_url += '/about'
    
    # Fetch the page with anti-detection measures
    html_content, _ = fetch_linkedin_page(company_url)
    
    if not html_content:
        logger.error(f"Could not fetch LinkedIn company page: {company_url}")
        return {
            'name': "Unknown",
            'overview': "Could not access LinkedIn company page due to access restrictions.",
            'website': "",
            'industry': "",
            'company_size': "",
            'headquarters': "",
            'founded': "",
            'specialties': []
        }
    
    # Parse with BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Extract basic company information
    company_data = {
        'name': "Unknown",
        'overview': "",
        'website': "",
        'industry': "",
        'company_size': "",
        'headquarters': "",
        'founded': "",
        'specialties': []
    }
    
    # Try to extract company name (multiple methods)
    name_elements = [
        soup.find('h1', class_=lambda c: c and ('org-top-card-summary__title' in c or 'organization-about-top-card__title' in c)),
        soup.find('span', class_=lambda c: c and ('org-top-card-summary__title' in c or 'organization-about-top-card__title' in c)),
        soup.find('title')
    ]
    
    for elem in name_elements:
        if elem and elem.text.strip():
            # Clean up the name
            name = elem.text.strip()
            # If it's from the title, extract just the company name
            if elem.name == 'title':
                name = re.sub(r'\s*\|.*$', '', name)
                name = re.sub(r'\s*LinkedIn.*$', '', name)
            company_data['name'] = name
            break
    
    # Extract overview (multiple methods)
    overview_elements = [
        soup.find(['div', 'p'], class_=lambda c: c and ('org-about-us-organization-description__text' in c or 'organization-about__description' in c)),
        soup.find(['div', 'p'], class_=lambda c: c and ('about-us' in c and 'description' in c)),
        soup.find(['div', 'p'], class_=lambda c: c and ('overview' in c))
    ]
    
    for elem in overview_elements:
        if elem and elem.text.strip():
            company_data['overview'] = elem.text.strip()
            break
    
    # Try to extract from meta description if no overview found
    if not company_data['overview']:
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and 'content' in meta_desc.attrs:
            company_data['overview'] = meta_desc['content'].strip()
    
    # Extract other details from about section
    detail_terms = {
        'website': ['website', 'site', 'homepage'],
        'industry': ['industry', 'sector'],
        'company_size': ['company size', 'employees', 'organization size'],
        'headquarters': ['headquarters', 'location', 'address'],
        'founded': ['founded', 'established'],
        'specialties': ['specialties', 'specialisms', 'expertise']
    }
    
    # Find all definition lists or similar structures
    dt_elements = soup.find_all(['dt', 'h3'])
    for dt in dt_elements:
        dt_text = dt.text.strip().lower()
        
        # Find corresponding description or value
        dd = dt.find_next(['dd', 'p'])
        if dd:
            dd_text = dd.text.strip()
            
            # Match to our fields
            for field, terms in detail_terms.items():
                if any(term in dt_text for term in terms):
                    if field == 'specialties':
                        # Split specialties into a list
                        specialties = [s.strip() for s in dd_text.split(',')]
                        company_data[field] = specialties
                    else:
                        company_data[field] = dd_text
                    break
    
    # If we still couldn't find data, try generic patterns
    if not any(company_data.values()):
        # Look for structured sections
        sections = soup.find_all(['section', 'div'], class_=lambda c: c and ('section' in str(c) or 'block' in str(c)))
        for section in sections:
            # Try to identify what section this is by its headers or class names
            section_text = section.text.lower()
            section_class = str(section.get('class', '')).lower()
            
            # Check what kind of section this might be
            for field, terms in detail_terms.items():
                if any(term in section_text for term in terms) or any(term in section_class for term in terms):
                    # Extract the content
                    p_tags = section.find_all(['p', 'span'])
                    for p in p_tags:
                        if len(p.text.strip()) > 5 and not any(term in p.text.lower() for term in sum(detail_terms.values(), [])):
                            if field == 'specialties':
                                specialties = [s.strip() for s in p.text.split(',')]
                                company_data[field] = specialties
                            else:
                                company_data[field] = p.text.strip()
                            break
    
    # If we have no overview but have other data, create a simple overview
    if not company_data['overview'] and (company_data['industry'] or company_data['company_size']):
        overview_parts = []
        if company_data['name'] != "Unknown":
            overview_parts.append(f"{company_data['name']} is a company")
        if company_data['industry']:
            overview_parts.append(f"in the {company_data['industry']} industry")
        if company_data['headquarters']:
            overview_parts.append(f"based in {company_data['headquarters']}")
        if company_data['founded']:
            overview_parts.append(f"founded in {company_data['founded']}")
        if company_data['company_size']:
            overview_parts.append(f"with approximately {company_data['company_size']} employees")
        
        if overview_parts:
            company_data['overview'] = ' '.join(overview_parts) + '.'
    
    logger.info(f"Extracted LinkedIn company about data: {company_data['name']}")
    return company_data
    
def extract_company_posts(linkedin_url):
    """
    Extract recent posts from a LinkedIn company page
    
    Args:
        linkedin_url: LinkedIn company profile URL
        
    Returns:
        dict: Post data including count and post content
    """
    if '/company/' not in linkedin_url:
        logger.warning(f"Not a company URL: {linkedin_url}")
        return None
    
    # Make sure the URL is the posts page
    posts_url = re.sub(r'/(?:about|people|jobs)/?.*$', '', linkedin_url)
    posts_url = posts_url.rstrip('/')
    if not posts_url.endswith('/posts'):
        posts_url += '/posts'
    
    # Fetch the page
    html_content, authenticated = fetch_linkedin_page(posts_url)
    
    # Initialize posts data
    posts_data = {
        'count': 0,
        'posts': [],
        'authentication_status': "LinkedIn's anti-scraping measures are active"
    }
    
    if not html_content:
        logger.error(f"Could not fetch LinkedIn posts page: {posts_url}")
        posts_data['posts'].append({
            'text': "LinkedIn's anti-scraping protection prevented post data collection.",
            'date': "Recently"
        })
        return posts_data
    
    # Try to parse with BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Check if we were redirected to login
    if 'uas/login' in str(html_content).lower() or soup.find('form', attrs={'action': re.compile(r'.*login.*')}):
        logger.warning("Authentication required to view LinkedIn posts")
        posts_data['posts'].append({
            'text': "LinkedIn requires authentication to view detailed post content.",
            'date': "Recently"
        })
        
        return posts_data
    
    # Find post elements (multiple methods to handle different LinkedIn layouts)
    post_containers = []
    
    # Method 1: Look for update feed posts
    post_containers.extend(soup.find_all(['div', 'article'], attrs={
        'class': lambda c: c and any(term in str(c).lower() for term in [
            'feed-shared-update', 'post-content', 'update-components', 'feed-shared-update-v2'
        ])
    }))
    
    # Method 2: Look for update content
    if not post_containers:
        post_containers.extend(soup.find_all(['div'], attrs={'data-urn': re.compile(r'.*update.*')}))
    
    # Method 3: Look for post text elements
    if not post_containers:
        post_containers.extend(soup.find_all(['p', 'div'], attrs={
            'class': lambda c: c and any(term in str(c).lower() for term in [
                'feed-shared-text', 'update-content', 'post-text'
            ])
        }))
    
    # Process found posts
    unique_posts = set()  # To avoid duplicates
    
    for container in post_containers:
        # Extract post text (try multiple methods)
        post_text_element = container.find(['p', 'div', 'span'], attrs={
            'class': lambda c: c and any(term in str(c).lower() for term in [
                'feed-shared-text', 'update-text', 'post-text', 'update-content'
            ])
        })
        
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
    
    # If we found no posts but have content
    if not posts_data['posts'] and html_content:
        # Check if the page indicates no posts
        no_posts_phrases = ['No posts yet', 'No updates', 'share their first']
        page_text = soup.text.lower()
        
        if any(phrase.lower() in page_text for phrase in no_posts_phrases):
            posts_data['posts'].append({
                'text': "This company has no posts on LinkedIn yet.",
                'date': "N/A"
            })
        else:
            posts_data['posts'].append({
                'text': "Unable to extract posts due to LinkedIn's page structure.",
                'date': "Recently"
            })
    
    # Set post count
    posts_data['count'] = len(posts_data['posts'])
    
    logger.info(f"Extracted {posts_data['count']} posts from LinkedIn")
    return posts_data

def extract_company_jobs(linkedin_url):
    """
    Extract job listings from a LinkedIn company page
    
    Args:
        linkedin_url: LinkedIn company profile URL
        
    Returns:
        dict: Jobs data including count and job listings
    """
    if '/company/' not in linkedin_url:
        logger.warning(f"Not a company URL: {linkedin_url}")
        return None
    
    # Make sure the URL is the jobs page
    jobs_url = re.sub(r'/(?:about|people|posts)/?.*$', '', linkedin_url)
    jobs_url = jobs_url.rstrip('/')
    if not jobs_url.endswith('/jobs'):
        jobs_url += '/jobs'
    
    # Fetch the page
    html_content, authenticated = fetch_linkedin_page(jobs_url)
    
    # Initialize jobs data
    jobs_data = {
        'count': 0,
        'jobs': [],
        'authentication_status': "LinkedIn's anti-scraping measures are active"
    }
    
    if not html_content:
        logger.error(f"Could not fetch LinkedIn jobs page: {jobs_url}")
        jobs_data['jobs'].append({
            'title': "LinkedIn's anti-scraping protection prevented job data collection.",
            'location': "Unknown",
            'date_posted': "Recently"
        })
        return jobs_data
    
    # Try to parse with BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Check if we were redirected to login
    if 'uas/login' in str(html_content).lower() or soup.find('form', attrs={'action': re.compile(r'.*login.*')}):
        logger.warning("Authentication required to view LinkedIn jobs")
        jobs_data['jobs'].append({
            'title': "LinkedIn requires authentication to view job listings",
            'location': "Login required",
            'date_posted': "Recently"
        })
        
        return jobs_data
    
    # Find job elements (multiple methods to handle different LinkedIn layouts)
    job_elements = []
    
    # Method 1: Standard job containers
    job_elements.extend(soup.find_all(['li', 'div'], attrs={
        'class': lambda c: c and any(term in str(c).lower() for term in [
            'job-card', 'job-listing', 'job-result', 'jobs-job-card'
        ])
    }))
    
    # Method 2: Look for job titles
    if not job_elements:
        job_elements.extend(soup.find_all(['h3', 'h4'], attrs={
            'class': lambda c: c and 'job-title' in str(c).lower()
        }))
    
    # Method 3: Look for job cards more generically
    if not job_elements:
        job_containers = soup.find_all(['li', 'div', 'section'], attrs={
            'class': lambda c: c and ('card' in str(c).lower() or 'item' in str(c).lower())
        })
        
        for container in job_containers:
            # Check if this might be a job listing
            text = container.text.lower()
            if ('job' in text or 'position' in text or 'hiring' in text) and ('apply' in text or 'location' in text):
                job_elements.append(container)
    
    # Process found jobs
    for job_elem in job_elements:
        job = {
            'title': '',
            'location': '',
            'date_posted': ''
        }
        
        # Extract job title
        title_elem = job_elem.find(['h3', 'h4', 'a', 'span'], attrs={
            'class': lambda c: c and any(term in str(c).lower() for term in [
                'job-title', 'title', 'position-title'
            ])
        })
        
        if title_elem:
            job['title'] = title_elem.text.strip()
        
        # If no specific title element found, try to infer
        if not job['title']:
            # Look for the most prominent heading
            heading = job_elem.find(['h3', 'h4', 'h5', 'strong'])
            if heading:
                job['title'] = heading.text.strip()
        
        # Only continue if we have a title
        if job['title']:
            # Extract location
            location_elem = job_elem.find(['span', 'div'], string=re.compile(r'(remote|\w+,\s*\w+|location)', re.I))
            if location_elem:
                job['location'] = location_elem.text.strip()
            
            # Extract posting date
            date_elem = job_elem.find(['span', 'div', 'time'], string=re.compile(r'(ago|day|week|month|posted)', re.I))
            if date_elem:
                job['date_posted'] = date_elem.text.strip()
            
            # Add to jobs list
            jobs_data['jobs'].append(job)
    
    # If we found no jobs but have content
    if not jobs_data['jobs'] and html_content:
        # Check if the page indicates no jobs
        no_jobs_phrases = ['No jobs', 'No open positions', 'No current job']
        page_text = soup.text.lower()
        
        if any(phrase.lower() in page_text for phrase in no_jobs_phrases):
            jobs_data['jobs'].append({
                'title': "This company has no job openings on LinkedIn at this time.",
                'location': "N/A",
                'date_posted': "N/A"
            })
        else:
            jobs_data['jobs'].append({
                'title': "Unable to extract job listings due to LinkedIn's page structure.",
                'location': "Unknown",
                'date_posted': "Recently"
            })
    
    # Set job count
    jobs_data['count'] = len(jobs_data['jobs'])
    
    logger.info(f"Extracted {jobs_data['count']} jobs from LinkedIn")
    return jobs_data

def extract_company_people(linkedin_url):
    """
    Extract people information from a LinkedIn company page
    
    Args:
        linkedin_url: LinkedIn company profile URL
        
    Returns:
        dict: People data including count and profiles
    """
    if '/company/' not in linkedin_url:
        logger.warning(f"Not a company URL: {linkedin_url}")
        return None
    
    # Make sure the URL is the people page
    people_url = re.sub(r'/(?:about|jobs|posts)/?.*$', '', linkedin_url)
    people_url = people_url.rstrip('/')
    if not people_url.endswith('/people'):
        people_url += '/people'
    
    # Fetch the page
    html_content, authenticated = fetch_linkedin_page(people_url)
    
    # Initialize people data
    people_data = {
        'employee_count': 'Unknown',
        'leadership': [],
        'employees': [],
        'authentication_status': "LinkedIn's anti-scraping measures are active"
    }
    
    if not html_content:
        logger.error(f"Could not fetch LinkedIn people page: {people_url}")
        return people_data
    
    # Try to parse with BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Check if we were redirected to login
    if 'uas/login' in str(html_content).lower() or soup.find('form', attrs={'action': re.compile(r'.*login.*')}):
        logger.warning("Authentication required to view LinkedIn people")
        
        # Try to extract employee count from the main company page
        main_url = re.sub(r'/(?:about|people|jobs|posts)/?.*$', '', linkedin_url)
        main_html, _ = fetch_linkedin_page(main_url)
        
        if main_html:
            main_soup = BeautifulSoup(main_html, 'html.parser')
            
            # Look for employee count
            count_elem = main_soup.find(['span', 'div'], string=re.compile(r'(\d+)\s*(employees?|staff|people|professionals)', re.I))
            if count_elem:
                count_match = re.search(r'(\d+[\d,]*)\s*(employees?|staff|people|professionals)', count_elem.text, re.I)
                if count_match:
                    people_data['employee_count'] = count_match.group(1)
                    logger.info(f"Found employee count: {people_data['employee_count']}")
        
        return people_data
    
    # Extract employee count
    count_elem = soup.find(['span', 'div'], string=re.compile(r'(\d+)\s*(employees?|staff|people|professionals)', re.I))
    if count_elem:
        count_match = re.search(r'(\d+[\d,]*)\s*(employees?|staff|people|professionals)', count_elem.text, re.I)
        if count_match:
            people_data['employee_count'] = count_match.group(1)
    
    # Find people elements
    people_elements = soup.find_all(['li', 'div'], attrs={
        'class': lambda c: c and any(term in str(c).lower() for term in [
            'person-card', 'profile-card', 'employee-card', 'people-card'
        ])
    })
    
    # If not found, try another approach
    if not people_elements:
        people_sections = soup.find_all(['section', 'div'], attrs={
            'class': lambda c: c and any(term in str(c).lower() for term in [
                'leadership', 'employees', 'people', 'staff'
            ])
        })
        
        for section in people_sections:
            cards = section.find_all(['li', 'div'], attrs={
                'class': lambda c: c and ('card' in str(c).lower() or 'item' in str(c).lower())
            })
            people_elements.extend(cards)
    
    # Process found people
    for person_elem in people_elements:
        person = {
            'name': '',
            'title': '',
            'is_leadership': False
        }
        
        # Extract name
        name_elem = person_elem.find(['h3', 'h4', 'a', 'span'], attrs={
            'class': lambda c: c and any(term in str(c).lower() for term in [
                'person-name', 'name', 'profile-name'
            ])
        })
        
        if name_elem:
            person['name'] = name_elem.text.strip()
        
        # If no specific name element found, try to infer
        if not person['name']:
            # Look for the most prominent heading
            heading = person_elem.find(['h3', 'h4', 'h5', 'strong'])
            if heading:
                person['name'] = heading.text.strip()
        
        # Only continue if we have a name
        if person['name']:
            # Extract title
            title_elem = person_elem.find(['span', 'div', 'p'], attrs={
                'class': lambda c: c and any(term in str(c).lower() for term in [
                    'person-title', 'title', 'position', 'role'
                ])
            })
            
            if title_elem:
                person['title'] = title_elem.text.strip()
            
            # Extract title using generic approach if not found
            if not person['title']:
                # Find first paragraph or span after name
                sibling = name_elem.find_next(['p', 'span', 'div']) if name_elem else None
                if sibling:
                    person['title'] = sibling.text.strip()
            
            # Check if this is a leadership position
            person_text = person_elem.text.lower()
            leadership_terms = ['ceo', 'cto', 'cfo', 'chief', 'director', 'vp', 'vice president', 
                               'head of', 'president', 'founder', 'co-founder', 'owner', 'partner']
            
            if person['title'] and any(term in person['title'].lower() for term in leadership_terms):
                person['is_leadership'] = True
            elif any(term in person_text for term in leadership_terms):
                person['is_leadership'] = True
            
            # Add to appropriate list
            if person['is_leadership']:
                people_data['leadership'].append(person)
            else:
                people_data['employees'].append(person)
    
    logger.info(f"Extracted {len(people_data['leadership'])} leadership and {len(people_data['employees'])} employees from LinkedIn")
    return people_data

def extract_all_company_data(linkedin_url):
    """
    Extract all company data from LinkedIn
    
    Args:
        linkedin_url: LinkedIn company profile URL
        
    Returns:
        dict: Complete company data including about, posts, jobs, and people
    """
    # Normalize URL format
    if not linkedin_url.startswith(('http://', 'https://')):
        linkedin_url = 'https://' + linkedin_url
    
    if 'linkedin.com' not in linkedin_url:
        logger.warning(f"Not a LinkedIn URL: {linkedin_url}")
        return {
            'error': 'Not a valid LinkedIn company URL'
        }
    
    # Make sure this is a company page
    if '/company/' not in linkedin_url:
        if '/in/' in linkedin_url or '/pub/' in linkedin_url:
            logger.warning(f"This is a LinkedIn personal profile, not a company page: {linkedin_url}")
            return {
                'error': 'This is a LinkedIn personal profile, not a company page'
            }
        # Try to detect if it might be a company page with a different format
        company_matches = re.search(r'linkedin\.com/(?:school|organization|school)/([^/]+)', linkedin_url)
        if company_matches:
            # Convert to company format
            company_id = company_matches.group(1)
            linkedin_url = f"https://www.linkedin.com/company/{company_id}/"
            logger.info(f"Converted to company URL format: {linkedin_url}")
        else:
            logger.warning(f"Not a recognized LinkedIn company URL format: {linkedin_url}")
            return {
                'error': 'Not a valid LinkedIn company URL format'
            }
    
    # Ensure URL is standardized
    linkedin_url = re.sub(r'(/company/[^/]+).*$', r'\1/', linkedin_url)
    
    # Extract different types of data
    about_data = extract_company_about(linkedin_url)
    posts_data = extract_company_posts(linkedin_url)
    jobs_data = extract_company_jobs(linkedin_url)
    people_data = extract_company_people(linkedin_url)
    
    # Combine all data
    company_data = {
        'company_url': linkedin_url,
        'about': about_data,
        'posts': posts_data,
        'jobs': jobs_data,
        'people': people_data
    }
    
    logger.info(f"Completed full extraction for: {linkedin_url}")
    return company_data