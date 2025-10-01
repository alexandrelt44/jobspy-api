"""
Utility functions for Wellfound scraper
"""

import json
import re
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

from .constant import LOCATION_MAPPINGS, JOB_TITLE_MAPPINGS, WELLFOUND_CATEGORIES


def normalize_job_title(job_title: str) -> str:
    """
    Convert job title to Wellfound URL format
    
    Args:
        job_title: Original job title from search
        
    Returns:
        Normalized job title for URL
    """
    if not job_title:
        return "software-engineer"  # Default fallback
    
    # Check direct mappings first
    if job_title in JOB_TITLE_MAPPINGS:
        return JOB_TITLE_MAPPINGS[job_title]
    
    # Try case-insensitive matching
    for key, value in JOB_TITLE_MAPPINGS.items():
        if job_title.lower() == key.lower():
            return value
    
    # Generic conversion
    normalized = job_title.lower()
    normalized = re.sub(r'[^\w\s-]', '', normalized)  # Remove special chars
    normalized = re.sub(r'\s+', '-', normalized.strip())  # Replace spaces with dashes
    normalized = re.sub(r'-+', '-', normalized)  # Replace multiple dashes with single
    
    # Check if the normalized title matches any Wellfound category
    if normalized in WELLFOUND_CATEGORIES:
        return normalized
    
    # If no match, try to find closest match
    for category in WELLFOUND_CATEGORIES:
        if any(word in normalized for word in category.split('-')):
            return category
    
    # Default fallback
    return "software-engineer"


def normalize_location(location: str) -> str:
    """
    Convert location to Wellfound URL format
    
    Args:
        location: Original location from search
        
    Returns:
        Normalized location for URL
    """
    if not location:
        return "europe"  # Default fallback
    
    # Check direct mappings first
    if location in LOCATION_MAPPINGS:
        return LOCATION_MAPPINGS[location]
    
    # Try case-insensitive matching
    for key, value in LOCATION_MAPPINGS.items():
        if location.lower() == key.lower():
            return value
    
    # Handle remote variations
    if "remote" in location.lower():
        return "remote"
    
    # Generic conversion
    normalized = location.lower()
    normalized = re.sub(r'[^\w\s-]', '', normalized)  # Remove special chars
    normalized = re.sub(r'\s+', '-', normalized.strip())  # Replace spaces with dashes
    normalized = re.sub(r'-+', '-', normalized)  # Replace multiple dashes with single
    
    return normalized


def build_search_url(base_url: str, job_title: str, location: str) -> str:
    """
    Build the complete search URL for Wellfound
    
    Args:
        base_url: Base Wellfound URL
        job_title: Normalized job title
        location: Normalized location
        
    Returns:
        Complete search URL
    """
    normalized_title = normalize_job_title(job_title)
    normalized_location = normalize_location(location)
    
    # Handle remote jobs specially
    if normalized_location == "remote":
        return f"{base_url}/remote/{normalized_title}-jobs"
    
    # Standard role + location URL
    return f"{base_url}/role/l/{normalized_title}/{normalized_location}"


def extract_jobs_from_html(html: str, base_url: str) -> List[Dict]:
    """
    Extract job listings from Wellfound HTML page
    
    Args:
        html: HTML content of the page
        base_url: Base URL for resolving relative links
        
    Returns:
        List of job dictionaries
    """
    soup = BeautifulSoup(html, 'html.parser')
    jobs = []
    
    # Try to find JSON data embedded in script tags first
    json_jobs = extract_jobs_from_json_scripts(soup)
    if json_jobs:
        return json_jobs
    
    # Fallback to HTML parsing
    # Parse each job link individually with its company context
    job_links = soup.find_all('a', href=re.compile(r'/jobs/\d+-'))
    
    # To avoid duplicates, track which job IDs we've already processed
    processed_job_ids = set()
    
    for job_link in job_links:
        try:
            # Extract job ID for deduplication
            job_id = re.search(r'/jobs/(\d+)-', job_link.get('href', ''))
            if job_id:
                job_id = job_id.group(1)
                if job_id in processed_job_ids:
                    continue  # Skip duplicates
                processed_job_ids.add(job_id)
            
            # Parse this specific job link with its company context
            job_data = parse_individual_job(job_link, base_url, soup)
            if job_data:
                jobs.append(job_data)
                
        except Exception as e:
            # Log the error but continue processing other jobs
            print(f"Error parsing job link: {e}")
            continue
    
    return jobs


