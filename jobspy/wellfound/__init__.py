"""
Wellfound scraper for JobSpy using scrape.do API to bypass DataDome protection
"""

import time
from datetime import datetime
from typing import Optional
import requests
import urllib.parse
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
)
from jobspy.util import create_logger
from .constant import headers, REQUEST_CONFIG, SCRAPE_DO_TOKEN
from .util import (
    build_search_url,
    extract_jobs_from_html,
    normalize_job_title,
    normalize_location,
    is_valid_job_data
)

log = create_logger("Wellfound")


class WellfoundScraper(Scraper):
    base_url = "https://wellfound.com"
    delay = REQUEST_CONFIG["delay_between_requests"]
    
    def __init__(
        self, 
        proxies: list[str] | str | None = None, 
        ca_cert: str | None = None, 
        user_agent: str | None = None
    ):
        """
        Initialize WellfoundScraper with scrape.do API integration
        """
        super().__init__(Site.WELLFOUND, proxies=proxies, ca_cert=ca_cert)
        
        self.user_agent = user_agent or headers["User-Agent"]
    
    def scrape(self, scraper_input: ScraperInput) -> JobResponse:
        """
        Scrape job listings from Wellfound using scrape.do API
        
        Args:
            scraper_input: Input parameters for scraping
            
        Returns:
            JobResponse with job listings
        """
        log.info(f"Starting Wellfound scrape for '{scraper_input.search_term}' in '{scraper_input.location}'")
        
        jobs = []
        
        try:
            # Use scrape.do API only (bypasses DataDome)
            log.info("Scraping Wellfound with scrape.do API...")
            jobs = self._scrape_with_scrape_do(scraper_input)
            
            if jobs:
                log.info(f"Successfully scraped {len(jobs)} jobs from Wellfound using scrape.do")
            else:
                log.info("No jobs found with scrape.do")
                
        except Exception as e:
            log.error(f"Error scraping Wellfound: {str(e)}")
            
        return JobResponse(jobs=jobs)
    
    def _scrape_with_scrape_do(self, scraper_input: ScraperInput) -> list[JobPost]:
        """
        Scrape using scrape.do API service (primary method)
        
        Args:
            scraper_input: Input parameters for scraping
            
        Returns:
            List of JobPost objects
        """
        try:
            # Build search URL
            search_url = build_search_url(
                self.base_url,
                scraper_input.search_term,
                scraper_input.location
            )
            
            log.info(f"scrape.do URL: {search_url}")
            
            # Try primary URL first
            jobs = self._scrape_url_with_scrape_do(search_url)
            
            if not jobs:
                log.info("Primary URL failed, trying scrape.do alternatives...")
                jobs = self._try_scrape_do_alternatives(scraper_input)
            
            if jobs:
                # Convert to JobPost objects
                return self._convert_to_job_posts(
                    jobs, 
                    scraper_input.results_wanted,
                    scraper_input.description_format
                )
            
            return []
                
        except Exception as e:
            log.error(f"scrape.do request failed: {str(e)}")
            return []
    
    def _scrape_url_with_scrape_do(self, target_url: str, max_pages: int = None) -> list[dict]:
        """
        Scrape all available pages from a URL using scrape.do API
        
        Args:
            target_url: Base URL to scrape (without page parameter)
            max_pages: Maximum number of pages to scrape (None = auto-detect all pages)
            
        Returns:
            List of raw job dictionaries from all pages
        """
        all_jobs = []
        total_pages_detected = None
        
        # Start with page 1 to detect total pages
        page_num = 1
        
        while True:
            try:
                # Build URL for this page
                if page_num == 1:
                    page_url = target_url
                else:
                    # Add page parameter
                    separator = "&" if "?" in target_url else "?"
                    page_url = f"{target_url}{separator}page={page_num}"
                
                log.info(f"Scraping page {page_num}: {page_url}")
                
                # Build scrape.do API URL
                encoded_url = urllib.parse.quote(page_url)
                api_url = f"http://api.scrape.do/?url={encoded_url}&token={SCRAPE_DO_TOKEN}&super=true&render=true"
                
                # Make request
                response = requests.get(api_url, timeout=60)
                
                if response.status_code == 200:
                    html_content = response.text
                    log.info(f"Page {page_num}: Retrieved {len(html_content)} characters")
                    
                    # Check for actual job content
                    if "results total" in html_content and ("Actively Hiring" in html_content or "company logo" in html_content):
                        log.info(f"✅ Page {page_num}: Found job listings")
                        
                        # Extract pagination info on first page to know total
                        page_info = self._extract_pagination_info(html_content)
                        current_page = page_info.get('current_page', page_num)
                        detected_total = page_info.get('total_pages', 1)
                        
                        # Set total pages on first detection
                        if total_pages_detected is None:
                            total_pages_detected = detected_total
                            log.info(f"🔍 Detected {total_pages_detected} total pages to scrape")
                        
                        log.info(f"📄 Page {current_page} of {total_pages_detected}")
                        
                        # Extract jobs using existing parser
                        page_jobs = extract_jobs_from_html(html_content, self.base_url)
                        log.info(f"Page {page_num}: Parsed {len(page_jobs)} jobs")
                        
                        all_jobs.extend(page_jobs)
                        
                        # Check stopping conditions
                        if len(page_jobs) == 0:
                            log.info(f"No jobs found on page {page_num}, stopping")
                            break
                        
                        if current_page >= total_pages_detected:
                            log.info(f"✅ Completed all {total_pages_detected} pages")
                            break
                            
                        # Respect max_pages limit if specified
                        if max_pages and page_num >= max_pages:
                            log.info(f"Reached max_pages limit of {max_pages}")
                            break
                        
                        # Brief delay between pages to be respectful
                        time.sleep(2)
                        page_num += 1
                            
                    else:
                        log.warning(f"Page {page_num}: No job content found")
                        break  # Stop if no jobs on this page
                        
                elif response.status_code == 402:
                    log.error("scrape.do credit exhausted (402 Payment Required)")
                    break
                elif response.status_code == 429:
                    log.error("scrape.do rate limited (429 Too Many Requests)")
                    break
                else:
                    log.error(f"Page {page_num} failed: {response.status_code} - {response.text[:200]}")
                    break  # Stop on errors
                    
            except Exception as e:
                log.error(f"Page {page_num} request failed: {str(e)}")
                break  # Stop on exceptions
        
        final_page_count = page_num if total_pages_detected else page_num - 1
        log.info(f"🏁 Total jobs collected from {final_page_count} pages: {len(all_jobs)}")
        return all_jobs
    
    def _extract_pagination_info(self, html_content: str) -> dict:
        """
        Extract pagination information from HTML content
        
        Args:
            html_content: HTML content to parse
            
        Returns:
            Dictionary with current_page and total_pages
        """
        try:
            # Look for the specific Wellfound pagination pattern:
            # <h4 class="styles_resultCount__Biln8">Page <!-- -->2<!-- --> of <!-- -->2</h4>
            import re
            
            # Pattern to match the HTML structure with comments
            page_pattern = r'class="styles_resultCount__Biln8">Page\s*<!--[^>]*-->\s*(\d+)\s*<!--[^>]*-->\s*of\s*<!--[^>]*-->\s*(\d+)\s*</h4>'
            match = re.search(page_pattern, html_content)
            
            if match:
                current_page = int(match.group(1))
                total_pages = int(match.group(2))
                log.info(f"📊 Extracted pagination: Page {current_page} of {total_pages}")
                return {'current_page': current_page, 'total_pages': total_pages}
            
            # Fallback: simpler pattern without HTML tags
            simple_pattern = r'Page\s+(\d+)\s+of\s+(\d+)'
            simple_match = re.search(simple_pattern, html_content)
            
            if simple_match:
                current_page = int(simple_match.group(1))
                total_pages = int(simple_match.group(2))
                log.info(f"📊 Extracted pagination (simple): Page {current_page} of {total_pages}")
                return {'current_page': current_page, 'total_pages': total_pages}
            
            # Another fallback: look for result count patterns to estimate pages
            result_pattern = r'(\d+)\s+results\s+total'
            result_match = re.search(result_pattern, html_content)
            
            if result_match:
                total_results = int(result_match.group(1))
                # Estimate pages (assuming ~25 results per page based on what we've seen)
                estimated_pages = max(1, (total_results + 24) // 25)
                log.info(f"📊 Estimated pagination from {total_results} results: ~{estimated_pages} pages")
                return {'current_page': 1, 'total_pages': estimated_pages}
            
            log.warning("Could not find pagination information in HTML")
            
        except Exception as e:
            log.warning(f"Error extracting pagination info: {str(e)}")
        
        return {'current_page': 1, 'total_pages': 1}
    
    def _try_scrape_do_alternatives(self, scraper_input: ScraperInput) -> list[dict]:
        """
        Try alternative URL patterns with scrape.do
        
        Args:
            scraper_input: Input parameters for scraping
            
        Returns:
            List of raw job dictionaries
        """
        normalized_term = normalize_job_title(scraper_input.search_term)
        
        # Alternative URL patterns based on what works
        alternatives = [
            f"{self.base_url}/role/l/{normalized_term}/europe",  # Europe fallback (known to work)
            f"{self.base_url}/remote/{normalized_term}-jobs",     # Remote jobs
            f"{self.base_url}/role/{normalized_term}",            # General role search
        ]
        
        for alt_url in alternatives:
            log.info(f"Trying scrape.do alternative: {alt_url}")
            jobs = self._scrape_url_with_scrape_do(alt_url, max_pages=3)  # Limit alternatives to avoid excessive requests
            if jobs:
                return jobs
            
            # Brief delay between attempts
            time.sleep(2)
        
        return []
    
    
    def _convert_to_job_posts(
        self, 
        raw_jobs: list[dict], 
        results_wanted: int,
        description_format: DescriptionFormat
    ) -> list[JobPost]:
        """
        Convert raw job data to JobPost objects
        
        Args:
            raw_jobs: List of raw job dictionaries
            results_wanted: Maximum number of jobs to return
            description_format: Format for job description
            
        Returns:
            List of JobPost objects
        """
        jobs = []
        
        for raw_job in raw_jobs[:results_wanted]:
            try:
                if not is_valid_job_data(raw_job):
                    continue
                
                # Create Location object
                location = None
                if raw_job.get('location'):
                    location = Location(
                        city=raw_job['location'],
                        state=None,
                        country=None
                    )
                
                # Parse compensation if available
                compensation = None
                if raw_job.get('salary'):
                    compensation = self._parse_compensation(raw_job['salary'])
                
                # Create JobPost
                job_post = JobPost(
                    title=raw_job.get('title', 'N/A'),
                    company_name=raw_job.get('company', 'N/A'),
                    location=location,
                    job_type=None,  # Wellfound doesn't typically specify job type in listings
                    date_posted=self._get_current_date(),
                    job_url=raw_job.get('job_url'),
                    job_url_direct=raw_job.get('job_url'),  # Same as job_url for Wellfound
                    description=raw_job.get('description', ''),
                    compensation=compensation,
                    emails=None,  # Not typically available in listings
                    is_remote=self._is_remote_job(raw_job),
                )
                
                jobs.append(job_post)
                
            except Exception as e:
                log.error(f"Error converting job to JobPost: {str(e)}")
                continue
        
        return jobs
    
    def _parse_compensation(self, salary_text: str) -> Optional[Compensation]:
        """
        Parse salary text into Compensation object
        
        Args:
            salary_text: Raw salary text
            
        Returns:
            Compensation object or None
        """
        if not salary_text:
            return None
        
        try:
            # Basic parsing - this could be enhanced
            # Look for patterns like "$50k - $80k", "€40,000 - €60,000", etc.
            import re
            
            # Remove common prefixes
            salary_text = re.sub(r'^\$?salary:?\s*', '', salary_text, flags=re.IGNORECASE)
            
            # Look for range pattern
            range_match = re.search(r'[\$€£]?([\d,]+)k?\s*-\s*[\$€£]?([\d,]+)k?', salary_text)
            if range_match:
                min_amount = int(re.sub(r'[^\d]', '', range_match.group(1)))
                max_amount = int(re.sub(r'[^\d]', '', range_match.group(2)))
                
                # Handle 'k' notation
                if 'k' in salary_text.lower():
                    min_amount *= 1000
                    max_amount *= 1000
                
                # Determine currency
                currency = 'USD'  # Default
                if '€' in salary_text:
                    currency = 'EUR'
                elif '£' in salary_text:
                    currency = 'GBP'
                
                return Compensation(
                    min_amount=min_amount,
                    max_amount=max_amount,
                    currency=currency,
                    interval="yearly"  # Wellfound typically shows annual salaries
                )
        
        except Exception as e:
            log.warning(f"Error parsing compensation '{salary_text}': {str(e)}")
        
        return None
    
    def _is_remote_job(self, job_data: dict) -> bool:
        """
        Determine if a job is remote based on available data
        
        Args:
            job_data: Job data dictionary
            
        Returns:
            True if job appears to be remote
        """
        location = (job_data.get('location') or '').lower()
        title = (job_data.get('title') or '').lower()
        description = (job_data.get('description') or '').lower()
        
        remote_keywords = ['remote', 'anywhere', 'worldwide', 'distributed']
        
        return any(keyword in location or keyword in title or keyword in description 
                  for keyword in remote_keywords)
    
    def _get_current_date(self) -> datetime:
        """
        Get current date for job posting (date only, no time)
        
        Returns:
            Current date with time set to 00:00:00
        """
        return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)