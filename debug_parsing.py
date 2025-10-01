#!/usr/bin/env python3
"""
Debug the parsing logic specifically
"""
import sys
import os
import re

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bs4 import BeautifulSoup
from jobspy.wellfound.util import extract_jobs_from_html

def debug_parsing():
    """Debug the parsing step by step"""
    
    html_file = "debug_wellfound_https__wellfound.com_role_l_product-manager_porto.html"
    
    with open(html_file, 'r', encoding='utf-8') as f:
        html = f.read()
    
    soup = BeautifulSoup(html, 'html.parser')
    base_url = "https://wellfound.com"
    
    # Step 1: Find all job links
    job_links = soup.find_all('a', href=re.compile(r'/jobs/\d+-'))
    print(f"Found {len(job_links)} job links:")
    for i, link in enumerate(job_links):
        print(f"  {i+1}. {link.get('href')} - '{link.get_text().strip()}'")
    
    # Step 2: Find containers manually
    print(f"\n--- Manual Container Finding ---")
    
    processed_job_ids = set()
    found_containers = []
    
    for i, link in enumerate(job_links):
        # Extract job ID for deduplication
        job_id = re.search(r'/jobs/(\d+)-', link.get('href', ''))
        if job_id:
            job_id = job_id.group(1)
            print(f"\nLink {i+1}: Job ID = {job_id}")
            if job_id in processed_job_ids:
                print(f"  ❌ Duplicate job ID {job_id}, skipping")
                continue  # Skip duplicates
            processed_job_ids.add(job_id)
            print(f"  ✅ New job ID {job_id}, processing")
        
        # Find the parent container that holds the full job info
        container = link
        for level in range(8):
            parent = container.parent
            if parent and parent.name == 'div':
                # Check if this div contains both job link and company info
                company_link = parent.find('a', href=re.compile(r'/company/'))
                if company_link:
                    found_containers.append(parent)
                    print(f"  ✅ Found container at level {level+1}")
                    break
            container = parent
            if not parent:
                break
    
    print(f"\nFound {len(found_containers)} unique containers")
    
    # Step 3: Test parsing each container
    print(f"\n--- Testing Container Parsing ---")
    
    from jobspy.wellfound.util import parse_job_container
    
    for i, container in enumerate(found_containers):
        print(f"\nContainer {i+1}:")
        
        # Debug what job links are in this container
        container_job_links = container.find_all('a', href=re.compile(r'/jobs/\d+-'))
        print(f"  Job links in container: {len(container_job_links)}")
        for j, cjl in enumerate(container_job_links):
            print(f"    {j+1}. {cjl.get('href')} - '{cjl.get_text().strip()}'")
        
        # Parse the container
        job_data = parse_job_container(container, base_url)
        if job_data:
            print(f"  ✅ Parsed successfully:")
            for key, value in job_data.items():
                print(f"    {key}: {value}")
        else:
            print(f"  ❌ Failed to parse")

if __name__ == "__main__":
    debug_parsing()