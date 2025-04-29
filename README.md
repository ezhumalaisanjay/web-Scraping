# LinkedIn Scraper

A comprehensive web scraping API specialized in extracting structured business information from websites, with a focus on LinkedIn data extraction.

## Features

- Extract company information from LinkedIn profiles
- Find LinkedIn company URLs from regular websites
- Batch processing for multiple URLs
- Extract detailed business information including:
  - Company overview and about sections
  - Company posts and job listings
  - People/employee information
  - Contact details and social media links

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/linkedin-scraper.git
cd linkedin-scraper

# Install dependencies
pip install -e .
```

## Usage

### Running locally

```bash
# Start the Flask application
gunicorn --bind 0.0.0.0:5000 main:app
```

### Usage in Web Interface

1. Navigate to the home page (http://localhost:5000)
2. Enter a LinkedIn company URL or a regular company website URL
3. Choose extraction options
4. View the structured results

### API Endpoints

- `/api/scrape` - Extract data from a LinkedIn profile
- `/api/find_linkedin` - Find LinkedIn URL from a company website
- `/api/batch_process` - Process multiple URLs in batch mode

## Deployment

The application is configured for deployment to:
- AWS Elastic Beanstalk
- AWS Amplify 
- Google App Engine

## Authentication

The scraper supports both authenticated and unauthenticated LinkedIn access. For better data extraction, you can provide LinkedIn credentials using environment variables:

```
LINKEDIN_EMAIL=your-email@example.com
LINKEDIN_PASSWORD=your-password
```

## License

[MIT License](LICENSE)