#!/usr/bin/env python3
"""
Debug script for Wellfound scraper - inspect page content
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

def debug_wellfound_page():
    """Debug the Wellfound page to see what content we get"""
    
    # Configure Chrome options
    chrome_options = Options()
    # Remove headless for debugging - we want to see what happens
    # chrome_options.add_argument("--headless")
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
        
        # Test multiple URLs
        test_urls = [
            "https://wellfound.com/role/l/product-manager/porto",
            "https://wellfound.com/jobs/porto",
            "https://wellfound.com/remote/product-manager-jobs",
            "https://wellfound.com/jobs/europe",
        ]
        
        for url in test_urls:
            print(f"\n=== Testing URL: {url} ===")
            
            try:
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
                
                # Wait additional time for JavaScript
                time.sleep(5)
                
                # Get page title and status
                print(f"Page title: {driver.title}")
                print(f"Current URL: {driver.current_url}")
                
                # Check for common error indicators
                if "403" in driver.title or "Forbidden" in driver.title:
                    print("❌ Page shows 403 Forbidden")
                elif "404" in driver.title or "Not Found" in driver.title:
                    print("❌ Page shows 404 Not Found")
                elif "cloudflare" in driver.title.lower():
                    print("❌ Cloudflare challenge page")
                else:
                    print("✓ Page loaded successfully")
                
                # Get page source and analyze
                html = driver.page_source
                soup = BeautifulSoup(html, 'html.parser')
                
                print(f"Page HTML length: {len(html)} characters")
                
                # Look for job-related content
                job_containers = soup.find_all(['div', 'article'], class_=lambda x: x and any(
                    keyword in x.lower() for keyword in ['job', 'listing', 'startup', 'company', 'role']
                ))
                print(f"Found {len(job_containers)} potential job containers")
                
                # Look for specific text patterns
                if "product" in html.lower():
                    print("✓ Found 'product' text in page")
                if "manager" in html.lower():
                    print("✓ Found 'manager' text in page")
                if "porto" in html.lower():
                    print("✓ Found 'porto' text in page")
                    
                # Save the HTML for manual inspection
                filename = f"debug_wellfound_{url.replace('/', '_').replace(':', '')}.html"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(html)
                print(f"✓ Saved HTML to {filename}")
                
                # Look for any links that might be jobs
                links = soup.find_all('a', href=True)
                job_links = [link for link in links if any(
                    keyword in link.get('href', '').lower() for keyword in ['job', 'role', 'position']
                )]
                print(f"Found {len(job_links)} potential job links")
                
                if job_links:
                    print("Sample job links:")
                    for i, link in enumerate(job_links[:3]):
                        print(f"  {i+1}. {link.get('href')} - {link.get_text()[:50]}")
                
            except Exception as e:
                print(f"❌ Error loading {url}: {e}")
                continue
        
    except Exception as e:
        print(f"❌ Error setting up WebDriver: {e}")
    finally:
        if 'driver' in locals():
            input("Press Enter to close browser...")  # Keep browser open for manual inspection
            driver.quit()

if __name__ == "__main__":
    debug_wellfound_page()