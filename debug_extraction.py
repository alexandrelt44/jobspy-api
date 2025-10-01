#!/usr/bin/env python3
"""
Debug the job extraction process specifically
"""
import sys
import os
import re

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bs4 import BeautifulSoup
from urllib.parse import urljoin

def debug_job_extraction():
    """Debug the job extraction from the saved HTML"""
    
    html_file = "debug_wellfound_https__wellfound.com_role_l_product-manager_porto.html"
    
    if not os.path.exists(html_file):
        print(f"❌ File {html_file} not found. Run debug_wellfound.py first.")
        return
    
    with open(html_file, 'r', encoding='utf-8') as f:
        html = f.read()
    
    soup = BeautifulSoup(html, 'html.parser')
    base_url = "https://wellfound.com"
    
    print(f"HTML length: {len(html)} characters")
    
    # Step 1: Find all job links
    job_links = soup.find_all('a', href=re.compile(r'/jobs/\d+-'))
    print(f"Found {len(job_links)} job links:")
    
    for i, link in enumerate(job_links[:5]):
        print(f"  {i+1}. {link.get('href')} - '{link.get_text().strip()}'")
    
    if not job_links:
        print("❌ No job links found! The regex might be wrong.")
        # Try to find any links containing 'jobs'
        any_job_links = soup.find_all('a', href=lambda x: x and 'jobs' in x)
        print(f"Found {len(any_job_links)} links containing 'jobs':")
        for i, link in enumerate(any_job_links[:5]):
            print(f"  {i+1}. {link.get('href')} - '{link.get_text().strip()[:50]}'")
        return
    
    # Step 2: Find job containers using the actual extraction logic
    print(f"\n--- Looking for job containers (using actual extraction logic) ---")
    
    # Import the actual extraction function
    from jobspy.wellfound.util import extract_jobs_from_html
    
    jobs = extract_jobs_from_html(html, base_url)
    print(f"Found {len(jobs)} jobs using extract_jobs_from_html()")
    
    for i, job in enumerate(jobs):
        print(f"\nJob {i+1}:")
        for key, value in job.items():
            print(f"  {key}: {value}")
    
    if jobs:
        return  # Skip the manual parsing if extraction works
    
    # Manual parsing for debugging
    job_containers = []
    
    for i, link in enumerate(job_links[:3]):  # Test first 3 links
        print(f"\nAnalyzing link {i+1}: {link.get('href')}")
        
        container = link
        for level in range(8):  # Increased levels
            parent = container.parent
            if parent and parent.name == 'div':
                # Check if this div contains both job link and company info
                company_link = parent.find('a', href=re.compile(r'/company/'))
                if company_link:
                    company_name = ""
                    company_text_elem = company_link.find(['h2', 'span'])
                    if company_text_elem:
                        company_name = company_text_elem.get_text().strip()
                    print(f"  ✓ Found container at level {level+1} with company: '{company_name}'")
                    job_containers.append(parent)
                    break
                else:
                    print(f"  - Level {level+1}: div but no company link")
            container = parent
            if not parent:
                print(f"  - Level {level+1}: reached top")
                break
    
    print(f"\nFound {len(job_containers)} job containers")
    
    # Step 3: Test parsing each container
    print(f"\n--- Parsing containers ---")
    for i, container in enumerate(job_containers[:3]):
        print(f"\nContainer {i+1}:")
        
        try:
            # Look for job title link pattern: /jobs/XXXXXXX-job-title
            title_elem = container.find('a', href=re.compile(r'/jobs/\d+-'))
            if not title_elem:
                print("  ❌ No title element found")
                continue
            
            title = title_elem.get_text().strip()
            job_url = urljoin(base_url, title_elem['href'])
            print(f"  ✓ Title: {title}")
            print(f"  ✓ URL: {job_url}")
            
            # Find company name - look for company link or header
            company_elem = container.find('a', href=re.compile(r'/company/'))
            if company_elem:
                company = company_elem.get_text().strip()
                print(f"  ✓ Company: {company}")
            else:
                print("  ❌ No company found")
            
            # Find location - look for text near location icon
            location_spans = container.find_all('span', string=re.compile(r'Porto|Lisbon|Remote|Europe', re.I))
            if location_spans:
                location = location_spans[0].get_text().strip()
                print(f"  ✓ Location: {location}")
            else:
                # Try alternative location search
                pl1_spans = container.find_all('span', class_='pl-1')
                if pl1_spans:
                    location = pl1_spans[0].get_text().strip()
                    print(f"  ✓ Location (alt): {location}")
                else:
                    print("  ❌ No location found")
                    
            # Find job type
            job_type_elem = container.find('span', class_=re.compile(r'accent-yellow|bg-accent', re.I))
            if job_type_elem:
                job_type = job_type_elem.get_text().strip()
                print(f"  ✓ Job Type: {job_type}")
            else:
                print("  ❌ No job type found")
                
        except Exception as e:
            print(f"  ❌ Error parsing container: {e}")

if __name__ == "__main__":
    debug_job_extraction()