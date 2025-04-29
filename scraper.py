import re
import urllib.request
import logging
import trafilatura
from bs4 import BeautifulSoup
import json
from urllib.parse import urlparse
from html.parser import HTMLParser
from linkedin_enhanced_scraper import extract_all_enhanced_data

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Custom HTML Parser class based on the uploaded file
class MyHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.paragraphs = []
        self.contact_info = []
        self.services = []
        self.products = []
        self.company_name = None
        self.capture = False
        self.headings = []  # Store heading data to analyze better
        self.current_tag = None  # Track the current tag being processed

    def handle_starttag(self, tag, attrs):
        self.current_tag = tag  # Track the current tag
        if tag == 'p' or tag == 'a':
            self.capture = True
        elif tag == 'h1' or tag == 'h2' or tag == 'h3':
            self.capture = True  # Capture text in headers (for potential company name)

    def handle_endtag(self, tag):
        if tag == 'p' or tag == 'a' or tag == 'h1' or tag == 'h2' or tag == 'h3':
            self.capture = False
        self.current_tag = None  # Reset current tag when ending a tag

    def handle_data(self, data):
        if self.capture:
            text = data.strip()
            if self.current_tag in ['h1', 'h2', 'h3']:
                self.headings.append(text)
            # Check for company name: First heading tag or the title of the page
            if not self.company_name and self.headings:
                self.company_name = self.headings[0]  # Select the first heading as the company name
            # Check for contact info (email, phone, address)
            elif re.search(r'[\w\.-]+@[\w\.-]+', text):
                self.contact_info.append(text)
            elif re.search(r'\+?\d{1,4}?[-.\s]?\(?\d{1,3}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,4}', text):
                self.contact_info.append(text)
            elif re.search(r'\d{1,4}[\w\s]+[,\-.\d]*\s*(Street|Ave|Road|Boulevard|Lane)', text):
                self.contact_info.append(text)
            elif 'service' in text.lower():
                self.services.append(text)
            elif 'product' in text.lower() or 'offer' in text.lower():
                self.products.append(text)
            else:
                self.paragraphs.append(text)

# Regular expressions for data extraction
EMAIL_PATTERN = r'[\w\.-]+@[\w\.-]+\.\w+'
PHONE_PATTERN = r'(?:\+\d{1,3}[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}'
ADDRESS_PATTERN = r'\d+\s+(?:[A-Za-z0-9.-]+\s+){1,5}(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Plaza|Plz|Square|Sq)'
SOCIAL_MEDIA_PATTERNS = {
    'facebook': r'facebook\.com/[\w.-]+',
    'twitter': r'twitter\.com/[\w.-]+',
    'linkedin': r'linkedin\.com/(?:company|in|school)/[\w.-]+',
    'instagram': r'instagram\.com/[\w.-]+',
}

def extract_emails(text):
    """Extract email addresses from text"""
    emails = re.findall(EMAIL_PATTERN, text)
    return list(set(emails))  # Remove duplicates

def extract_phones(text):
    """Extract phone numbers from text"""
    phones = re.findall(PHONE_PATTERN, text)
    return list(set(phones))  # Remove duplicates

def extract_addresses(text):
    """Extract physical addresses from text"""
    addresses = re.findall(ADDRESS_PATTERN, text, re.IGNORECASE)
    return list(set(addresses))  # Remove duplicates

def extract_social_media(text):
    """Extract social media links from text"""
    social_media = {}
    for platform, pattern in SOCIAL_MEDIA_PATTERNS.items():
        matches = re.findall(pattern, text)
        if matches:
            social_media[platform] = list(set(matches))
    return social_media

def clean_text(text):
    """Clean text by removing extra whitespace and normalizing newlines"""
    if not text:
        return ""
    # Replace multiple whitespace with a single space
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_company_name(soup, domain_name):
    """Extract company name using multiple methods"""
    # Method 1: Look for title tag
    title = soup.title.string if soup.title else None
    
    # Method 2: Look for logo alt text
    logo = soup.find('img', alt=re.compile(r'logo', re.I))
    logo_alt = logo.get('alt') if logo else None
    
    # Method 3: Look for heading in header
    header = soup.find('header')
    header_heading = None
    if header:
        heading = header.find(['h1', 'h2'])
        header_heading = heading.text.strip() if heading else None
    
    # Method 4: First h1 on the page
    first_h1 = soup.find('h1')
    first_h1_text = first_h1.text.strip() if first_h1 else None
    
    # Method 5: Use the domain name
    domain_parts = domain_name.split('.')
    domain_company = domain_parts[0].title() if domain_parts else None
    
    # Select the best company name
    candidates = [
        name for name in [header_heading, first_h1_text, logo_alt, title, domain_company]
        if name and len(name) < 100
    ]
    
    if candidates:
        # Choose the shortest name as it's likely most accurate
        return min(candidates, key=len)
    return domain_company or "Unknown Company"

