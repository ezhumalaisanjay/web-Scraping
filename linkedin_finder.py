import logging
import re
import urllib.request
from urllib.parse import urlparse, urljoin
import trafilatura
from bs4 import BeautifulSoup

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_linkedin_url(url):
    """
    Extract LinkedIn company URL from a website.
    Returns the LinkedIn URL if found, None otherwise.
    """
    try:
        # Parse domain for later use
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        
        logger.info(f"Searching for LinkedIn URL on: {url}")
        
        # Use trafilatura to get the HTML content
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            logger.error(f"Failed to download URL: {url}")
            return None
        
        # Parse with BeautifulSoup for better tag access
        soup = BeautifulSoup(downloaded, 'html.parser')
        
        # Method 1: Look for direct LinkedIn links in social media sections
        linkedin_urls = []
        
        # Look for links containing 'linkedin.com'
        linkedin_links = soup.find_all('a', href=lambda href: href and 'linkedin.com' in href.lower())
        for link in linkedin_links:
            href = link.get('href')
            if href:
                # Clean the URL to get only the company path
                if 'linkedin.com/company/' in href.lower():
                    linkedin_urls.append(href)
                    logger.info(f"Found LinkedIn company link: {href}")
        
        # Method 2: Look for common social media sections
        social_sections = soup.find_all(['div', 'ul', 'section'], class_=lambda c: c and any(
            term in str(c).lower() for term in ['social', 'connect', 'follow', 'links', 'footer', 'contact']
        ))
        
        for section in social_sections:
            links = section.find_all('a', href=lambda href: href and 'linkedin.com' in href.lower())
            for link in links:
                href = link.get('href')
                if href:
                    linkedin_urls.append(href)
                    logger.info(f"Found LinkedIn link in social section: {href}")
        
        # Method 3: Check for meta tags with LinkedIn URLs
        meta_linkedin = soup.find('meta', property='og:linkedin')
        if meta_linkedin and meta_linkedin.get('content'):
            linkedin_urls.append(meta_linkedin.get('content'))
            logger.info(f"Found LinkedIn URL in meta tag: {meta_linkedin.get('content')}")
        
        # Method 4: Look for schema.org social media profiles
        script_tags = soup.find_all('script', type='application/ld+json')
        for script in script_tags:
            if script.string:
                # Look for LinkedIn URLs in JSON-LD
                linkedin_matches = re.findall(r'https?://(?:www\.)?linkedin\.com/(?:company|school)/[^"\'\s]+', script.string)
                linkedin_urls.extend(linkedin_matches)
        
        # Filter LinkedIn company URLs and remove duplicates
        filtered_urls = []
        seen_urls = set()
        
        for url in linkedin_urls:
            # Normalize the URL
            if url.endswith('/'):
                url = url[:-1]
            
            # Only include company URLs and skip duplicates
            if 'linkedin.com/company/' in url.lower() and url not in seen_urls:
                filtered_urls.append(url)
                seen_urls.add(url)
        
        if filtered_urls:
            return filtered_urls[0]  # Return the first LinkedIn company URL found
        
        # If no specific company URL found, look for any LinkedIn link as fallback
        if linkedin_urls:
            return linkedin_urls[0]
            
        logger.warning(f"No LinkedIn URL found on: {url}")
        return None
        
    except Exception as e:
        logger.error(f"Error extracting LinkedIn URL: {str(e)}")
        return None

def find_and_extract_linkedin_about(website_url):
    """
    Main function to find LinkedIn URL from a website and extract the company about section.
    
    Args:
        website_url: The company's main website URL
        
    Returns:
        Dictionary with LinkedIn URL and the extracted company data
    """
    from scraper import scrape_website  # Import here to avoid circular imports
    
    # Step 1: Find LinkedIn URL from the website
    linkedin_url = extract_linkedin_url(website_url)
    
    if not linkedin_url:
        return {
            "success": False,
            "website_url": website_url,
            "linkedin_url": None,
            "message": "No LinkedIn URL found on the website"
        }
    
    # Step 2: Extract company info from LinkedIn
    company_data = scrape_website(linkedin_url)
    
    if not company_data:
        return {
            "success": False,
            "website_url": website_url,
            "linkedin_url": linkedin_url,
            "message": "Failed to extract company data from LinkedIn"
        }
    
    return {
        "success": True,
        "website_url": website_url,
        "linkedin_url": linkedin_url,
        "company_data": company_data
    }

if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) > 1:
        website_url = sys.argv[1]
    else:
        website_url = input("Enter company website URL: ")
        
    result = find_and_extract_linkedin_about(website_url)
    
    if result["success"]:
        print(f"Successfully found LinkedIn profile: {result['linkedin_url']}")
        
        company_data = result["company_data"]
        linkedin_data = company_data.get("linkedin_data", {})
        
        print("\nCompany Details:")
        print(f"Name: {company_data.get('company_name', 'N/A')}")
        
        if "overview" in linkedin_data:
            print("\nAbout/Overview:")
            print(linkedin_data["overview"])
        
        if "founded" in linkedin_data:
            print(f"\nFounded: {linkedin_data['founded']}")
        
        if "business_categories" in linkedin_data:
            print("\nBusiness Categories:")
            for category in linkedin_data["business_categories"]:
                print(f"- {category}")
        
        if "specialties" in linkedin_data:
            print("\nSpecialties:")
            for specialty in linkedin_data["specialties"]:
                print(f"- {specialty}")
        
        if "milestones" in linkedin_data:
            print("\nMilestones:")
            for milestone in linkedin_data["milestones"]:
                print(f"- {milestone}")
    else:
        print(f"Error: {result['message']}")