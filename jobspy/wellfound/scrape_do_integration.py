#!/usr/bin/env python3
"""
Wellfound scraper integration using scrape.do API
"""
import requests
import urllib.parse
import time
from typing import Optional, List
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from jobspy.util import create_logger
from jobspy.wellfound.util import extract_jobs_from_html, normalize_job_title, normalize_location
from jobspy.wellfound.constant import SCRAPE_DO_TOKEN

log = create_logger("Wellfound-ScrapeDo")

class ScrapeDoWellfoundScraper:
    """Wellfound scraper using scrape.do API service"""
    
    def __init__(self, token: str = SCRAPE_DO_TOKEN):
        self.token = token
        self.base_url = "https://wellfound.com"
        self.api_base = "http://api.scrape.do/"
        
    def scrape_jobs(self, search_term: str, location: str, results_wanted: int = 25) -> List[dict]:
        """
        Scrape jobs from Wellfound using scrape.do
        
        Args:
            search_term: Job title/keywords to search for
            location: Location to search in 
            results_wanted: Maximum number of results to return
            
        Returns:
            List of job dictionaries
        """
        jobs = []
        
        # Try primary URL first
        primary_url = self._build_search_url(search_term, location)
        jobs = self._scrape_url(primary_url)
        
        if not jobs:
            log.info("Primary URL failed, trying alternatives...")
            jobs = self._try_alternative_urls(search_term, location)
        
        # Limit results
        return jobs[:results_wanted] if jobs else []
    
    def _build_search_url(self, search_term: str, location: str) -> str:
        """Build the Wellfound search URL"""
        normalized_term = normalize_job_title(search_term)
        normalized_location = normalize_location(location)
        
        # Primary pattern: /role/l/job-title/location
        return f"{self.base_url}/role/l/{normalized_term}/{normalized_location}"
    
    def _scrape_url(self, target_url: str) -> List[dict]:
        """
        Scrape a single URL using scrape.do
        
        Args:
            target_url: URL to scrape
            
        Returns:
            List of job dictionaries
        """
        try:
            log.info(f"Scraping URL with scrape.do: {target_url}")
            
            # Build scrape.do API URL exactly like the working curl command
            encoded_url = urllib.parse.quote(target_url)
            api_url = f"{self.api_base}?url={encoded_url}&token={self.token}&super=true&render=true"
            
            # Make request with minimal headers (like curl)
            response = requests.get(api_url, timeout=60)
            
            log.info(f"scrape.do response status: {response.status_code}")
            
            if response.status_code == 200:
                html_content = response.text
                log.info(f"Retrieved {len(html_content)} characters")
                
                # Check for actual job content (ignore challenge keywords - scrape.do bypasses them)
                if "results total" in html_content and ("Actively Hiring" in html_content or "company logo" in html_content):
                    log.info("✅ Found actual job listings page with scrape.do")
                    
                    # Note: Challenge scripts may still be present but scrape.do bypassed them
                    if any(keyword in html_content.lower() for keyword in ['datadome', 'captcha', 'challenge']):
                        log.info("Challenge scripts present but scrape.do successfully bypassed them")
                    
                    # Extract jobs using our parser
                    jobs = extract_jobs_from_html(html_content, self.base_url)
                    log.info(f"Extracted {len(jobs)} jobs from bypassed content")
                    return jobs
                else:
                    log.warning("Content doesn't appear to be job listings page")
                    # Save for debugging
                    with open(f"scrape_do_debug_{int(time.time())}.html", 'w', encoding='utf-8') as f:
                        f.write(html_content)
                    log.info("Saved content for debugging")
                    return []
                    
            elif response.status_code == 402:
                log.error("scrape.do credit exhausted (402 Payment Required)")
                return []
            elif response.status_code == 429:
                log.error("scrape.do rate limited (429 Too Many Requests)")
                return []
            else:
                log.error(f"scrape.do failed: {response.status_code} - {response.text[:200]}")
                return []
                
        except Exception as e:
            log.error(f"scrape.do request failed: {str(e)}")
            return []
    
    def _try_alternative_urls(self, search_term: str, location: str) -> List[dict]:
        """
        Try alternative URL patterns
        
        Args:
            search_term: Job search term
            location: Location to search in
            
        Returns:
            List of job dictionaries
        """
        normalized_term = normalize_job_title(search_term)
        
        # Alternative URL patterns based on what we know works
        alternatives = [
            f"{self.base_url}/role/l/{normalized_term}/europe",  # Europe fallback (this worked in curl)
            f"{self.base_url}/remote/{normalized_term}-jobs",     # Remote jobs
            f"{self.base_url}/role/{normalized_term}",            # General role search
        ]
        
        for alt_url in alternatives:
            log.info(f"Trying alternative URL: {alt_url}")
            jobs = self._scrape_url(alt_url)
            if jobs:
                return jobs
            
            # Brief delay between attempts
            time.sleep(2)
        
        return []

def test_scrape_do_integration():
    """Test the scrape.do integration"""
    print("Testing scrape.do Wellfound integration...")
    
    scraper = ScrapeDoWellfoundScraper()
    
    # Test with Product Manager in Europe (we know this works from curl)
    jobs = scraper.scrape_jobs("Product Manager", "Europe", results_wanted=5)
    
    print(f"Found {len(jobs)} jobs")
    
    if jobs:
        print("\\nSample jobs:")
        for i, job in enumerate(jobs[:3]):
            print(f"  {i+1}. {job.get('title', 'N/A')} at {job.get('company', 'N/A')}")
            print(f"     Location: {job.get('location', 'N/A')}")
            print(f"     URL: {job.get('job_url', 'N/A')}")
        return True
    else:
        print("No jobs found")
        return False

if __name__ == "__main__":
    success = test_scrape_do_integration()
    print(f"\\nIntegration test: {'✅ SUCCESS' if success else '❌ FAILED'}")