def extract_services_products(text, company_name):
    """Extract services and products from text"""
    # Look for sections about services or products
    services = []
    products = []
    
    # Split text into paragraphs
    paragraphs = re.split(r'\n+', text)
    
    for para in paragraphs:
        para = clean_text(para)
        
        # Services often contain these keywords
        if re.search(r'\b(service|solution|offering|expertise|consulting|support)\b', para, re.I):
            if len(para) > 20 and len(para) < 500:  # Avoid too short or too long paragraphs
                services.append(para)
        
        # Products often contain these keywords
        if re.search(r'\b(product|tool|software|platform|app|application)\b', para, re.I):
            if len(para) > 20 and len(para) < 500:  # Avoid too short or too long paragraphs
                products.append(para)
    
    # Limit to top 5 most relevant services and products
    services = services[:5]
    products = products[:5]
    
    return services, products

def extract_company_history(text, company_name):
    """Extract company history, founding date, and other significant information"""
    history_info = {}
    
    # Split text into paragraphs for analysis
    paragraphs = re.split(r'\n+', text)
    
    # Look for founding date patterns
    founding_date_patterns = [
        # Year only: "founded in 2010" or "established in 2010"
        r'(?:founded|established|started|launched|created|began|incorporated)(?:\s+\w+){0,3}\s+in\s+(\d{4})',
        # Month and year: "founded in January 2010"
        r'(?:founded|established|started|launched|created|began|incorporated)(?:\s+\w+){0,3}\s+in\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})',
        # Simple year search when company name is directly associated
        r'(?:' + re.escape(company_name) + r')\s+(?:was|were)?\s+(?:founded|established|started|launched|created|began|incorporated)(?:\s+\w+){0,3}\s+in\s+(\d{4})',
        # Simple founding statement
        r'(?:since|established|founded)\s+in\s+(\d{4})',
        # Founded by person in year
        r'(?:founded|established|started|created|began)\s+by\s+(?:[A-Z][a-z]+\s+)+in\s+(\d{4})',
        # Year directly with founding word
        r'(?:founded|established|started|created|began|incorporated):\s*(\d{4})',
    ]
    
    for pattern in founding_date_patterns:
        for para in paragraphs:
            matches = re.search(pattern, para, re.I)
            if matches:
                founding_year = matches.group(1)
                history_info['founding_year'] = founding_year
                history_info['founding_context'] = clean_text(para)
                break
        if 'founding_year' in history_info:
            break
    
    # Look for revenue/funding information
    financial_patterns = [
        # Revenue patterns
        r'(?:revenue|sales|turnover|annual\s+revenue)(?:\s+\w+){0,3}\s+(?:of|is|was|reached|exceeded|approximately|about|around|nearly|over)?\s+(?:\$|€|£|¥)?(\d+(?:[\.,]\d+)?)\s*(?:million|billion|trillion|m|b|t|M|B|T)',
        # Funding patterns
        r'(?:funding|raised|investment|capital|series\s+[a-z])(?:\s+\w+){0,3}\s+(?:of|totaling|totalling|reaching|approximately|about|around|nearly|over)?\s+(?:\$|€|£|¥)?(\d+(?:[\.,]\d+)?)\s*(?:million|billion|trillion|m|b|t|M|B|T)',
        # Valuation patterns
        r'(?:valued|valuation|worth|market\s+cap)(?:\s+\w+){0,3}\s+(?:of|at|approximately|about|around|nearly|over)?\s+(?:\$|€|£|¥)?(\d+(?:[\.,]\d+)?)\s*(?:million|billion|trillion|m|b|t|M|B|T)',
        # Direct currency amounts
        r'(?:\$|€|£|¥)(\d+(?:[\.,]\d+)?)\s*(?:million|billion|trillion|m|b|t|M|B|T)',
    ]
    
    for pattern in financial_patterns:
        for para in paragraphs:
            matches = re.search(pattern, para, re.I)
            if matches and 'financial_info' not in history_info:
                history_info['financial_info'] = clean_text(para)
                break
    
    # Look for employee count
    employee_patterns = [
        r'(?:employs|employees|team|staff|workforce)(?:\s+\w+){0,3}\s+(?:of|approximately|about|around|nearly|over|more\s+than)?\s+(\d{1,3}(?:,\d{3})*)\s+(?:people|employees|members|professionals|individuals|staff)',
        r'(?:employs|employees|team|staff|workforce|headcount)(?:\s+\w+){0,3}\s+(?:of|approximately|about|around|nearly|over|more\s+than)?\s+(\d{1,3}(?:,\d{3})*)',
        r'(?:company\s+size|size|headcount)(?:\s*:)?\s*(\d{1,3}(?:,\d{3})*\s*-\s*\d{1,3}(?:,\d{3})*)',
        r'(?:company\s+size|size|headcount)(?:\s*:)?\s*(\d{1,3}(?:,\d{3})*\+?)',
    ]
    
    for pattern in employee_patterns:
        for para in paragraphs:
            matches = re.search(pattern, para, re.I)
            if matches and 'employee_count' not in history_info:
                history_info['employee_count'] = matches.group(1)
                history_info['employee_context'] = clean_text(para)
                break
    
    # Look for founders information
    founder_patterns = [
        r'(?:founded|established|started|created|began)(?:\s+by\s+)((?:[A-Z][a-z]+ [A-Z][a-z]+)(?:,? (?:and )?))+',
        r'(?:founder|co-founder|creator)(?:s)?\s+(?:is|are|was|were)\s+((?:[A-Z][a-z]+ [A-Z][a-z]+)(?:,? (?:and )?))+',
        r'(?:founder|co-founder|creator)(?:s)?\s*(?::|-)?\s*((?:[A-Z][a-z]+ [A-Z][a-z]+)(?:,? (?:and )?))+',
    ]
    
    for pattern in founder_patterns:
        for para in paragraphs:
            matches = re.search(pattern, para, re.I)
            if matches and 'founders' not in history_info:
                history_info['founders'] = matches.group(1).strip()
                history_info['founder_context'] = clean_text(para)
                break
    
    # Look for acquisition information
    acquisition_patterns = [
        r'(?:acquired|purchased|bought|taken\s+over)(?:\s+by\s+)((?:[A-Z][a-z]+ )+)(?:\s+\w+){0,5}\s+in\s+(\d{4})',
        r'(?:acquisition|purchase|takeover|merger)(?:\s+\w+){0,3}\s+by\s+((?:[A-Z][a-z]+ )+)',
        r'(?:acquired|purchased|bought|takeover|acquisition)\s+(?:of|by)\s+((?:[A-Z][a-z]+ )+)',
    ]
    
    for pattern in acquisition_patterns:
        for para in paragraphs:
            matches = re.search(pattern, para, re.I)
            if matches and 'acquisition_info' not in history_info:
                history_info['acquisition_info'] = clean_text(para)
                break
    
    # Look for industry/sector information
    industry_patterns = [
        r'(?:industry|sector)(?:\s*:)?\s*([A-Za-z, &]+)',
        r'(?:specializes|specializes\s+in|focuses\s+on)(?:\s+the)?\s+([A-Za-z, &]+)\s+(?:industry|sector)',
        r'(?:leading|top)(?:\s+the)?\s+([A-Za-z, &]+)\s+(?:industry|sector|market)',
    ]
    
    for pattern in industry_patterns:
        for para in paragraphs:
            matches = re.search(pattern, para, re.I)
            if matches and 'industry' not in history_info:
                industry = matches.group(1).strip()
                if 5 < len(industry) < 100:  # Reasonable length for industry name
                    history_info['industry'] = industry
                    break
    
    # Look for timeline and milestones
    milestone_patterns = [
        r'(?:timeline|milestones|history)(?:\s*:)?\s*([^\.]+\d{4}[^\.]+)',
        r'(?:in\s+)(\d{4})(?:,?\s+)([^\.]+)',
    ]
    
    milestones = []
    for pattern in milestone_patterns:
        for para in paragraphs:
            matches = re.findall(pattern, para, re.I)
            if matches:
                for match in matches:
                    if isinstance(match, tuple):
                        milestone = f"{match[0]}: {match[1]}"
                    else:
                        milestone = match
                    milestones.append(clean_text(milestone))
    
    if milestones:
        history_info['milestones'] = milestones[:5]  # Limit to top 5 milestones
    
    return history_info

