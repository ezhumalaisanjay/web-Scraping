"""
LinkedIn Enhanced Scraper

This module extends the LinkedIn scraper functionality to extract:
1. Recent posts and their summaries
2. Job openings
3. Company people/employees
"""

import logging
import re
import urllib.request
from urllib.parse import urlparse, urljoin
import trafilatura
from bs4 import BeautifulSoup

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_posts(linkedin_url):
    """
    Extract recent posts from a LinkedIn company page
    
    Args:
        linkedin_url: LinkedIn company profile URL
        
    Returns:
        Dictionary with posts information
    """
    logger.info(f"Extracting posts from: {linkedin_url}")
    
    # Ensure we're using the company URL
    if '/company/' not in linkedin_url:
        logger.warning(f"Not a company URL: {linkedin_url}")
        return None
    
    # Add /posts to URL if not already present
    if not linkedin_url.endswith('/posts'):
        posts_url = linkedin_url.rstrip('/') + '/posts'
    else:
        posts_url = linkedin_url
    
    try:
        # Use trafilatura to get HTML content
        downloaded = trafilatura.fetch_url(posts_url)
        
        # Check for login redirect
        login_redirect = False
        if not downloaded or 'uas/login' in str(downloaded).lower():
            login_redirect = True
            logger.warning(f"LinkedIn requires login to view posts. Using main company page instead: {linkedin_url}")
            # Try using the main company page to at least get some activity info
            downloaded = trafilatura.fetch_url(linkedin_url)
            if not downloaded:
                logger.error(f"Failed to download company page: {linkedin_url}")
                # Return a basic structure with explanation
                return {
                    'count': "Unknown (login required)",
                    'posts': [
                        {
                            'text': "LinkedIn requires login to view detailed post content. The company has posted content, but it's not accessible without authentication.",
                            'date': "Recently"
                        }
                    ],
                    'authentication_required': True
                }
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(downloaded, 'html.parser')
        
        # Find post elements
        posts_data = {
            'count': 0,
            'posts': []
        }
        
        # Look for posts in different potential containers
        post_containers = []
        
        # Method 1: Look for post containers by class names commonly used by LinkedIn
        post_containers.extend(soup.find_all(['div', 'article'], class_=lambda c: c and any(
            term in str(c).lower() for term in ['feed-shared-update', 'post-view', 'update-components', 'feed-item']
        )))
        
        # Method 2: Look for post containers with data attributes
        post_containers.extend(soup.find_all(['div', 'article'], attrs=lambda attrs: attrs and any(
            attr and 'post' in attr.lower() for attr in attrs
        )))
        
        # If no containers found or login required, try finding activity summary info 
        if not post_containers or login_redirect:
            logger.warning(f"No post containers found or login required for: {posts_url}")
            
            # For login-redirected pages, always provide a default post explaining the limitation
            if login_redirect:
                posts_data['authentication_required'] = True
                posts_data['posts'].append({
                    'text': "LinkedIn requires login to view detailed post content. The company has posted content, but it's not accessible without authentication.",
                    'date': "Recently"
                })
            
            # Look for activity indicators on the main page
            activity_indicators = [
                r'(\d+)\s*posts?', 
                r'(\d+)\s*articles?',
                r'(\d+)\s*activit(y|ies)',
                r'posted\s*(\d+)',
                r'shared\s*(\d+)'
            ]
            
            for pattern in activity_indicators:
                count_element = soup.find(['span', 'div'], string=re.compile(pattern, re.I))
                if count_element:
                    count_match = re.search(pattern, count_element.text, re.I)
                    if count_match:
                        count_num = count_match.group(1)
                        posts_data['count'] = count_num
                        logger.info(f"Found post count: {count_num}")
                        
                        # If we have a count but no posts yet, add a sample post
                        if not posts_data['posts']:
                            posts_data['posts'].append({
                                'text': f"This company has approximately {count_num} posts on LinkedIn. Login required to view content.",
                                'date': "Recently"
                            })
                        break
            
            # If still no count found, but login redirected, use "Unknown (login required)"
            if 'count' not in posts_data or not posts_data['count']:
                posts_data['count'] = "Unknown (login required)"
        
        # Process each post container for regular accessible posts
        unique_posts = set()  # To avoid duplicates
        
        for container in post_containers:
            # Extract post text
            post_text_element = container.find(['p', 'div', 'span'], class_=lambda c: c and any(
                term in str(c).lower() for term in ['feed-shared-text', 'update-text', 'post-text']
            ))
            
            if post_text_element and post_text_element.text.strip():
                post_text = post_text_element.text.strip()
                
                # Only add unique posts
                if post_text not in unique_posts:
                    unique_posts.add(post_text)
                    
                    # Create post object
                    post = {
                        'text': post_text[:250] + ('...' if len(post_text) > 250 else '')  # Limit to 250 chars
                    }
                    
                    # Try to find post date
                    date_element = container.find(['span', 'time'], string=re.compile(r'(ago|day|week|month|year|hour)', re.I))
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
        
        # Update final count if not already set and we extracted actual posts
        if (not posts_data.get('count') or posts_data['count'] == 0) and len(posts_data['posts']) > 0:
            posts_data['count'] = len(posts_data['posts'])
        
        logger.info(f"Extracted posts data: count={posts_data.get('count', 0)}, posts={len(posts_data['posts'])}")
        
        return posts_data
    
    except Exception as e:
        logger.error(f"Error extracting posts from {linkedin_url}: {str(e)}")
        # Return a basic structure with error info
        return {
            'count': "Error",
            'posts': [
                {
                    'text': f"Error extracting posts: {str(e)}",
                    'date': "Error"
                }
            ],
            'error': str(e)
        }

