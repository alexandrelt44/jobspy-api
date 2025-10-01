#!/usr/bin/env python3
"""
Debug script for Portugal Wellfound page with more diverse results
"""
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
import time
from bs4 import BeautifulSoup
from jobspy.wellfound.util import extract_jobs_from_html

def test_portugal_page():
    """Test the Portugal page which has more diverse results"""
    
    # Configure Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in background for automated testing
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Anti-detection measures
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    chrome_options.add_argument(f"--user-agent={user_agent}")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    try:
        # Initialize driver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        url = "https://wellfound.com/role/l/product-manager/porto"
        print(f"Testing URL: {url}")
        
        driver.get(url)
        
        # Wait for page to load
        WebDriverWait(driver, 15).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        
        # Check if Cloudflare challenge is present
        try:
            WebDriverWait(driver, 10).until_not(
                EC.presence_of_element_located((By.ID, "cf-challenge-running"))
            )
            print("✓ No Cloudflare challenge detected")
        except TimeoutException:
            print("✓ No Cloudflare challenge found (good)")
        
        # Wait longer for DataDome and other challenges
        print("Waiting for anti-bot challenges to complete...")
        time.sleep(10)
        
        # Check if we're still on a challenge page
        current_title = driver.title
        if current_title == "wellfound.com" and len(driver.page_source) < 10000:
            print("Still on challenge page, waiting longer...")
            time.sleep(15)
            
        # Try refreshing the page if we're still on a challenge
        if "captcha" in driver.page_source.lower() or "challenge" in driver.page_source.lower():
            print("Detected challenge page, refreshing...")
            driver.refresh()
            time.sleep(10)
        
        # Get page title and status
        print(f"Page title: {driver.title}")
        print(f"Current URL: {driver.current_url}")
        
        # Get page source and analyze
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        print(f"Page HTML length: {len(html)} characters")
        
        # Look for job-related content
        import re
        job_links = soup.find_all('a', href=re.compile(r'/jobs/\d+-'))
        print(f"Found {len(job_links)} job links:")
        
        # Show first 10 job links
        for i, link in enumerate(job_links[:10]):
            print(f"  {i+1}. {link.get('href')} - '{link.get_text().strip()}'")
        
        # Test our extraction function
        print(f"\n=== Testing extract_jobs_from_html ===")
        jobs = extract_jobs_from_html(html, "https://wellfound.com")
        print(f"Extracted {len(jobs)} jobs:")
        
        # Show first 10 jobs with more details
        for i, job in enumerate(jobs[:10]):
            print(f"\n{i+1}. {job.get('title')} at {job.get('company')}")
            print(f"   Location: {job.get('location')}")
            print(f"   Type: {job.get('job_type')}")
            print(f"   URL: {job.get('job_url')}")
        
        if len(jobs) > 10:
            print(f"\n... and {len(jobs) - 10} more jobs")
        
        # Save HTML for further analysis if needed
        filename = "debug_portugal_product_manager.html"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"\n✓ Saved HTML to {filename} for further analysis")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if 'driver' in locals():
            driver.quit()

if __name__ == "__main__":
    test_portugal_page()