def extract_linkedin_company_info(soup, url, text):
    """Extract company information specifically from LinkedIn company pages"""
    linkedin_info = {}
    
    # Check if this is a LinkedIn page
    if 'linkedin.com/company/' not in url and 'linkedin.com/school/' not in url and 'linkedin.com/in/' not in url:
        return {}
    
    logger.info(f"Detected LinkedIn URL: {url}, extracting specialized LinkedIn info")
    
    # Extract the company name from LinkedIn
    # Try multiple class patterns to account for LinkedIn UI changes
    li_company_name_elem = soup.find('h1', class_=lambda c: c and ('org-top-card-summary__title' in c or 
                                                                'top-card-layout__title' in c or
                                                                'artdeco-entity-lockup__title' in c))
    if not li_company_name_elem:
        # Try generic h1 in header or profile section
        li_company_name_elem = soup.find('h1')
    
    if li_company_name_elem:
        linkedin_info['company_name'] = li_company_name_elem.text.strip()
    
    # Extract follower count - try multiple patterns
    follower_elem = soup.find(['div', 'span'], class_=lambda c: c and ('org-top-card-summary__follower-count' in c or 
                                                                     'top-card-layout__entity-info' in c or
                                                                     'follower-count' in c))
    if follower_elem:
        follower_text = follower_elem.text.strip()
        follower_match = re.search(r'([\d,\.]+\s*(?:followers|connections|people|professionals))', follower_text, re.I)
        if follower_match:
            linkedin_info['follower_count'] = follower_match.group(1)
        else:
            follower_match = re.search(r'([\d,\.]+[KMB]?\+?)', follower_text)
            if follower_match:
                linkedin_info['follower_count'] = follower_match.group(1)
    
    # Extract all company overview/description data with enhanced detection
    about_sections = []
    
    # New Method: Look for the "Overview" section specific to LinkedIn company pages
    # This targets the format shown in the user's screenshot
    overview_heading = soup.find(['h1', 'h2', 'h3'], string=lambda s: s and 'Overview' in s)
    if overview_heading:
        logger.info(f"Found LinkedIn 'Overview' heading - extracting company profile data: {overview_heading.text}")
        
        # Add specific extraction for Sixty One Steps format shown in screenshot
        # Look for lines like "SME Focused - Boutique Agency"
        parent_text = ""
        parent = overview_heading.parent
        if parent:
            parent_text = parent.text
            
        # Look for business category patterns like "SME Focused - Boutique Agency"
        category_patterns = [
            r'((?:SME|B2B|B2C|Enterprise)\s+(?:Focused|Specialized|Oriented|Centric))(?:\s*[:-]\s*|\s+)([A-Za-z0-9 &]+)',
            r'([A-Za-z]+\s+Agency|[A-Za-z]+\s+Service|[A-Za-z]+\s+Consultancy)(?:\s*[:-]\s*|\s+)([A-Za-z0-9 &]+)',
            r'(Select\s+[A-Za-z]+\s+[A-Za-z]+)(?:\s*[:-]\s*|\s+)([A-Za-z0-9 &]+)'
        ]
        
        for pattern in category_patterns:
            category_matches = re.findall(pattern, parent_text, re.I)
            if category_matches:
                categories = []
                for match in category_matches:
                    if len(match) >= 2:
                        full_match = f"{match[0]} - {match[1]}"
                        categories.append(full_match.strip())
                
                if categories:
                    linkedin_info['business_categories'] = categories
                    logger.info(f"Extracted LinkedIn business categories: {', '.join(categories)}")
        
        # Method A: Extract from the heading's parent section
        # Try to get all paragraphs that follow the Overview heading
        parent = overview_heading.parent
        while parent and parent.name not in ['section', 'div', 'main', 'article']:
            parent = parent.parent
            
        if parent:
            # Extract all paragraphs within this section
            overview_paragraphs = parent.find_all(['p', 'div'], recursive=True)
            overview_text = []
            for p in overview_paragraphs:
                p_text = p.text.strip()
                # Only include paragraphs with real content, avoid navigation elements
                if len(p_text) > 30 and not any(skip in p_text.lower() for skip in ['show more', 'read more', 'see all', 'follow']):
                    overview_text.append(p_text)
            
            if overview_text:
                full_overview = "\n\n".join(overview_text)
                about_sections.append(full_overview)
                logger.info(f"Extracted {len(overview_text)} paragraphs from LinkedIn Overview section")
        
        # Method B: Look for specific content divisions after the Overview heading
        # This targets the specific layout in the screenshot
        next_sibling = overview_heading.find_next_sibling()
        if next_sibling:
            sibling_text = next_sibling.text.strip()
            if len(sibling_text) > 100:  # Long enough to be company description
                about_sections.append(sibling_text)
                logger.info("Extracted LinkedIn overview text from sibling element")
            
            # Try to find all paragraphs
            sibling_paragraphs = next_sibling.find_all(['p', 'div'])
            if sibling_paragraphs:
                overview_text = []
                for p in sibling_paragraphs:
                    p_text = p.text.strip()
                    if len(p_text) > 30:
                        overview_text.append(p_text)
                
                if overview_text:
                    full_overview = "\n\n".join(overview_text)
                    about_sections.append(full_overview)
                    logger.info(f"Extracted {len(overview_text)} paragraphs from sibling of Overview heading")
        
        # Method C: Extract the entire text block for overview sections
        # Common in LinkedIn layout where they have blocks of descriptive text
        # This looks for text blocks directly visible in the page as shown in screenshot
        overview_parent = overview_heading.parent
        overview_grandparent = overview_parent.parent if overview_parent else None
        
        if overview_grandparent:
            # Find all direct text blocks and paragraphs in the overview section
            all_blocks = []
            for child in overview_grandparent.children:
                if child.name and child.name not in ['h1', 'h2', 'h3', 'h4']:  # Skip headings
                    block_text = child.text.strip()
                    if len(block_text) > 50:  # Skip short elements
                        all_blocks.append(block_text)
            
            if all_blocks:
                block_text = "\n\n".join(all_blocks)
                about_sections.append(block_text)
                logger.info(f"Extracted {len(all_blocks)} text blocks from LinkedIn Overview section")
    
    # Method 1: Try standard about section by class
    about_section = soup.find('section', class_=lambda c: c and 'artdeco-card' in c and ('about-us' in c or 'about-section' in c))
    if about_section:
        about_sections.append(about_section.text.strip())
        logger.info("Found LinkedIn about section by class")
    
    # Method 2: Try by ID
    about_section_id = soup.find(id=lambda i: i and ('about-us' in i or 'about-section' in i or 'overview' in i))
    if about_section_id:
        about_sections.append(about_section_id.text.strip())
        logger.info("Found LinkedIn about section by ID")
    
    # Method 3: Try other common about containers by class
    about_containers = soup.find_all('div', class_=lambda c: c and any(term in c for term in ['about-us', 'description', 'about-section', 'overview', 'company-info']))
    for container in about_containers:
        about_sections.append(container.text.strip())
        logger.info("Found LinkedIn about section by container class")
    
    # Method 4: Find sections by heading content
    about_headings = soup.find_all(['h1', 'h2', 'h3', 'h4'], string=lambda s: s and ('About' in s or 'Overview' in s or 'Company' in s))
    for heading in about_headings:
        # Get parent section or div
        parent = heading
        for _ in range(3):  # Go up to 3 levels up
            if parent:
                parent = parent.parent
                if parent and parent.name in ['section', 'div']:
                    about_sections.append(parent.text.strip())
                    logger.info(f"Found LinkedIn about section from heading: {heading.text}")
                    break
    
    # Method 5: Look specifically for paragraphs in about sections
    for section_text in about_sections.copy():  # Use copy to avoid modifying while iterating
        # Check for structured data within the text
        about_lines = section_text.split('\n')
        for line in about_lines:
            # Look for "About" prefix
            if line.strip().startswith('About'):
                rest_of_line = line.strip()[5:].strip()  # Skip "About" and any spaces
                if len(rest_of_line) > 50:  # If substantial content after "About"
                    about_sections.append(rest_of_line)
                    logger.info("Found LinkedIn about content from line starting with 'About'")
    
    # Method 6: Find paragraphs with substantial content
    paragraphs = soup.find_all('p')
    for p in paragraphs:
        p_text = p.text.strip()
        # Only include paragraphs with substantial content that might be overview text
        if len(p_text) > 100 and p_text.count('.') > 2:  # Multiple sentences
            about_sections.append(p_text)
            logger.info("Found potential LinkedIn about content from paragraph")
    
    # Method 7: Look for meta description
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    if meta_desc and meta_desc.has_attr('content'):
        about_sections.append(meta_desc['content'])
        logger.info("Found LinkedIn about content from meta description")
    
    # Filter and deduplicate about sections
    filtered_sections = []
    seen_content = set()
    for section in about_sections:
        # Clean the section text
        clean_section = clean_text(section)
        
        # Skip if too short or already seen
        if len(clean_section) < 50 or clean_section in seen_content:
            continue
            
        filtered_sections.append(clean_section)
        seen_content.add(clean_section)
    
    if filtered_sections:
        # Use the longest description found, which is likely the most complete
        linkedin_info['overview'] = max(filtered_sections, key=len)
        
        # Store all sections for comprehensive data
        if len(filtered_sections) > 1:
            linkedin_info['all_about_sections'] = filtered_sections
            
        logger.info(f"Extracted LinkedIn overview with {len(linkedin_info['overview'])} characters")
    
    # Extract all company info from text with enhanced patterns
    
    # Company size
    size_patterns = [
        r'(?:company\s+size|size|employees)(?:\s*:)?\s*(\d{1,3}(?:,\d{3})*(?:\s*-\s*\d{1,3}(?:,\d{3})*|\+))',
        r'(?:company\s+size|size|employees)(?:\s*:)?\s*(\d+(?:,\d+)*(?:\s*to\s*\d+(?:,\d+)*|\+)?)',
        r'(\d+(?:,\d+)*(?:\s*-\s*\d+(?:,\d+)*|\+))\s+employees'
    ]
    
    for pattern in size_patterns:
        size_match = re.search(pattern, text, re.I)
        if size_match:
            linkedin_info['company_size'] = size_match.group(1)
            break
    
    # Founded date - try multiple patterns
    founded_patterns = [
        r'(?:founded|established)(?:\s*:)?\s*(\d{4})',
        r'(?:founded|established)(?:\s+in)?\s+(\d{4})',
        r'(?:since|founded|established)\s+(\d{4})',
        r'founded(?:\s*:)?\s*(\w+\s+\d{4})'  # Month and year
    ]
    
    for pattern in founded_patterns:
        founded_match = re.search(pattern, text, re.I)
        if founded_match:
            linkedin_info['founded'] = founded_match.group(1)
            # Capture surrounding context for founding info
            context_pattern = r'(.{0,50}' + re.escape(founded_match.group(0)) + r'.{0,50})'
            context_match = re.search(context_pattern, text, re.I | re.DOTALL)
            if context_match:
                linkedin_info['founding_context'] = clean_text(context_match.group(1))
            break
    
    # Industry with improved matching
    industry_patterns = [
        r'(?:industry|sector)(?:\s*:)?\s*([A-Za-z0-9, &/]+)',
        r'(?:industry|sector)(?:\s*:)?\s*([^\.]+)',
        r'(?:in\s+the\s+)([A-Za-z, &]+)(?:\s+industry|sector)'
    ]
    
    for pattern in industry_patterns:
        industry_match = re.search(pattern, text, re.I)
        if industry_match:
            industry = industry_match.group(1).strip()
            if 5 < len(industry) < 100:  # Reasonable length check
                linkedin_info['industry'] = industry
                break
    
    # Headquarters location - enhanced patterns
    hq_patterns = [
        r'(?:headquarters|location|based\s+in)(?:\s*:)?\s*([A-Za-z0-9, ]+)',
        r'(?:headquartered|located)\s+in\s+([A-Za-z0-9, ]+)',
        r'(?:HQ|main\s+office)(?:\s*:)?\s+([A-Za-z0-9, ]+)'
    ]
    
    for pattern in hq_patterns:
        hq_match = re.search(pattern, text, re.I)
        if hq_match:
            hq_location = hq_match.group(1).strip()
            if 3 < len(hq_location) < 100:  # Reasonable length check
                linkedin_info['headquarters'] = hq_location
                break
    
    # Extract specialties with improved matching
    specialties_patterns = [
        r'specialties(?:\s*:)?\s*([^\.]+)',
        r'specializing\s+in\s+([^\.]+)',
        r'expertise(?:\s+in)?(?:\s*:)?\s*([^\.]+)'
    ]
    
    for pattern in specialties_patterns:
        specialties_match = re.search(pattern, text, re.I)
        if specialties_match:
            specialties_text = specialties_match.group(1)
            # Split by commas or "and"
            specialties = re.split(r',\s*|\s+and\s+', specialties_text)
            linkedin_info['specialties'] = [s.strip() for s in specialties if len(s.strip()) > 3]
            break
    
    # Extract funding/financial information with enhanced patterns
    funding_patterns = [
        r'(?:funding|raised|investment|capital|series\s+[a-z])(?:\s+\w+){0,3}\s+(?:of|totaling|totalling|reaching|approximately|about|around|nearly|over)?\s+(?:\$|€|£|¥)?(\d+(?:[\.,]\d+)?)\s*(?:million|billion|trillion|m|b|t|M|B|T)',
        r'(?:funding|raised|investment|capital)(?:\s+of)?\s+(?:\$|€|£|¥)(\d+(?:[\.,]\d+)?)\s*(?:million|billion|trillion|[MBT])',
        r'(?:series\s+[a-z])(?:\s+funding)?\s+(?:of)?\s+(?:\$|€|£|¥)?(\d+(?:[\.,]\d+)?)\s*(?:million|billion|trillion|[MBT])',
        r'(?:valuation|valued\s+at)\s+(?:\$|€|£|¥)?(\d+(?:[\.,]\d+)?)\s*(?:million|billion|trillion|[MBT])'
    ]
    
    for pattern in funding_patterns:
        funding_match = re.search(pattern, text, re.I)
        if funding_match:
            # Capture full context of the funding information
            context_pattern = r'(.{0,100}' + re.escape(funding_match.group(0)) + r'.{0,100})'
            context_match = re.search(context_pattern, text, re.I | re.DOTALL)
            if context_match:
                linkedin_info['funding'] = clean_text(context_match.group(1))
            else:
                linkedin_info['funding'] = funding_match.group(0)
            break
    
    # Extract revenue information
    revenue_patterns = [
        r'(?:revenue|sales|turnover)(?:\s+\w+){0,3}\s+(?:of|is|was|reached|exceeded|approximately|about|around|nearly|over)?\s+(?:\$|€|£|¥)?(\d+(?:[\.,]\d+)?)\s*(?:million|billion|trillion|[MBT])',
        r'annual\s+(?:revenue|sales)\s+(?:of)?\s+(?:\$|€|£|¥)?(\d+(?:[\.,]\d+)?)\s*(?:million|billion|trillion|[MBT])'
    ]
    
    for pattern in revenue_patterns:
        revenue_match = re.search(pattern, text, re.I)
        if revenue_match:
            context_pattern = r'(.{0,100}' + re.escape(revenue_match.group(0)) + r'.{0,100})'
            context_match = re.search(context_pattern, text, re.I | re.DOTALL)
            if context_match:
                linkedin_info['revenue'] = clean_text(context_match.group(1))
            else:
                linkedin_info['revenue'] = revenue_match.group(0)
            break
    
    # Extract milestone/timeline information
    timeline_patterns = [
        r'(\d{4})(?:\s*(?:-|–|:)\s*)([^\.;]+)',
        r'(?:in|since)\s+(\d{4})(?:\s*,)?\s+([^\.;]+)'
    ]
    
    milestones = []
    for pattern in timeline_patterns:
        matches = re.findall(pattern, text, re.I)
        for match in matches:
            if isinstance(match, tuple) and len(match) >= 2:
                year = match[0]
                event = match[1].strip()
                if len(event) > 10:  # Skip very short descriptions
                    milestones.append(f"{year}: {event}")
    
    if milestones:
        linkedin_info['milestones'] = milestones[:5]  # Limit to top 5 milestones
    
    # Extract website from LinkedIn page - try multiple patterns
    website_elem = soup.find('a', class_=lambda c: c and ('org-about-us-company-module__website' in c or 
                                                      'top-card-link' in c or
                                                      'website' in c))
    if website_elem:
        linkedin_info['website'] = website_elem.get('href')
    
    # Try to extract any additional profile sections that contain key business information
    sections = soup.find_all(['section', 'div'], class_=lambda c: c and ('artdeco-card' in c or 'profile-section' in c))
    for section in sections:
        # Get section title or heading
        section_title_elem = section.find(['h2', 'h3'])
        if section_title_elem:
            section_title = section_title_elem.text.strip().lower()
            section_content = section.text.strip()
            
            # Check for interesting sections by keywords
            if any(keyword in section_title for keyword in ['about', 'overview', 'history', 'timeline']):
                if 'overview' not in linkedin_info:
                    linkedin_info['overview'] = section_content
            elif any(keyword in section_title for keyword in ['highlight', 'achievement', 'accomplishment']):
                linkedin_info['highlights'] = section_content
    
    # Enhanced data extraction: posts, job openings, and people
    try:
        # Only proceed with enhanced extraction if this is a LinkedIn company URL
        if 'linkedin.com/company/' in url:
            logger.info(f"Adding enhanced LinkedIn data extraction for: {url}")
            enhanced_data = extract_all_enhanced_data(url)
            
            # Store the complete raw data for each category to enable better template handling
            if 'posts' in enhanced_data:
                # Store the complete posts data structure (including authentication_required flag)
                linkedin_info['posts'] = enhanced_data['posts']
            
            if 'jobs' in enhanced_data:
                # Store the complete jobs data structure
                linkedin_info['jobs'] = enhanced_data['jobs']
            
            if 'people' in enhanced_data:
                # Store the complete people data structure
                linkedin_info['people'] = enhanced_data['people']
            
            # Also maintain the legacy structure for backward compatibility
            
            # Add posts data if available
            if 'posts' in enhanced_data:
                posts_data = enhanced_data['posts']
                
                if 'count' in posts_data:
                    linkedin_info['post_count'] = posts_data['count']
                
                if 'posts' in posts_data and posts_data['posts']:
                    # Limit to top 5 posts
                    posts = posts_data['posts'][:5]
                    linkedin_info['recent_posts'] = posts
                    
                    # Also create a brief summary of recent posts
                    post_summaries = []
                    for post in posts:
                        if 'text' in post:
                            post_text = post['text']
                            # Create a brief summary (first 100 chars)
                            summary = post_text[:100] + ('...' if len(post_text) > 100 else '')
                            date = post.get('date', 'Recently')
                            reactions = post.get('reactions', 'Unknown')
                            post_summary = f"{summary} ({date}, {reactions} reactions)"
                            post_summaries.append(post_summary)
                    
                    if post_summaries:
                        linkedin_info['post_summaries'] = post_summaries
            
            # Add job openings data if available
            if 'jobs' in enhanced_data:
                jobs_data = enhanced_data['jobs']
                
                if 'count' in jobs_data:
                    linkedin_info['job_opening_count'] = jobs_data['count']
                
                if 'jobs' in jobs_data and jobs_data['jobs']:
                    # Limit to top 5 job openings
                    jobs = jobs_data['jobs'][:5]
                    linkedin_info['job_openings'] = jobs
            
            # Add people data if available
            if 'people' in enhanced_data:
                people_data = enhanced_data['people']
                
                if 'employee_count' in people_data:
                    linkedin_info['employee_count_from_people'] = people_data['employee_count']
                
                if 'leaders' in people_data and people_data['leaders']:
                    linkedin_info['leadership_team'] = people_data['leaders']
                
                if 'locations' in people_data and people_data['locations']:
                    linkedin_info['employee_locations'] = people_data['locations']
                
                if 'departments' in people_data and people_data['departments']:
                    linkedin_info['departments'] = people_data['departments']
            
            # Log the enhanced data fields that were added
            enhanced_fields = [key for key in linkedin_info.keys() if key in [
                'posts', 'jobs', 'people',
                'post_count', 'recent_posts', 'post_summaries', 
                'job_opening_count', 'job_openings', 
                'leadership_team', 'employee_locations', 'departments'
            ]]
            
            if enhanced_fields:
                logger.info(f"Added enhanced LinkedIn data: {', '.join(enhanced_fields)}")
    
    except Exception as e:
        logger.error(f"Error extracting enhanced LinkedIn data: {str(e)}")
        # Continue with basic data even if enhanced extraction fails
    
    logger.info(f"Extracted LinkedIn data: {', '.join(linkedin_info.keys())}")
    return linkedin_info