def extract_job_openings(linkedin_url):
    """
    Extract job openings from a LinkedIn company page
    
    Args:
        linkedin_url: LinkedIn company profile URL
        
    Returns:
        Dictionary with job openings information
    """
    logger.info(f"Extracting job openings from: {linkedin_url}")
    
    # Ensure we're using the company URL
    if '/company/' not in linkedin_url:
        logger.warning(f"Not a company URL: {linkedin_url}")
        return None
    
    # Add /jobs to URL if not already present
    if not linkedin_url.endswith('/jobs'):
        jobs_url = linkedin_url.rstrip('/') + '/jobs'
    else:
        jobs_url = linkedin_url
    
    try:
        # Use trafilatura to get HTML content
        downloaded = trafilatura.fetch_url(jobs_url)
        
        # Check for login redirect
        login_redirect = False
        if not downloaded or 'uas/login' in str(downloaded).lower():
            # Check if we were redirected to login page
            login_redirect = True
            logger.warning(f"LinkedIn requires login to view jobs. Using main company page instead: {linkedin_url}")
            # Try using the main company page to at least get some job info
            downloaded = trafilatura.fetch_url(linkedin_url)
            if not downloaded:
                logger.error(f"Failed to download company page: {linkedin_url}")
                # Return a basic structure with explanation about authentication
                return {
                    'count': "Unknown (login required)",
                    'jobs': [
                        {
                            'title': "Login Required to View Jobs",
                            'location': "LinkedIn authentication needed",
                            'date_posted': "Unknown"
                        }
                    ],
                    'authentication_required': True
                }
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(downloaded, 'html.parser')
        
        # Initialize jobs data
        jobs_data = {
            'count': 0,
            'jobs': []
        }
        
        # If login redirected, set authentication flag
        if login_redirect:
            jobs_data['authentication_required'] = True
            jobs_data['jobs'].append({
                'title': "Login Required to View Jobs",
                'location': "LinkedIn authentication needed",
                'date_posted': "Unknown"
            })
            
            # Try to extract job count from main page if redirected
            count_elements = soup.find_all(['span', 'div'], string=re.compile(r'(\d+)\s*(?:open\s*)?jobs?', re.I))
            for element in count_elements:
                count_match = re.search(r'(\d+)\s*(?:open\s*)?jobs?', element.text, re.I)
                if count_match:
                    try:
                        jobs_data['count'] = int(count_match.group(1))
                        logger.info(f"Found job count from main page: {jobs_data['count']}")
                        
                        # If we have count but no real jobs (due to login), add a sample job
                        if len(jobs_data['jobs']) <= 1 and jobs_data['count'] > 0:
                            jobs_data['jobs'] = [{
                                'title': f"Company has {jobs_data['count']} job openings",
                                'location': "Login to LinkedIn to view details",
                                'date_posted': "Recently"
                            }]
                        break
                    except ValueError:
                        logger.warning(f"Could not convert job count to integer: {count_match.group(1)}")
        
        # Only proceed with detailed extraction if not login redirected
        if not login_redirect:
            # Method 1: Look for job listings containers
            job_elements = []
            
            # Try to find job cards by common class names
            job_elements.extend(soup.find_all(['li', 'div'], class_=lambda c: c and any(
                term in str(c).lower() for term in ['job-card', 'job-listing', 'job-result', 'jobs-search', 'job-item']
            )))
            
            # If no elements found using class-based approach, try other methods
            if not job_elements:
                # Try to find job title headers
                job_elements = soup.find_all(['h3', 'h4'], string=lambda s: s and len(s.strip()) > 0)
            
            # Extract total job count if available
            count_element = soup.find(['span', 'div'], string=re.compile(r'(\d+)\s*jobs?', re.I))
            if count_element:
                count_match = re.search(r'(\d+)\s*jobs?', count_element.text, re.I)
                if count_match:
                    jobs_data['count'] = int(count_match.group(1))
                    logger.info(f"Found job count: {jobs_data['count']}")
            
            # Process job elements
            for element in job_elements:
                # For each job element, extract the title, location, and posting date if available
                
                # Extract job title
                job_title = element.get_text().strip()
                
                # Create basic job object
                job = {
                    'title': job_title
                }
                
                # Try to find location
                location_element = element.find_next(['span', 'div'], string=re.compile(r'(remote|united states|usa|uk|canada|australia|india|germany|france)', re.I))
                if location_element:
                    job['location'] = location_element.text.strip()
                
                # Try to find posting date
                date_element = element.find_next(['span', 'div'], string=re.compile(r'(posted|ago|day|week|month)', re.I))
                if date_element:
                    job['date_posted'] = date_element.text.strip()
                
                # Add job to list if it has a title
                if job['title'] and len(job['title']) > 3:  # Minimum length to avoid noise
                    jobs_data['jobs'].append(job)
            
            # If we didn't find a count earlier, use the length of discovered jobs
            if jobs_data['count'] == 0:
                jobs_data['count'] = len(jobs_data['jobs'])
        
        # If login required and no count found yet
        if login_redirect and (not jobs_data['count'] or jobs_data['count'] == 0):
            jobs_data['count'] = "Unknown (login required)"
        
        logger.info(f"Extracted {len(jobs_data['jobs'])} job openings from {jobs_url}")
        return jobs_data
    
    except Exception as e:
        logger.error(f"Error extracting job openings from {linkedin_url}: {str(e)}")
        # Return a basic structure with error info
        return {
            'count': "Error",
            'jobs': [
                {
                    'title': f"Error: {str(e)}",
                    'location': "Error retrieving jobs",
                    'date_posted': "Error"
                }
            ],
            'error': str(e)
        }