def extract_jobs_from_json_scripts(soup: BeautifulSoup) -> List[Dict]:
    """
    Extract job data from JSON embedded in script tags
    
    Args:
        soup: BeautifulSoup object of the page
        
    Returns:
        List of job dictionaries or empty list
    """
    # Look for common patterns where job data is embedded
    script_patterns = [
        '__NEXT_DATA__',
        'window.__INITIAL_STATE__',
        'window.jobData',
        'window.searchResults'
    ]
    
    for script in soup.find_all('script'):
        if not script.string:
            continue
            
        script_content = script.string.strip()
        
        for pattern in script_patterns:
            if pattern in script_content:
                try:
                    # Extract JSON data
                    json_match = re.search(f'{pattern}.*?=\\s*({{.*?}})(?:;|$)', script_content, re.DOTALL)
                    if json_match:
                        json_data = json.loads(json_match.group(1))
                        return parse_json_job_data(json_data)
                except (json.JSONDecodeError, AttributeError) as e:
                    print(f"Error parsing JSON from script: {e}")
                    continue
    
    return []


def parse_json_job_data(json_data: Dict) -> List[Dict]:
    """
    Parse job data from JSON structure
    
    Args:
        json_data: JSON data containing job information
        
    Returns:
        List of standardized job dictionaries
    """
    jobs = []
    
    # This will need to be adjusted based on actual Wellfound JSON structure
    # Common paths where job data might be found
    possible_paths = [
        ['props', 'pageProps', 'jobs'],
        ['props', 'initialState', 'jobs'],
        ['jobs'],
        ['data', 'jobs'],
        ['searchResults', 'jobs']
    ]
    
    job_list = None
    for path in possible_paths:
        current = json_data
        try:
            for key in path:
                current = current[key]
            if isinstance(current, list):
                job_list = current
                break
        except (KeyError, TypeError):
            continue
    
    if not job_list:
        return jobs
    
    for job_item in job_list:
        try:
            job = standardize_job_data(job_item)
            if job:
                jobs.append(job)
        except Exception as e:
            print(f"Error standardizing job data: {e}")
            continue
    
    return jobs


def parse_individual_job(job_link, base_url: str, soup: BeautifulSoup) -> Optional[Dict]:
    """
    Parse an individual job link with its company context
    
    Args:
        job_link: BeautifulSoup job link element
        base_url: Base URL for resolving links
        soup: Full page soup for company context lookup
        
    Returns:
        Job dictionary or None
    """
    try:
        # Get basic job info from the link itself
        title = clean_text(job_link.get_text())
        job_url = urljoin(base_url, job_link['href'])
        
        # Find the company context for this job
        # Go up the DOM to find the company container
        company_info = find_company_for_job(job_link, soup)
        
        # Find job-specific details in the immediate area around the job link
        job_details = find_job_details_near_link(job_link)
        
        job_data = {
            'title': title,
            'company': company_info.get('name') if company_info else None,
            'location': job_details.get('location'),
            'job_type': job_details.get('job_type'),
            'job_url': job_url,
            'site': 'wellfound'
        }
        
        # Only return if we have essential information
        if job_data['title'] and job_data['job_url']:
            return job_data
    
    except Exception as e:
        print(f"Error parsing individual job: {e}")
    
    return None


def find_company_for_job(job_link, soup: BeautifulSoup) -> Optional[Dict]:
    """
    Find the company information for a specific job link
    
    Args:
        job_link: The job link element
        soup: Full page soup
        
    Returns:
        Dictionary with company info or None
    """
    # Strategy 1: Look for company info in the same container as the job
    container = job_link
    for _ in range(10):  # Go up the DOM tree
        parent = container.parent
        if parent and parent.name == 'div':
            # Look for company links in this container
            company_links = parent.find_all('a', href=re.compile(r'/company/'))
            for company_link in company_links:
                # Check if this company link has text content
                text_content = company_link.get_text().strip()
                if text_content:
                    return {'name': text_content}
                
                # Also check if it has an h2 with text inside
                h2_elem = company_link.find('h2')
                if h2_elem and h2_elem.get_text().strip():
                    return {'name': h2_elem.get_text().strip()}
                    
            # If we found company links but no text, we might be in a company section
            # Look for any h2 with company-like classes
            company_headers = parent.find_all('h2', class_=re.compile(r'font-semibold|company', re.I))
            for header in company_headers:
                text = header.get_text().strip()
                if text and len(text) < 100:  # Reasonable company name length
                    return {'name': text}
        
        container = parent
        if not parent:
            break
    
    return None


