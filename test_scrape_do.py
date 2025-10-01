#!/usr/bin/env python3
"""
Test scrape.do API to bypass DataDome on Wellfound
"""
import requests
import urllib.parse
import time

def test_scrape_do():
    """Test Wellfound scraping using scrape.do API"""
    print("Testing Wellfound with scrape.do API...")
    
    token = "1badeb624be04cdfb4bc798a2c53e9c93728941d41e"
    
    # Test URLs - starting with Europe since that worked in playground
    test_urls = [
        "https://wellfound.com/role/l/product-manager/europe",  # This worked in playground
        "https://wellfound.com/role/l/product-manager/portugal",
        "https://wellfound.com/role/product-manager",  # Alternative pattern
        "https://wellfound.com/remote/product-manager-jobs",
    ]
    
    # First test with a simple site to verify scrape.do is working
    print("Testing scrape.do with a simple site first...")
    
    simple_url = urllib.parse.quote("https://httpbin.org/html")
    test_endpoint = f"http://api.scrape.do/?token={token}&url={simple_url}"
    
    try:
        response = requests.get(test_endpoint, timeout=30)
        print(f"Simple test response status: {response.status_code}")
        if response.status_code == 200 and len(response.text) > 100:
            print("✅ scrape.do is working correctly")
        else:
            print(f"❌ scrape.do has issues: {response.text[:200]}...")
            return []
    except Exception as e:
        print(f"❌ scrape.do connection failed: {e}")
        return []
    
    print("\\nNow testing Wellfound URLs...")
    
    for i, target_url in enumerate(test_urls):
        print(f"\\n=== Testing URL {i+1}: {target_url} ===")
        
        try:
            # URL encode the target URL and use super=true&render=true parameters
            encoded_url = urllib.parse.quote(target_url)
            api_url = f"http://api.scrape.do/?url={encoded_url}&token={token}&super=true&render=true"
            
            print(f"Making scrape.do request...")
            print(f"Using parameters: super=true&render=true")
            print(f"Encoded URL: {encoded_url}")
            
            response = requests.get(api_url, timeout=60)  # 60 second timeout
            
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                html_content = response.text
                print(f"Content length: {len(html_content)} characters")
                
                # Check for DataDome or challenges
                content_lower = html_content.lower()
                if any(keyword in content_lower for keyword in ['datadome', 'captcha', 'challenge']):
                    print("❌ DataDome challenge detected")
                    
                    # Save challenge page for analysis
                    challenge_filename = f"scrape_do_challenge_{i+1}.html"
                    with open(challenge_filename, 'w', encoding='utf-8') as f:
                        f.write(html_content)
                    print(f"Saved challenge page to {challenge_filename}")
                    
                else:
                    print("✅ No challenge detected!")
                    
                    # Check for job-related content
                    job_indicators = [
                        'job', 'position', 'role', 'hiring', 'career',
                        'product manager', 'software engineer', 'developer'
                    ]
                    
                    job_content_found = any(indicator in content_lower for indicator in job_indicators)
                    
                    if job_content_found:
                        print("✅ Job-related content found!")
                        
                        # Check if it's the actual listings page vs homepage
                        listings_indicators = [
                            'job-title', 'job-listing', 'job-card', 'position-title',
                            'company-name', 'salary', 'apply', 'job-description'
                        ]
                        
                        is_listings_page = any(indicator in content_lower for indicator in listings_indicators)
                        
                        if is_listings_page:
                            print("✅ Appears to be actual job listings page!")
                        else:
                            print("⚠️  Job content found but might be homepage/landing page")
                        
                        # Save successful response
                        success_filename = f"scrape_do_success_{i+1}_{target_url.split('/')[-1]}.html"
                        with open(success_filename, 'w', encoding='utf-8') as f:
                            f.write(html_content)
                        print(f"✓ Saved response to {success_filename}")
                        
                        # Try to extract jobs using our existing parser
                        try:
                            from jobspy.wellfound.util import extract_jobs_from_html
                            jobs = extract_jobs_from_html(html_content, "https://wellfound.com")
                            print(f"Jobs extracted by parser: {len(jobs)}")
                            
                            if jobs:
                                print("✅ SUCCESS! Sample jobs:")
                                for j, job in enumerate(jobs[:5]):
                                    print(f"  {j+1}. {job.get('title', 'N/A')} at {job.get('company', 'N/A')}")
                                    print(f"     Location: {job.get('location', 'N/A')}")
                                    print(f"     URL: {job.get('job_url', 'N/A')}")
                                
                                return jobs  # Success!
                            else:
                                print("⚠️  Parser found no jobs - need to check HTML structure")
                                
                                # Look for job links manually
                                from bs4 import BeautifulSoup
                                soup = BeautifulSoup(html_content, 'html.parser')
                                job_links = soup.find_all('a', href=lambda x: x and '/jobs/' in x)
                                print(f"Manual job link search found: {len(job_links)} links")
                                
                                if job_links:
                                    print("Sample job links:")
                                    for j, link in enumerate(job_links[:5]):
                                        print(f"  {j+1}. {link.get('href')} - '{link.get_text().strip()[:60]}...'")
                                
                        except Exception as e:
                            print(f"Error parsing jobs: {e}")
                            
                    else:
                        print("⚠️  No job-related content found")
                        
                        # Save for analysis anyway
                        filename = f"scrape_do_nojobs_{i+1}.html"
                        with open(filename, 'w', encoding='utf-8') as f:
                            f.write(html_content)
                        print(f"Saved content to {filename}")
            
            elif response.status_code == 429:
                print("❌ Rate limited by scrape.do")
                print("Response:", response.text[:200])
                break
                
            elif response.status_code == 402:
                print("❌ Payment required - scrape.do credit exhausted")
                print("Response:", response.text[:200])
                break
                
            else:
                print(f"❌ scrape.do error: {response.status_code}")
                print("Response:", response.text[:200])
            
            # Wait between requests to avoid rate limiting
            if i < len(test_urls) - 1:
                print("Waiting 5 seconds before next request...")
                time.sleep(5)
                
        except Exception as e:
            print(f"❌ Error with scrape.do request: {e}")
            continue
    
    print(f"\\n=== FINAL RESULTS ===")
    print("scrape.do test completed")
    return []

if __name__ == "__main__":
    jobs = test_scrape_do()
    
    if jobs:
        print("🎉 SUCCESS: scrape.do bypassed DataDome and found jobs!")
        print(f"Total jobs found: {len(jobs)}")
    else:
        print("❌ scrape.do could not bypass Wellfound protection or extract jobs")