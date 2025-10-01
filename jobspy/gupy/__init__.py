"""
Gupy.io scraper for JobSpy
"""

import time
from datetime import datetime
from typing import Optional, List
import requests
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from jobspy.model import (
    JobPost,
    Location,
    JobResponse,
    Compensation,
    DescriptionFormat,
    Scraper,
    ScraperInput,
    Site,
    JobType,
)
from jobspy.util import create_logger, create_session, markdown_converter, extract_emails_from_text
from .constant import headers, REQUEST_CONFIG, BASE_URL
from .util import (
    build_api_url,
    parse_api_response,
    parse_location,
    extract_job_type,
    is_remote_job,
    normalize_job_title,
    normalize_company_name,
)

log = create_logger("Gupy")


class GupyScraper(Scraper):
    base_url = BASE_URL
    delay = REQUEST_CONFIG["delay_between_requests"]

    def __init__(
        self,
        proxies: list[str] | str | None = None,
        ca_cert: str | None = None,
        user_agent: str | None = None
    ):
        """
        Initialize GupyScraper with proxy support
        """
        super().__init__(Site.GUPY, proxies=proxies, ca_cert=ca_cert)

        self.session = create_session(
            proxies=self.proxies,
            ca_cert=ca_cert,
            is_tls=False
        )
        self.session.headers.update(headers)

        if user_agent:
            self.session.headers["User-Agent"] = user_agent

        self.scraper_input = None
        self.seen_urls = set()

    def scrape(self, scraper_input: ScraperInput) -> JobResponse:
        """
        Scrape Gupy for jobs with scraper_input criteria

        Args:
            scraper_input: ScraperInput object with search parameters

        Returns:
            JobResponse with found jobs
        """
        self.scraper_input = scraper_input
        log.info(f"Starting Gupy scrape for: {scraper_input.search_term}")

        job_list = []
        offset = 0
        limit = min(50, scraper_input.results_wanted)  # API supports up to 50 per request
        max_requests = 10  # Reasonable limit to prevent infinite loops

        request_count = 0
        while len(job_list) < scraper_input.results_wanted and request_count < max_requests:
            log.info(f"Scraping offset {offset}, limit {limit}")

            try:
                page_jobs = self._scrape_api_page(offset, limit)
                if not page_jobs:
                    log.info(f"No jobs found at offset {offset}, stopping")
                    break

                job_list.extend(page_jobs)
                offset += limit
                request_count += 1

                # Add delay between requests
                if request_count < max_requests:
                    time.sleep(self.delay)

            except Exception as e:
                log.error(f"Error scraping offset {offset}: {str(e)}")
                break

        # Limit results to requested amount
        final_jobs = job_list[:scraper_input.results_wanted]

        log.info(f"Found {len(final_jobs)} jobs")
        return JobResponse(jobs=final_jobs)

    def _scrape_api_page(self, offset: int, limit: int) -> List[JobPost]:
        """
        Scrape jobs using Gupy API endpoint

        Args:
            offset: Starting position for results
            limit: Number of results to fetch

        Returns:
            List of JobPost objects from this request
        """
        api_url = build_api_url(
            search_term=self.scraper_input.search_term,
            location=self.scraper_input.location,
            offset=offset,
            limit=limit
        )

        log.debug(f"Requesting API URL: {api_url}")

        try:
            # Use JSON headers for API request
            api_headers = self.session.headers.copy()
            api_headers.update({
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            })

            response = self.session.get(api_url, headers=api_headers, timeout=30)
            response.raise_for_status()

            # Parse JSON response
            api_data = response.json()
            log.debug(f"API returned {len(api_data.get('data', []))} jobs")

        except requests.exceptions.RequestException as e:
            log.error(f"API request failed for offset {offset}: {str(e)}")
            return []
        except ValueError as e:
            log.error(f"Failed to parse JSON response: {str(e)}")
            return []

        # Parse API response
        try:
            raw_jobs = parse_api_response(api_data)
            log.debug(f"Parsed {len(raw_jobs)} jobs from API response")

            jobs = []
            for raw_job in raw_jobs:
                processed_job = self._process_api_job(raw_job)
                if processed_job and self._matches_location_filter(processed_job):
                    jobs.append(processed_job)

            return jobs

        except Exception as e:
            log.error(f"Error processing API jobs: {str(e)}")
            return []

    def _process_api_job(self, job_data: dict) -> Optional[JobPost]:
        """
        Process job data from API response into JobPost object

        Args:
            job_data: Dictionary with job data from API

        Returns:
            JobPost object or None if processing fails
        """
        try:
            job_url = job_data.get('job_url')
            if not job_url:
                return None

            # Skip duplicates
            if job_url in self.seen_urls:
                return None
            self.seen_urls.add(job_url)

            # Extract and clean basic data
            title = normalize_job_title(job_data.get('title', ''))
            company = normalize_company_name(job_data.get('company', ''))

            if not title:
                return None

            # Build location
            city = job_data.get('city', '')
            state = job_data.get('state', '')
            country = job_data.get('country', 'Brasil')

            location = Location(
                city=city if city else None,
                state=state if state else None,
                country=country
            )

            # Parse date
            date_posted = None
            if job_data.get('date_posted'):
                try:
                    # Parse ISO format: "2025-09-17T20:27:39.086Z"
                    dt = datetime.fromisoformat(job_data['date_posted'].replace('Z', '+00:00'))
                    date_posted = dt.strftime('%Y-%m-%d')
                except:
                    pass

            # Determine job type and remote status
            is_remote = job_data.get('is_remote', False)
            workplace_type = job_data.get('workplace_type', '')

            # Map workplace type to is_remote
            if workplace_type in ['remote', 'remoto']:
                is_remote = True

            # Extract job type from workplace_type or job_type
            job_type = None
            if workplace_type in ['hybrid', 'hibrido']:
                # Not a standard JobType, but we can infer full-time
                job_type = JobType.FULL_TIME
            elif job_data.get('job_type') == 'vacancy_type_effective':
                job_type = JobType.FULL_TIME

            # Get description
            description = job_data.get('description', '')

            # Convert to markdown if requested
            if description and self.scraper_input.description_format == DescriptionFormat.MARKDOWN:
                description = markdown_converter(description)

            # Create unique ID
            job_id = f"gupy-{job_data.get('id', hash(job_url) % 1000000)}"

            return JobPost(
                id=job_id,
                title=title,
                company_name=company if company else None,
                location=location,
                job_type=[job_type] if job_type else None,
                job_url=job_url,
                job_url_direct=job_data.get('company_url'),
                description=description,
                date_posted=date_posted,
                is_remote=is_remote,
                emails=extract_emails_from_text(description) if description else None,
                site=Site.GUPY,
                company_logo=job_data.get('company_logo'),
            )

        except Exception as e:
            log.error(f"Error processing API job: {str(e)}")
            return None

    def _matches_location_filter(self, job: JobPost) -> bool:
        """
        Check if job matches the location filter

        Args:
            job: JobPost object to check

        Returns:
            True if job matches location filter or no filter specified
        """
        if not self.scraper_input.location:
            return True

        search_location = self.scraper_input.location.lower()

        # Special handling for broad country searches
        if search_location in ['brasil', 'brazil']:
            # For Brazil searches, accept all jobs in Brazil (which is default for Gupy)
            return True

        # Check city
        if job.location and job.location.city:
            if search_location in job.location.city.lower():
                return True

        # Check state
        if job.location and job.location.state:
            if search_location in job.location.state.lower():
                return True

        # Check combined location string
        if job.location:
            location_str = f"{job.location.city or ''} {job.location.state or ''}".strip().lower()
            if search_location in location_str:
                return True

        return False

    def _process_job(self, job_data: dict) -> Optional[JobPost]:
        """
        Process raw job data into JobPost object

        Args:
            job_data: Dictionary with raw job data

        Returns:
            JobPost object or None if processing fails
        """
        try:
            job_url = job_data.get('job_url')
            if not job_url:
                return None

            # Skip duplicates
            if job_url in self.seen_urls:
                return None
            self.seen_urls.add(job_url)

            # Extract and clean basic data
            title = normalize_job_title(job_data.get('title', ''))
            company = normalize_company_name(job_data.get('company', ''))

            if not title:
                return None

            # Parse location
            location = parse_location(job_data.get('location', ''))

            # Extract job type
            job_type = extract_job_type(job_data.get('work_type', ''))

            # Check if remote
            is_remote = is_remote_job(job_data)

            # Get description if job URL is available
            description = self._fetch_job_description(job_url)

            # Create unique ID
            job_id = f"gupy-{hash(job_url) % 1000000}"

            return JobPost(
                id=job_id,
                title=title,
                company_name=company if company else None,
                location=location,
                job_type=job_type,
                job_url=job_url,
                description=description,
                date_posted=job_data.get('date_posted'),
                is_remote=is_remote,
                emails=extract_emails_from_text(description) if description else None,
                site=Site.GUPY,
            )

        except Exception as e:
            log.error(f"Error processing job: {str(e)}")
            return None

    def _fetch_job_description(self, job_url: str) -> Optional[str]:
        """
        Fetch detailed job description from job URL

        Args:
            job_url: URL of the job posting

        Returns:
            Job description text or None if fetch fails
        """
        if not job_url:
            return None

        try:
            # Add delay to avoid rate limiting
            time.sleep(1)

            response = self.session.get(job_url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Look for description content
            description_selectors = [
                {'class_': lambda x: x and any(term in x.lower() for term in ['description', 'descricao', 'desc'])},
                {'class_': lambda x: x and any(term in x.lower() for term in ['content', 'conteudo', 'body'])},
                {'id': lambda x: x and any(term in x.lower() for term in ['description', 'descricao', 'content'])},
            ]

            description_element = None
            for selector in description_selectors:
                description_element = soup.find(['div', 'section', 'article'], selector)
                if description_element:
                    break

            if description_element:
                # Clean up the description
                description = description_element.get_text(separator='\n', strip=True)

                # Convert to markdown if requested
                if self.scraper_input.description_format == DescriptionFormat.MARKDOWN:
                    description = markdown_converter(description)

                return description

        except Exception as e:
            log.debug(f"Could not fetch description from {job_url}: {str(e)}")

        return None