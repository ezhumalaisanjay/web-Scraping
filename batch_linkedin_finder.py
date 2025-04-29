#!/usr/bin/env python3
"""
Batch LinkedIn URL Finder

This script takes a list of company website URLs (either from a file or command line arguments)
and finds their LinkedIn company profile URLs.

Usage:
    python batch_linkedin_finder.py url1 url2 url3 ...
    python batch_linkedin_finder.py --file urls.txt

Output formats:
    --json : Output results as JSON
    --csv : Output results as CSV
    Default: Simple text output
"""

import argparse
import csv
import json
import logging
import sys
from linkedin_finder import extract_linkedin_url
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def process_url(url):
    """Process a single URL and return the result"""
    # Add http:// prefix if not present
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    try:
        # Extract domain for display
        domain = urlparse(url).netloc
        
        logger.info(f"Processing: {domain}")
        linkedin_url = extract_linkedin_url(url)
        
        if linkedin_url:
            logger.info(f"Found LinkedIn URL: {linkedin_url}")
            return {
                'success': True,
                'website_url': url,
                'domain': domain,
                'linkedin_url': linkedin_url
            }
        else:
            logger.warning(f"No LinkedIn URL found for: {domain}")
            return {
                'success': False,
                'website_url': url,
                'domain': domain,
                'linkedin_url': None
            }
    except Exception as e:
        logger.error(f"Error processing {url}: {str(e)}")
        return {
            'success': False,
            'website_url': url,
            'domain': urlparse(url).netloc,
            'linkedin_url': None,
            'error': str(e)
        }

def read_urls_from_file(filename):
    """Read URLs from a file, one URL per line"""
    try:
        with open(filename, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
        return urls
    except Exception as e:
        logger.error(f"Error reading file {filename}: {str(e)}")
        return []

def output_results_as_json(results):
    """Output results in JSON format"""
    print(json.dumps(results, indent=2))

def output_results_as_csv(results):
    """Output results in CSV format"""
    fieldnames = ['website_url', 'domain', 'linkedin_url', 'success']
    writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames, extrasaction='ignore')
    writer.writeheader()
    for result in results:
        writer.writerow(result)

def output_results_as_text(results):
    """Output results in simple text format"""
    found_count = sum(1 for r in results if r['success'])
    total_count = len(results)
    
    print(f"\nResults: Found {found_count} LinkedIn URLs out of {total_count} websites\n")
    print("Website".ljust(40) + "LinkedIn URL")
    print("-" * 80)
    
    for result in results:
        domain = result['domain']
        linkedin_url = result['linkedin_url'] or "Not found"
        print(f"{domain.ljust(40)} {linkedin_url}")

def main():
    parser = argparse.ArgumentParser(description='Batch LinkedIn URL Finder')
    parser.add_argument('urls', nargs='*', help='List of website URLs to process')
    parser.add_argument('--file', '-f', help='File containing URLs, one per line')
    parser.add_argument('--json', action='store_true', help='Output results as JSON')
    parser.add_argument('--csv', action='store_true', help='Output results as CSV')
    parser.add_argument('--output', '-o', help='Output file (default: stdout)')
    args = parser.parse_args()
    
    # Get URLs from either command line or file
    urls = []
    if args.file:
        urls = read_urls_from_file(args.file)
    elif args.urls:
        urls = args.urls
    else:
        parser.print_help()
        sys.exit(1)
    
    if not urls:
        logger.error("No URLs to process")
        sys.exit(1)
    
    logger.info(f"Processing {len(urls)} URLs...")
    
    # Process URLs
    results = []
    for url in urls:
        result = process_url(url)
        results.append(result)
    
    # Redirect output if needed
    if args.output:
        original_stdout = sys.stdout
        try:
            with open(args.output, 'w') as f:
                sys.stdout = f
                if args.json:
                    output_results_as_json(results)
                elif args.csv:
                    output_results_as_csv(results)
                else:
                    output_results_as_text(results)
        finally:
            sys.stdout = original_stdout
    else:
        # Output to stdout
        if args.json:
            output_results_as_json(results)
        elif args.csv:
            output_results_as_csv(results)
        else:
            output_results_as_text(results)
    
    # Summary
    found_count = sum(1 for r in results if r['success'])
    logger.info(f"Finished processing {len(urls)} URLs")
    logger.info(f"Found {found_count} LinkedIn URLs")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())