def extract_people(linkedin_url):
    """
    Extract people (employees, leadership) from a LinkedIn company page
    
    Args:
        linkedin_url: LinkedIn company profile URL
        
    Returns:
        Dictionary with people information
    """
    logger.info(f"Extracting people from: {linkedin_url}")
    
    # Ensure we're using the company URL
    if '/company/' not in linkedin_url:
        logger.warning(f"Not a company URL: {linkedin_url}")
        return None
    
    # Add /people to URL if not already present
    if not linkedin_url.endswith('/people'):
        people_url = linkedin_url.rstrip('/') + '/people'
    else:
        people_url = linkedin_url
    
    try:
        # Use trafilatura to get HTML content
        downloaded = trafilatura.fetch_url(people_url)
        
        # Check for login redirect
        login_redirect = False
        if not downloaded or 'uas/login' in str(downloaded).lower():
            login_redirect = True
            logger.warning(f"LinkedIn requires login to view people. Using main company page instead: {linkedin_url}")
            # Try using the main company page to at least get some employee info
            downloaded = trafilatura.fetch_url(linkedin_url)
            if not downloaded:
                logger.error(f"Failed to download company page: {linkedin_url}")
                # Return a basic structure with explanation
                return {
                    'employee_count': "Unknown (login required)",
                    'leaders': [
                        {
                            'name': "LinkedIn Authentication Required",
                            'title': "Login needed to view leadership team"
                        }
                    ],
                    'locations': [],
                    'departments': [],
                    'authentication_required': True
                }
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(downloaded, 'html.parser')
        
        # Initialize people data
        people_data = {
            'employee_count': 0,
            'leaders': [],
            'locations': [],
            'departments': []
        }
        
        # If login redirected, set authentication flag
        if login_redirect:
            people_data['authentication_required'] = True
            people_data['leaders'].append({
                'name': "LinkedIn Authentication Required",
                'title': "Login needed to view leadership team"
            })
        
        # Try to extract employee count from multiple sources
        count_patterns = [
            r'(\d+[\,\d]*)\s*(employees?|people)',
            r'company size:?\s*(\d+[\,\d]*)',
            r'team size:?\s*(\d+[\,\d]*)',
            r'(\d+[\,\d]*)\s*(?:employees?|people) on Linkedin',
            r'([\d,]+)\s*followers'  # Fallback: follower count can give a rough idea of company size
        ]
        
        # Search for employee count in page text
        text_content = soup.get_text()
        for pattern in count_patterns:
            count_match = re.search(pattern, text_content, re.I)
            if count_match:
                try:
                    # Remove commas and convert to int
                    count_str = count_match.group(1).replace(',', '')
                    people_data['employee_count'] = int(count_str)
                    logger.info(f"Found employee count from text: {people_data['employee_count']}")
                    break
                except ValueError:
                    logger.warning(f"Could not convert employee count to integer: {count_match.group(1)}")
        
        # If the text search didn't yield results, try with element search
        if not people_data['employee_count'] or people_data['employee_count'] == 0:
            for pattern in count_patterns:
                count_element = soup.find(['span', 'div'], string=re.compile(pattern, re.I))
                if count_element:
                    count_match = re.search(pattern, count_element.text, re.I)
                    if count_match:
                        try:
                            # Remove commas and convert to int
                            count_str = count_match.group(1).replace(',', '')
                            people_data['employee_count'] = int(count_str)
                            logger.info(f"Found employee count from element: {people_data['employee_count']}")
                            break
                        except ValueError:
                            logger.warning(f"Could not convert employee count to integer: {count_match.group(1)}")
        
        # Look for alternative employee count indicators if login redirected or no count found
        if (login_redirect or not people_data['employee_count'] or people_data['employee_count'] == 0):
            # Check for company size range text
            size_patterns = [
                r'(1-10|11-50|51-200|201-500|501-1000|1001-5000|5001-10000|10001\+)\s*employees',
                r'company size:?\s*(1-10|11-50|51-200|201-500|501-1000|1001-5000|5001-10000|10001\+)',
                r'employees:?\s*(1-10|11-50|51-200|201-500|501-1000|1001-5000|5001-10000|10001\+)'
            ]
            
            # Try to find size range in full text first
            for pattern in size_patterns:
                size_match = re.search(pattern, text_content, re.I)
                if size_match:
                    size_text = size_match.group(1).strip()
                    people_data['employee_count'] = size_text
                    logger.info(f"Found company size range from text: {size_text}")
                    break
            
            # If still no size, look for elements
            if not people_data['employee_count'] or people_data['employee_count'] == 0:
                # Check for company size text in elements
                for pattern in size_patterns:
                    size_element = soup.find(['div', 'span'], string=re.compile(pattern, re.I))
                    if size_element:
                        size_match = re.search(pattern, size_element.text, re.I)
                        if size_match:
                            size_text = size_match.group(1).strip()
                            people_data['employee_count'] = size_text
                            logger.info(f"Found company size range from element: {size_text}")
                            break
                
                # If still no size found, check for any "company size" section
                size_section = soup.find(['h3', 'h4', 'div'], string=re.compile(r'company size', re.I))
                if size_section:
                    next_elem = size_section.find_next(['p', 'div', 'span'])
                    if next_elem:
                        size_text = next_elem.text.strip()
                        if size_text and len(size_text) < 50:  # Sanity check on length
                            people_data['employee_count'] = size_text
                            logger.info(f"Found company size section text: {size_text}")
        
        # If still no count but login required
        if login_redirect and (not people_data['employee_count'] or people_data['employee_count'] == 0):
            people_data['employee_count'] = "Unknown (login required)"
        
        # Only proceed with detailed extraction if not login redirected
        if not login_redirect:
            # Extract leadership/key people
            # Look for sections that might contain leadership titles
            leader_section = soup.find(['section', 'div'], class_=lambda c: c and any(
                term in str(c).lower() for term in ['leadership', 'key-people', 'company-leaders', 'executives']
            ))
            
            leader_elements = []
            
            if leader_section:
                # Look for name elements within the leadership section
                leader_elements = leader_section.find_all(['h3', 'h4', 'a'], class_=lambda c: c and 'name' in str(c).lower())
            
            # If no specific leadership section found, look for job titles that suggest leadership
            if not leader_elements:
                # Look for job titles that indicate leadership positions
                leader_elements = soup.find_all(['div', 'span'], string=re.compile(r'(CEO|Chief|Director|VP|Head of|President|Founder)', re.I))
            
            # Process leadership elements
            for element in leader_elements:
                # For each leadership element, try to find the person's name and title
                
                name_element = element
                title_element = element.find_next(['div', 'span'], class_=lambda c: c and any(
                    term in str(c).lower() for term in ['title', 'position', 'role']
                ))
                
                # If the element itself is the title, look for the name before it
                if re.search(r'(CEO|Chief|Director|VP|Head of|President|Founder)', element.text, re.I):
                    title_element = element
                    name_element = element.find_previous(['h3', 'h4', 'a', 'div', 'span'], class_=lambda c: c and 'name' in str(c).lower())
                
                # If we have a name element, extract the name and title
                if name_element:
                    name = name_element.text.strip()
                    title = title_element.text.strip() if title_element else ""
                    
                    # Add to leaders list if not already present
                    if name and title:
                        leader = {
                            'name': name,
                            'title': title
                        }
                        
                        # Only add if not duplicate
                        if not any(l.get('name') == name for l in people_data['leaders']):
                            people_data['leaders'].append(leader)
            
            # Extract location information
            location_elements = soup.find_all(['div', 'span'], string=re.compile(r'(united states|usa|uk|canada|australia|india|germany|france)', re.I))
            
            for element in location_elements:
                location = element.text.strip()
                
                # Extract percentage if available
                next_element = element.find_next(['div', 'span'], string=re.compile(r'(\d+[\.\d]*\s*%)', re.I))
                percentage = next_element.text.strip() if next_element else ""
                
                # Add to locations if not already present
                location_item = {
                    'location': location,
                    'percentage': percentage
                }
                
                if not any(l.get('location') == location for l in people_data['locations']):
                    people_data['locations'].append(location_item)
            
            # Extract department information
            department_elements = soup.find_all(['div', 'span'], string=re.compile(r'(engineering|sales|marketing|hr|finance|operations|product|design|research|development)', re.I))
            
            for element in department_elements:
                department = element.text.strip()
                
                # Extract percentage if available
                next_element = element.find_next(['div', 'span'], string=re.compile(r'(\d+[\.\d]*\s*%)', re.I))
                percentage = next_element.text.strip() if next_element else ""
                
                # Add to departments if not already present
                department_item = {
                    'department': department,
                    'percentage': percentage
                }
                
                if not any(d.get('department') == department for d in people_data['departments']):
                    people_data['departments'].append(department_item)
        
        # Log extraction results
        logger.info(f"Extracted people data: {len(people_data['leaders'])} leaders, {len(people_data['locations'])} locations, {len(people_data['departments'])} departments")
        return people_data
    
    except Exception as e:
        logger.error(f"Error extracting people from {linkedin_url}: {str(e)}")
        # Return a basic structure with error info
        return {
            'employee_count': "Error",
            'leaders': [
                {
                    'name': "Error retrieving data",
                    'title': f"Error: {str(e)}"
                }
            ],
            'locations': [],
            'departments': [],
            'error': str(e)
        }

def extract_all_enhanced_data(linkedin_url):
    """
    Extract all enhanced data: posts, jobs, and people
    
    Args:
        linkedin_url: LinkedIn company profile URL
        
    Returns:
        Dictionary with all enhanced data
    """
    enhanced_data = {}
    
    # Extract posts
    posts_data = extract_posts(linkedin_url)
    if posts_data:
        enhanced_data['posts'] = posts_data
    
    # Extract job openings
    jobs_data = extract_job_openings(linkedin_url)
    if jobs_data:
        enhanced_data['jobs'] = jobs_data
    
    # Extract people
    people_data = extract_people(linkedin_url)
    if people_data:
        enhanced_data['people'] = people_data
    
    return enhanced_data