#!/usr/bin/env python3
"""
Debug what content we get with undetected ChromeDriver + proxy
"""
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
from bs4 import BeautifulSoup
import re

def debug_undetected_content():
    """Debug what content we get with undetected ChromeDriver"""
    
    # Configure undetected Chrome
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    
    # Use Decodo proxy
    proxy_server = "http://gate.decodo.com:10001:spg83ur5k3:Cv~wjcw3h44h2UdUNf"
    options.add_argument(f"--proxy-server={proxy_server}")
    
    driver = None
    
    try:
        # Initialize undetected Chrome
        driver = uc.Chrome(
            options=options,
            headless=True,
            version_main=None,
            use_subprocess=True,
        )
        
        # Test URLs in order of priority
        test_urls = [
            "https://wellfound.com/role/l/product-manager/portugal",
            "https://wellfound.com/role/l/software-engineer/portugal", 
            "https://wellfound.com/jobs/portugal",
            "https://wellfound.com/remote/product-manager-jobs"
        ]
        
        for url in test_urls:
            print(f"\n=== Testing: {url} ===")
            
            try:
                driver.get(url)
                
                # Wait for page load
                WebDriverWait(driver, 30).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
                
                # Wait a bit more for JavaScript
                time.sleep(5)
                
                # Get page info
                html = driver.page_source
                soup = BeautifulSoup(html, 'html.parser')
                
                print(f"Page title: {driver.title}")
                print(f"Page length: {len(html)} characters")
                
                # Look for job links
                job_links = soup.find_all('a', href=re.compile(r'/jobs/\d+-'))
                print(f"Job links found: {len(job_links)}")
                
                if job_links:
                    print("First 5 job links:")
                    for i, link in enumerate(job_links[:5]):
                        print(f"  {i+1}. {link.get('href')} - '{link.get_text().strip()}'")
                else:
                    # Look for any jobs-related content
                    jobs_text = soup.find_all(text=re.compile(r'job|position|role|career', re.I))
                    if jobs_text:
                        print(f"Found {len(jobs_text)} job-related text elements")
                        print("Sample texts:", [text.strip()[:50] for text in jobs_text[:3]])
                    else:
                        print("No job-related content found")
                        
                        # Check if we got a valid Wellfound page
                        if "wellfound" in driver.title.lower() or "wellfound" in html.lower():
                            print("✓ Successfully loaded Wellfound page")
                            # Look for any indication of why no jobs
                            no_results = soup.find_all(text=re.compile(r'no.*result|not.*found|0.*result', re.I))
                            if no_results:
                                print("Possible 'no results' indicators:")
                                for text in no_results[:3]:
                                    print(f"  - '{text.strip()}'")
                        else:
                            print("❌ Page doesn't appear to be Wellfound")
                
                # Save HTML for inspection
                filename = f"debug_undetected_{url.split('/')[-1].replace('-', '_')}.html"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(html)
                print(f"Saved to: {filename}")
                
            except Exception as e:
                print(f"Error loading {url}: {e}")
                
    except Exception as e:
        print(f"Error initializing driver: {e}")
        
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    debug_undetected_content()