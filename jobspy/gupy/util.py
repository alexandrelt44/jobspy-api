"""
Utility functions for Gupy scraper
"""

import re
from typing import Optional, List, Dict, Any
from urllib.parse import urlencode, quote
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

from jobspy.model import JobPost, Location, Compensation, JobType
from .constant import API_SEARCH_URL


def build_api_url(search_term: str, location: str = None, limit: int = 20, offset: int = 0, **kwargs) -> str:
    """
    Build API URL for Gupy.io job search

    Args:
        search_term: Job search term (jobName parameter)
        location: Location to search in
        limit: Number of results per request (default 20)
        offset: Offset for pagination (default 0)
        **kwargs: Additional search parameters

    Returns:
        Complete API URL
    """
    params = []

    # Required jobName parameter
    if search_term:
        params.append(f"jobName={quote(search_term)}")

    # Pagination parameters
    params.append(f"limit={limit}")
    params.append(f"offset={offset}")

    # Note: Location filtering appears to be done client-side
    # The API doesn't seem to support location parameter
    # Location filtering will be handled during post-processing

    # Add other filters if provided
    for key, value in kwargs.items():
        if value is not None:
            if isinstance(value, list):
                for item in value:
                    params.append(f"{key}[]={quote(str(item))}")
            else:
                params.append(f"{key}={quote(str(value))}")

    if params:
        return f"{API_SEARCH_URL}?" + "&".join(params)
    else:
        return API_SEARCH_URL


def parse_api_response(api_response: dict) -> List[Dict[str, Any]]:
    """
    Parse API response from Gupy job search endpoint

    Args:
        api_response: JSON response from Gupy API

    Returns:
        List of job dictionaries with extracted data
    """
    jobs = []

    if not api_response or 'data' not in api_response:
        return jobs

    for job_data in api_response['data']:
        try:
            # Extract basic job information
            job = {
                'id': job_data.get('id'),
                'title': job_data.get('name', '').strip(),
                'company': job_data.get('careerPageName', '').strip(),
                'company_logo': job_data.get('careerPageLogo'),
                'company_url': job_data.get('careerPageUrl'),
                'description': job_data.get('description', '').strip(),
                'job_url': job_data.get('jobUrl'),
                'date_posted': job_data.get('publishedDate'),
                'application_deadline': job_data.get('applicationDeadline'),
                'is_remote': job_data.get('isRemoteWork', False),
                'workplace_type': job_data.get('workplaceType'),
                'city': job_data.get('city', '').strip(),
                'state': job_data.get('state', '').strip(),
                'country': job_data.get('country', '').strip(),
                'job_type': job_data.get('type'),
                'disabilities_support': job_data.get('disabilities', False),
                'skills': job_data.get('skills', []),
                'badges': job_data.get('badges', {}),
            }

            # Only add valid jobs
            if job['title'] and (job['company'] or job['job_url']):
                jobs.append(job)

        except Exception as e:
            # Skip malformed job entries
            continue

    return jobs


