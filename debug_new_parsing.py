#!/usr/bin/env python3
"""
Debug the new individual parsing logic
"""
import sys
import os
import re

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bs4 import BeautifulSoup
from jobspy.wellfound.util import extract_jobs_from_html, parse_individual_job

def debug_new_parsing():
    """Debug the new parsing approach"""
    
    html_file = "debug_wellfound_https__wellfound.com_role_l_product-manager_porto.html"
    
    if not os.path.exists(html_file):
        print(f"❌ File {html_file} not found. Run debug_wellfound.py first.")
        return
    
    with open(html_file, 'r', encoding='utf-8') as f:
        html = f.read()
    
    soup = BeautifulSoup(html, 'html.parser')
    base_url = "https://wellfound.com"
    
    print("=== Testing New Parsing Logic ===")
    
    # Test the full extraction function
    jobs = extract_jobs_from_html(html, base_url)
    print(f"extract_jobs_from_html found: {len(jobs)} jobs")
    
    for i, job in enumerate(jobs[:3]):
        print(f"\nJob {i+1}:")
        for key, value in job.items():
            print(f"  {key}: {value}")
    
    # Test individual parsing for the first few job links
    print(f"\n=== Testing Individual Job Parsing ===")
    
    job_links = soup.find_all('a', href=re.compile(r'/jobs/\d+-'))
    print(f"Found {len(job_links)} job links total")
    
    processed_job_ids = set()
    
    for i, job_link in enumerate(job_links[:5]):
        job_href = job_link.get('href', '')
        job_id = re.search(r'/jobs/(\d+)-', job_href)
        if job_id:
            job_id = job_id.group(1)
            if job_id in processed_job_ids:
                print(f"\nJob Link {i+1}: SKIPPED (duplicate {job_id})")
                continue
            processed_job_ids.add(job_id)
        
        print(f"\nJob Link {i+1}: {job_href}")
        print(f"  Title from link: '{job_link.get_text().strip()}'")
        
        # Test individual parsing
        job_data = parse_individual_job(job_link, base_url, soup)
        if job_data:
            print(f"  ✅ Parsed successfully:")
            for key, value in job_data.items():
                print(f"    {key}: {value}")
        else:
            print(f"  ❌ Failed to parse")

if __name__ == "__main__":
    debug_new_parsing()