def scrape_website(url):
    """Scrape website and extract business information"""
    logger.info(f"Starting scrape of URL: {url}")
    
    try:
        # Parse domain for later use
        parsed_url = urlparse(url)
        domain_name = parsed_url.netloc
        
        # Enhanced LinkedIn detection for more robust handling
        is_linkedin = 'linkedin.com' in url.lower()
        
        try:
            # Use trafilatura to get clean text
            downloaded = trafilatura.fetch_url(url)
            if not downloaded:
                logger.error(f"Failed to download URL: {url}")
                # If LinkedIn page but download failed, provide a specific message
                if is_linkedin:
                    return {
                        'company_name': "LinkedIn Data Extraction Limited",
                        'description': "LinkedIn restricts automated data extraction. For best results, try accessing LinkedIn company pages directly and copy the information manually.",
                        'linkedin_data': {
                            'overview': "LinkedIn has protection mechanisms against automated scraping. For comprehensive company data from LinkedIn, you may need to access it manually."
                        }
                    }
                return None
            
            # Extract clean text for analysis
            clean_content = trafilatura.extract(downloaded)
            if not clean_content:
                logger.error(f"Failed to extract content from URL: {url}")
                # LinkedIn-specific handling for content extraction failures
                if is_linkedin:
                    return {
                        'company_name': "LinkedIn Content Extraction Limited",
                        'description': "LinkedIn content extraction was limited. For better results, try accessing LinkedIn company pages directly and copy the information manually.",
                        'linkedin_data': {
                            'overview': "LinkedIn has enhanced their protection against automated data extraction. For best results with company data from LinkedIn, consider accessing pages manually."
                        }
                    }
                return None
                
        except Exception as download_error:
            logger.error(f"Error during download/extraction: {str(download_error)}")
            # Special handling for LinkedIn URLs
            if is_linkedin:
                return {
                    'company_name': "LinkedIn Access Limited",
                    'description': "LinkedIn restricts automated access. For better results, try accessing LinkedIn pages directly.",
                    'linkedin_data': {
                        'overview': "LinkedIn has implemented measures to prevent automated scraping. For access to company information, visit LinkedIn directly."
                    }
                }
            # Re-raise for other URLs
            raise
        
        # Use BeautifulSoup for structured parsing
        headers = {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/123.0.0.0 Safari/537.36'
            )
        }
        
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            html_content = response.read().decode('utf-8', errors='replace')
        
        # Parse with both parsers for better results
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Use our custom HTML parser as well
        parser = MyHTMLParser()
        parser.feed(html_content)
        
        # Extract business information from both methods
        company_name = extract_company_name(soup, domain_name)
        # If company name not found with BeautifulSoup, try the HTML parser
        if company_name == "Unknown Company" and parser.company_name:
            company_name = parser.company_name
        
        # Extract contact information from both visible text and metadata
        meta_description = soup.find('meta', attrs={'name': 'description'})
        meta_text = ""
        if meta_description and meta_description.has_attr('content'):
            meta_text = meta_description['content']
        
        full_text = f"{clean_content} {meta_text} {str(soup)}"
        
        emails = extract_emails(full_text)
        phones = extract_phones(full_text)
        addresses = extract_addresses(full_text)
        social_media = extract_social_media(full_text)
        
        # Add any contact info from HTML parser
        parsed_contacts = parser.contact_info
        for contact in parsed_contacts:
            # Check for email pattern
            email_match = re.search(EMAIL_PATTERN, contact)
            if email_match:
                emails.append(email_match.group(0))
                continue
                
            # Check for phone pattern
            phone_match = re.search(PHONE_PATTERN, contact)
            if phone_match:
                phones.append(phone_match.group(0))
                continue
                
            # Check for address pattern
            addr_match = re.search(ADDRESS_PATTERN, contact, re.IGNORECASE)
            if addr_match:
                addresses.append(addr_match.group(0))
        
        # Remove duplicates
        emails = list(set(emails))
        phones = list(set(phones))
        addresses = list(set(addresses))
        
        # Extract services and products from clean content and parser
        bs_services, bs_products = extract_services_products(clean_content, company_name)
        
        # Combine services and products from both methods
        services = bs_services
        products = bs_products
        
        # Add services and products from HTML parser
        services.extend([s for s in parser.services if s not in services])
        products.extend([p for p in parser.products if p not in products])
        
        # Limit to top 5 most relevant services and products
        services = services[:5]
        products = products[:5]
        
        # Get meta keywords
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        keywords = []
        if meta_keywords and meta_keywords.has_attr('content'):
            content = meta_keywords['content']
            if content and isinstance(content, str):
                keywords = [k.strip() for k in content.split(',')]
        
        # Get business description
        description = ""
        about_section = soup.find(id=re.compile(r'about', re.I)) or \
                        soup.find('section', class_=re.compile(r'about', re.I)) or \
                        soup.find('div', class_=re.compile(r'about', re.I))
        
        if about_section:
            description = clean_text(about_section.get_text())
        
        if not description and meta_description and meta_description.has_attr('content'):
            description = meta_description['content']
        
        # Extract company history information
        company_history = extract_company_history(clean_content, company_name)
        
        # Check if this is a LinkedIn page and extract specialized info
        linkedin_info = extract_linkedin_company_info(soup, url, clean_content)
        
        # If LinkedIn data is available, enhance our company history data
        if linkedin_info:
            # Use LinkedIn company name if available
            if 'company_name' in linkedin_info and linkedin_info['company_name']:
                company_name = linkedin_info['company_name']
            
            # Add founding year if available from LinkedIn but not from general extraction
            if 'founded' in linkedin_info and 'founding_year' not in company_history:
                company_history['founding_year'] = linkedin_info['founded']
                company_history['founding_context'] = f"Founded in {linkedin_info['founded']}"
            
            # Add company size if available
            if 'company_size' in linkedin_info and 'employee_count' not in company_history:
                company_history['employee_count'] = linkedin_info['company_size']
                company_history['employee_context'] = f"Company size: {linkedin_info['company_size']}"
            
            # Add industry if available
            if 'industry' in linkedin_info and 'industry' not in company_history:
                company_history['industry'] = linkedin_info['industry']
            
            # Add LinkedIn-specific information to the result
            if 'specialties' in linkedin_info:
                company_history['specialties'] = linkedin_info['specialties']
            
            if 'headquarters' in linkedin_info:
                company_history['headquarters'] = linkedin_info['headquarters']
            
            if 'follower_count' in linkedin_info:
                company_history['linkedin_followers'] = linkedin_info['follower_count']
            
            if 'funding' in linkedin_info and 'financial_info' not in company_history:
                company_history['financial_info'] = linkedin_info['funding']
        
        # Combine everything into a result dictionary
        result = {
            'company_name': company_name,
            'description': description[:500] if description else "",
            'contact_info': {
                'emails': emails,
                'phones': phones,
                'addresses': addresses,
                'social_media': social_media
            },
            'services': services,
            'products': products,
            'keywords': keywords,
            'company_history': company_history,
            'url': url,
            'domain': domain_name
        }
        
        # Add LinkedIn-specific full data section if available
        if linkedin_info:
            result['linkedin_data'] = linkedin_info
        
        logger.info(f"Successfully scraped {url}")
        return result
        
    except Exception as e:
        logger.error(f"Error during scraping: {str(e)}")
        return None
