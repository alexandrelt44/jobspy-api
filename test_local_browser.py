#!/usr/bin/env python3
"""
Test using local browser (non-headless) to bypass DataDome manually
This will open a visible browser window for manual challenge solving if needed
"""
import sys
import os
import time

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth
from jobspy.wellfound.util import extract_jobs_from_html

def test_local_browser():
    """Test Wellfound with local visible browser for manual DataDome handling"""
    print("Testing Wellfound with local visible browser...")
    print("This will open a visible browser window. You can manually solve any challenges if they appear.")
    
    driver = None
    
    try:
        # Configure Chrome options for local browsing
        options = uc.ChromeOptions()
        
        # Basic options - but keep it visible (no headless)
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage") 
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--start-maximized")
        
        # Add proxy if needed (using first proxy from our list)
        decodo_proxies = [
            "gate.decodo.com:10001:spg83ur5k3:Cv~wjcw3h44h2UdUNf",
            "gate.decodo.com:10002:spg83ur5k3:Cv~wjcw3h44h2UdUNf",
        ]
        
        if decodo_proxies:
            proxy = decodo_proxies[0]
            parts = proxy.split(':')
            if len(parts) == 4:
                host, port, username, password = parts
                # For now, try without proxy first to see if local browser helps
                # proxy_server = f"{host}:{port}"
                # options.add_argument(f"--proxy-server=http://{proxy_server}")
                print(f"Proxy available but not using initially: {host}:{port}")
        
        # Initialize undetected Chrome in visible mode
        driver = uc.Chrome(
            options=options,
            headless=False,  # Visible browser
            version_main=None,
            use_subprocess=True,
        )
        
        # Apply stealth measures
        stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
        )
        
        # Test URL
        url = "https://wellfound.com/role/l/product-manager/portugal"
        print(f"\\nNavigating to: {url}")
        print("Browser window should open now...")
        
        # Navigate to the page
        driver.get(url)
        
        print("\\nWaiting for page to load...")
        print("If you see a challenge page in the browser window, it should resolve automatically or you can solve it manually.")
        print("Waiting 30 seconds for page to fully load and any challenges to resolve...")
        
        # Wait for challenges to resolve
        for i in range(30):
            time.sleep(1)
            if i % 5 == 0:
                print(f"Waiting... {30-i} seconds remaining")
            
            # Check if we have actual content (not just a challenge page)
            current_source = driver.page_source
            if len(current_source) > 50000:  # Substantial content suggests success
                print("✅ Substantial content detected - challenge likely resolved!")
                break
        
        print("\\nProceeding with content extraction...")
        
        # Check page content
        page_source = driver.page_source
        print(f"Page length: {len(page_source)} characters")
        
        # Check for challenges
        if any(keyword in page_source.lower() for keyword in ['captcha', 'challenge', 'datadome']):
            print("⚠️  Challenge still detected in page source")
            print("Make sure you've completed any challenges and are on the actual job page")
            
            print("Waiting 10 more seconds for any remaining page loads...")
            time.sleep(10)
            page_source = driver.page_source
            print(f"Updated page length: {len(page_source)} characters")
        
        # Save the HTML for inspection
        filename = "local_browser_portugal.html"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(page_source)
        print(f"✓ Saved page HTML to {filename}")
        
        # Try to extract jobs
        try:
            jobs = extract_jobs_from_html(page_source, "https://wellfound.com")
            print(f"\\n=== RESULTS ===")
            print(f"Jobs found: {len(jobs)}")
            
            if jobs:
                print("\\nFirst few jobs:")
                for i, job in enumerate(jobs[:5]):
                    print(f"  {i+1}. {job.get('title', 'N/A')} at {job.get('company', 'N/A')}")
                    print(f"     Location: {job.get('location', 'N/A')}")
                    print(f"     URL: {job.get('job_url', 'N/A')}")
                    print()
                
                return True
            else:
                print("No jobs extracted. Let's check what's in the page source...")
                # Look for job-related content
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(page_source, 'html.parser')
                
                # Look for common job listing indicators
                job_links = soup.find_all('a', href=lambda x: x and '/jobs/' in x)
                print(f"Job links found: {len(job_links)}")
                
                if job_links:
                    print("Sample job links:")
                    for i, link in enumerate(job_links[:5]):
                        print(f"  {i+1}. {link.get('href')} - '{link.get_text().strip()[:100]}'")
                
                return False
                
        except Exception as e:
            print(f"Error extracting jobs: {e}")
            return False
        
    except Exception as e:
        print(f"Error with browser: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        if driver:
            print("\\nClosing browser in 5 seconds...")
            time.sleep(5)
            driver.quit()

if __name__ == "__main__":
    success = test_local_browser()
    if success:
        print("\\n✅ SUCCESS: Local browser approach worked!")
    else:
        print("\\n❌ Local browser approach needs refinement")