def find_job_details_near_link(job_link) -> Dict:
    """
    Find job details (location, type, etc.) near a specific job link
    
    Args:
        job_link: The job link element
        
    Returns:
        Dictionary with job details
    """
    details = {}
    
    # Look in the immediate container around the job link
    container = job_link.parent
    for _ in range(5):  # Don't go too far up
        if not container:
            break
            
        # Look for location indicators
        location_spans = container.find_all('span', string=re.compile(r'Porto|Lisbon|Remote|Europe|Berlin|Madrid|Barcelona', re.I))
        if location_spans:
            details['location'] = location_spans[0].get_text().strip()
        elif not details.get('location'):
            # Alternative location search
            pl1_spans = container.find_all('span', class_='pl-1')
            for span in pl1_spans:
                text = span.get_text().strip()
                if any(word in text.lower() for word in ['porto', 'lisbon', 'remote', 'europe', 'berlin', 'madrid']):
                    details['location'] = text
                    break
        
        # Look for job type indicators
        if not details.get('job_type'):
            job_type_spans = container.find_all('span', class_=re.compile(r'accent-yellow|bg-accent', re.I))
            for span in job_type_spans:
                text = span.get_text().strip()
                if text.lower() in ['full-time', 'part-time', 'contract', 'internship']:
                    details['job_type'] = text
                    break
        
        container = container.parent
    
    return details


def parse_job_container(container, base_url: str) -> Optional[Dict]:
    """
    Parse individual job container from HTML
    
    Args:
        container: BeautifulSoup element containing job info
        base_url: Base URL for resolving links
        
    Returns:
        Job dictionary or None
    """
    try:
        # Look for job title link pattern: /jobs/XXXXXXX-job-title
        title_elem = container.find('a', href=re.compile(r'/jobs/\d+-'))
        if not title_elem:
            return None
        
        title = clean_text(title_elem.get_text())
        job_url = urljoin(base_url, title_elem['href'])
        
        # Find company name - look for company link that has text content
        company_elem = None
        company_links = container.find_all('a', href=re.compile(r'/company/'))
        
        for link in company_links:
            # Check if this link has text content (not just an image)
            text_content = link.get_text().strip()
            if text_content:
                company_elem = link
                break
            
            # Also check if it has an h2 with text inside
            h2_elem = link.find('h2')
            if h2_elem and h2_elem.get_text().strip():
                company_elem = h2_elem
                break
        
        if not company_elem:
            # Fallback to any h2 that might be company name
            company_elem = container.find(['h2'], class_=re.compile(r'font-semibold|company', re.I))
        
        # Find location - look for text near location icon or containing location words
        location_elem = container.find(['span'], string=re.compile(r'Porto|Lisbon|Remote|Europe', re.I))
        if not location_elem:
            # Look for spans with location text
            location_elem = container.find('span', class_='pl-1')
            
        # Find job type (Full-time, Part-time, etc.)
        job_type_elem = container.find('span', class_=re.compile(r'accent-yellow|bg-accent', re.I))
        
        job_data = {
            'title': title,
            'company': clean_text(company_elem.get_text()) if company_elem else None,
            'location': clean_text(location_elem.get_text()) if location_elem else None,
            'job_type': clean_text(job_type_elem.get_text()) if job_type_elem else None,
            'job_url': job_url,
            'site': 'wellfound'
        }
        
        # Only return if we have essential information
        if job_data['title'] and job_data['job_url']:
            return job_data
    
    except Exception as e:
        print(f"Error parsing job container: {e}")
    
    return None


def standardize_job_data(raw_job: Dict) -> Optional[Dict]:
    """
    Convert raw job data to standardized format
    
    Args:
        raw_job: Raw job data from JSON
        
    Returns:
        Standardized job dictionary
    """
    try:
        # Map common field names - this will need adjustment based on actual data structure
        field_mappings = {
            'title': ['title', 'jobTitle', 'name', 'position'],
            'company': ['company', 'companyName', 'startup', 'organization'],
            'location': ['location', 'city', 'region', 'area'],
            'description': ['description', 'summary', 'details'],
            'salary': ['salary', 'compensation', 'pay', 'wage'],
            'job_url': ['url', 'link', 'jobUrl', 'permalink']
        }
        
        standardized = {'site': 'wellfound'}
        
        for std_field, possible_fields in field_mappings.items():
            for field in possible_fields:
                if field in raw_job and raw_job[field]:
                    standardized[std_field] = clean_text(str(raw_job[field]))
                    break
        
        # Only return if we have essential information
        if standardized.get('title') or standardized.get('company'):
            return standardized
    
    except Exception as e:
        print(f"Error standardizing job data: {e}")
    
    return None


def clean_text(text: str) -> str:
    """
    Clean and normalize text content
    
    Args:
        text: Raw text to clean
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove extra whitespace and newlines
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove common prefixes/suffixes
    text = re.sub(r'^(job|position|role):\s*', '', text, flags=re.IGNORECASE)
    
    return text


def is_valid_job_data(job: Dict) -> bool:
    """
    Validate if job data is complete enough to be useful
    
    Args:
        job: Job dictionary
        
    Returns:
        True if job data is valid
    """
    # Must have at least title or company
    if not (job.get('title') or job.get('company')):
        return False
    
    # Title and company shouldn't be just whitespace
    title = job.get('title', '').strip()
    company = job.get('company', '').strip()
    
    if not title and not company:
        return False
    
    return True