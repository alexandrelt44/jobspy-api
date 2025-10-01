#!/usr/bin/env python3
"""
Test Wellfound scraping with Playwright + stealth (alternative to Selenium)
"""
import sys
import os
import asyncio

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from bs4 import BeautifulSoup
import re
from jobspy.wellfound.util import extract_jobs_from_html

async def test_playwright_wellfound():
    """Test Wellfound scraping with Playwright + stealth"""
    print("Testing Wellfound with Playwright + stealth...")
    
    async with async_playwright() as p:
        # Launch browser with stealth mode
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--disable-images',  # Faster loading
            ]
        )
        
        # Try with proxy from our list
        proxy_config = None
        decodo_proxies = [
            "gate.decodo.com:10001:spg83ur5k3:Cv~wjcw3h44h2UdUNf",
            "gate.decodo.com:10002:spg83ur5k3:Cv~wjcw3h44h2UdUNf",
            "gate.decodo.com:10003:spg83ur5k3:Cv~wjcw3h44h2UdUNf",
        ]
        
        if decodo_proxies:
            proxy = decodo_proxies[0]
            parts = proxy.split(':')
            if len(parts) == 4:
                host, port, username, password = parts
                proxy_config = {
                    'server': f'http://{host}:{port}',
                    'username': username,
                    'password': password
                }
                print(f"Using proxy: {host}:{port} with auth")
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            proxy=proxy_config
        )
        
        page = await context.new_page()
        
        # Apply stealth mode
        stealth_obj = Stealth()
        await stealth_obj.apply_stealth_async(page)
        
        test_urls = [
            "https://wellfound.com/role/l/product-manager/portugal",
            "https://wellfound.com/role/l/software-engineer/portugal",
            "https://wellfound.com/remote/product-manager-jobs"
        ]
        
        for url in test_urls:
            print(f"\n=== Testing: {url} ===")
            
            try:
                # Navigate to page with longer timeout
                print("Loading page...")
                response = await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                print(f"Response status: {response.status}")
                
                # Wait a bit for JavaScript to load
                await asyncio.sleep(5)
                
                # Check page title
                title = await page.title()
                print(f"Page title: {title}")
                
                # Get page content
                content = await page.content()
                print(f"Page length: {len(content)} characters")
                
                # Check for challenge indicators
                if any(keyword in content.lower() for keyword in ['captcha', 'challenge', 'datadome']):
                    print("⚠️  Challenge detected in page content")
                    
                    # Wait longer for challenge to resolve
                    print("Waiting for challenge to resolve...")
                    await asyncio.sleep(15)
                    
                    # Get content again
                    content = await page.content()
                    print(f"After waiting - Page length: {len(content)} characters")
                    
                    if any(keyword in content.lower() for keyword in ['captcha', 'challenge', 'datadome']):
                        print("❌ Challenge still present")
                        # Save challenge page for debugging
                        challenge_filename = f"playwright_challenge_{url.split('/')[-1].replace('-', '_')}.html"
                        with open(challenge_filename, 'w', encoding='utf-8') as f:
                            f.write(content)
                        print(f"Saved challenge page to {challenge_filename}")
                        continue
                    else:
                        print("✅ Challenge resolved!")
                else:
                    print("✅ No challenge detected")
                
                # Extract jobs using our existing parser
                jobs = extract_jobs_from_html(content, "https://wellfound.com")
                print(f"Jobs found: {len(jobs)}")
                
                if jobs:
                    print("First few jobs:")
                    for i, job in enumerate(jobs[:3]):
                        print(f"  {i+1}. {job.get('title')} at {job.get('company')} - {job.get('location')}")
                        print(f"     URL: {job.get('job_url')}")
                    
                    # Save HTML for inspection
                    filename = f"playwright_wellfound_{url.split('/')[-1].replace('-', '_')}.html"
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"✓ Saved HTML to {filename}")
                    
                    return jobs  # Success!
                else:
                    # Look for job-related content
                    soup = BeautifulSoup(content, 'html.parser')
                    job_links = soup.find_all('a', href=re.compile(r'/jobs/\d+-'))
                    print(f"Job links found: {len(job_links)}")
                    
                    if job_links:
                        print("Sample job links:")
                        for i, link in enumerate(job_links[:3]):
                            print(f"  {i+1}. {link.get('href')} - '{link.get_text().strip()}'")
                
            except Exception as e:
                print(f"❌ Error loading {url}: {e}")
                continue
        
        await browser.close()
        return []

def run_test():
    """Run the async test"""
    try:
        jobs = asyncio.run(test_playwright_wellfound())
        
        print(f"\n=== FINAL RESULTS ===")
        print(f"Total jobs found: {len(jobs)}")
        
        if jobs:
            print("SUCCESS: Playwright + stealth bypassed DataDome!")
            return True
        else:
            print("No jobs found, but may have bypassed challenges")
            return False
            
    except Exception as e:
        print(f"Error running Playwright test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    run_test()