def extract_jobs_from_html(html_content: str) -> List[Dict[str, Any]]:
    """
    Extract job data from Gupy HTML content

    Args:
        html_content: Raw HTML content from job search page

    Returns:
        List of job dictionaries with extracted data
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    jobs = []

    # Look for job listing containers
    # This will need to be updated based on actual HTML structure
    job_elements = soup.find_all(['div', 'article', 'section'],
                                class_=re.compile(r'job|vaga|position', re.I))

    if not job_elements:
        # Try alternative selectors
        job_elements = soup.find_all('div', attrs={'data-testid': re.compile(r'job|position', re.I)})

    for job_element in job_elements:
        try:
            job_data = extract_job_data(job_element)
            if job_data and is_valid_job_data(job_data):
                jobs.append(job_data)
        except Exception as e:
            continue

    return jobs


def extract_job_data(job_element) -> Optional[Dict[str, Any]]:
    """
    Extract individual job data from a job element

    Args:
        job_element: BeautifulSoup element containing job data

    Returns:
        Dictionary with job data or None if extraction fails
    """
    try:
        # Extract title
        title_element = job_element.find(['h1', 'h2', 'h3', 'h4'],
                                       class_=re.compile(r'title|titulo|cargo', re.I))
        if not title_element:
            title_element = job_element.find(['a'],
                                           class_=re.compile(r'job|vaga|position', re.I))

        title = title_element.get_text(strip=True) if title_element else None

        # Extract company name
        company_element = job_element.find(['span', 'div', 'p'],
                                         class_=re.compile(r'company|empresa|empregador', re.I))
        company = company_element.get_text(strip=True) if company_element else None

        # Extract location
        location_element = job_element.find(['span', 'div', 'p'],
                                          class_=re.compile(r'location|local|cidade', re.I))
        location_text = location_element.get_text(strip=True) if location_element else None

        # Extract job URL
        link_element = job_element.find('a', href=True)
        job_url = link_element['href'] if link_element else None
        if job_url and job_url.startswith('/'):
            job_url = f"https://portal.gupy.io{job_url}"

        # Extract work type/model
        work_type_element = job_element.find(['span', 'div'],
                                           class_=re.compile(r'remote|presencial|hibrido|work', re.I))
        work_type = work_type_element.get_text(strip=True) if work_type_element else None

        # Extract date posted (if available)
        date_element = job_element.find(['span', 'time'],
                                      class_=re.compile(r'date|data|tempo', re.I))
        date_text = date_element.get_text(strip=True) if date_element else None

        return {
            'title': title,
            'company': company,
            'location': location_text,
            'job_url': job_url,
            'work_type': work_type,
            'date_posted': parse_date(date_text) if date_text else None,
        }

    except Exception as e:
        return None


def parse_location(location_text: str) -> Location:
    """
    Parse location string into Location object

    Args:
        location_text: Raw location string from job posting

    Returns:
        Location object with parsed components
    """
    if not location_text:
        return Location()

    # Common Brazilian location patterns
    location_text = location_text.strip()

    # Handle "City, State" format
    if ',' in location_text:
        parts = [part.strip() for part in location_text.split(',')]
        if len(parts) >= 2:
            return Location(
                city=parts[0],
                state=parts[1],
                country="Brazil"
            )

    # Handle "City - State" format
    if ' - ' in location_text:
        parts = [part.strip() for part in location_text.split(' - ')]
        if len(parts) >= 2:
            return Location(
                city=parts[0],
                state=parts[1],
                country="Brazil"
            )

    # Single location (could be city or state)
    return Location(
        city=location_text,
        country="Brazil"
    )


def parse_date(date_text: str) -> Optional[str]:
    """
    Parse date from Brazilian Portuguese text

    Args:
        date_text: Date text in Portuguese

    Returns:
        ISO date string or None
    """
    if not date_text:
        return None

    date_text = date_text.lower().strip()
    today = datetime.now()

    # Handle relative dates in Portuguese
    if 'hoje' in date_text or 'agora' in date_text:
        return today.strftime('%Y-%m-%d')
    elif 'ontem' in date_text:
        return (today - timedelta(days=1)).strftime('%Y-%m-%d')
    elif 'dias' in date_text:
        # Extract number of days
        match = re.search(r'(\d+)\s*dias?', date_text)
        if match:
            days = int(match.group(1))
            return (today - timedelta(days=days)).strftime('%Y-%m-%d')
    elif 'semana' in date_text:
        # Extract number of weeks
        match = re.search(r'(\d+)\s*semanas?', date_text)
        if match:
            weeks = int(match.group(1))
            return (today - timedelta(weeks=weeks)).strftime('%Y-%m-%d')
        else:
            # Just "semana passada" (last week)
            return (today - timedelta(weeks=1)).strftime('%Y-%m-%d')

    return None


def extract_job_type(work_type_text: str) -> Optional[JobType]:
    """
    Extract job type from work type text

    Args:
        work_type_text: Text describing work arrangement

    Returns:
        JobType enum value or None
    """
    if not work_type_text:
        return None

    work_type_text = work_type_text.lower()

    # Map Portuguese terms to JobType
    if any(term in work_type_text for term in ['tempo integral', 'full time', 'clt']):
        return JobType.FULL_TIME
    elif any(term in work_type_text for term in ['meio período', 'part time', 'parcial']):
        return JobType.PART_TIME
    elif any(term in work_type_text for term in ['estágio', 'estagiário', 'internship']):
        return JobType.INTERNSHIP
    elif any(term in work_type_text for term in ['freelancer', 'autônomo', 'contractor']):
        return JobType.CONTRACT
    elif any(term in work_type_text for term in ['temporário', 'temporary']):
        return JobType.TEMPORARY

    return None


def is_remote_job(job_data: Dict[str, Any]) -> bool:
    """
    Determine if job is remote based on job data

    Args:
        job_data: Dictionary containing job information

    Returns:
        True if job appears to be remote
    """
    location = job_data.get('location', '').lower()
    work_type = job_data.get('work_type', '').lower()
    title = job_data.get('title', '').lower()

    remote_indicators = [
        'remoto', 'remote', 'home office', 'trabalho remoto',
        'à distância', 'anywhere', 'qualquer lugar'
    ]

    for indicator in remote_indicators:
        if indicator in location or indicator in work_type or indicator in title:
            return True

    return False


def is_valid_job_data(job_data: Dict[str, Any]) -> bool:
    """
    Validate if job data contains minimum required information

    Args:
        job_data: Dictionary containing job information

    Returns:
        True if job data is valid for processing
    """
    # Must have at least title and company or job URL
    has_title = job_data.get('title') and len(job_data['title'].strip()) > 0
    has_company = job_data.get('company') and len(job_data['company'].strip()) > 0
    has_url = job_data.get('job_url') and len(job_data['job_url'].strip()) > 0

    return has_title and (has_company or has_url)


def normalize_job_title(title: str) -> str:
    """
    Normalize job title text

    Args:
        title: Raw job title

    Returns:
        Cleaned and normalized title
    """
    if not title:
        return ""

    # Remove extra whitespace and normalize
    title = re.sub(r'\s+', ' ', title.strip())

    # Remove common prefixes/suffixes that might be noise
    title = re.sub(r'^(vaga:?|job:?|position:?)\s*', '', title, flags=re.I)
    title = re.sub(r'\s*(- vaga|job|position)\s*$', '', title, flags=re.I)

    return title.strip()


def normalize_company_name(company: str) -> str:
    """
    Normalize company name

    Args:
        company: Raw company name

    Returns:
        Cleaned company name
    """
    if not company:
        return ""

    # Remove extra whitespace
    company = re.sub(r'\s+', ' ', company.strip())

    # Remove common suffixes
    company = re.sub(r'\s*(ltda\.?|ltd\.?|inc\.?|corp\.?|s\.?a\.?)$', '', company, flags=re.I)

    return company.strip()