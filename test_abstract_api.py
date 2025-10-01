#!/usr/bin/env python3
"""
Test AbstractAPI web scraping service to bypass DataDome on Wellfound
"""
import requests
import json
import time
from urllib.parse import urljoin

def test_abstract_api():
    """Test Wellfound scraping using AbstractAPI"""
    print("Testing Wellfound with AbstractAPI web scraping service...")
    
    # AbstractAPI configuration
    api_key = "3f7047e908df447186533e5e629535f9"
    base_url = "https://scrape.abstractapi.com/v1/"
    
    # First test with a simple site to verify AbstractAPI is working
    print("Testing AbstractAPI with a simple site first...")
    
    simple_test = {
        "api_key": api_key,
        "url": "https://httpbin.org/html"
    }
    
    try:
        response = requests.post(base_url, headers=headers, json=simple_test, timeout=30)
        print(f"Simple test response status: {response.status_code}")
        if response.status_code == 200:
            print("✅ AbstractAPI is working correctly")
        else:
            print(f"❌ AbstractAPI has issues: {response.text}")
            return []
    except Exception as e:
        print(f"❌ AbstractAPI connection failed: {e}")
        return []
    
    # Test URLs
    test_urls = [
        "https://wellfound.com/role/l/product-manager/portugal",
        "https://wellfound.com/role/product-manager",  # Alternative pattern
        "https://wellfound.com/remote/product-manager-jobs",
        "https://wellfound.com/jobs/portugal",  # Simple location-based
    ]
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    for i, target_url in enumerate(test_urls):
        print(f"\n=== Testing URL {i+1}: {target_url} ===")
        
        try:
            # Try with minimal parameters first
            payload = {
                "api_key": api_key,
                "url": target_url
            }
            
            print(f"Making AbstractAPI request...")
            print(f"Parameters: minimal (just API key and URL)")
            
            response = requests.post(
                base_url,
                headers=headers,
                json=payload,
                timeout=60  # 60 second timeout
            )
            
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if we got content
                if 'text' in data and data['text']:
                    html_content = data['text']
                    print(f"Content length: {len(html_content)} characters")
                    
                    # Check for DataDome or challenges
                    content_lower = html_content.lower()
                    if any(keyword in content_lower for keyword in ['datadome', 'captcha', 'challenge']):
                        print("❌ DataDome challenge detected")
                        
                        # Save challenge page for analysis
                        challenge_filename = f"abstract_challenge_{i+1}.html"
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
                            
                            # Save successful response
                            success_filename = f"abstract_success_{i+1}_{target_url.split('/')[-1]}.html"
                            with open(success_filename, 'w', encoding='utf-8') as f:
                                f.write(html_content)
                            print(f"✓ Saved successful response to {success_filename}")
                            
                            # Try to extract jobs using our existing parser
                            try:
                                from jobspy.wellfound.util import extract_jobs_from_html
                                jobs = extract_jobs_from_html(html_content, "https://wellfound.com")
                                print(f"Jobs extracted: {len(jobs)}")
                                
                                if jobs:
                                    print("Sample jobs:")
                                    for j, job in enumerate(jobs[:3]):
                                        print(f"  {j+1}. {job.get('title', 'N/A')} at {job.get('company', 'N/A')}")
                                        print(f"     URL: {job.get('job_url', 'N/A')}")
                                    
                                    return jobs  # Success!
                                
                            except Exception as e:
                                print(f"Error parsing jobs: {e}")
                        else:
                            print("⚠️  No job-related content found - might be homepage/landing page")
                            
                            # Save for analysis anyway
                            filename = f"abstract_nojobs_{i+1}.html"
                            with open(filename, 'w', encoding='utf-8') as f:
                                f.write(html_content)
                            print(f"Saved content to {filename}")
                
                # Check for links if available
                if 'links' in data and data['links']:
                    links = data['links']
                    print(f"Links found: {len(links)}")
                    
                    job_links = [link for link in links if any(keyword in link.lower() 
                                for keyword in ['job', 'role', 'position', 'career'])]
                    
                    if job_links:
                        print("Job-related links:")
                        for j, link in enumerate(job_links[:5]):
                            print(f"  {j+1}. {link}")
            
            elif response.status_code == 429:
                print("❌ Rate limited by AbstractAPI")
                print("Response:", response.text)
                break
                
            else:
                print(f"❌ AbstractAPI error: {response.status_code}")
                print("Response:", response.text)
            
            # Wait between requests to avoid rate limiting
            if i < len(test_urls) - 1:
                print("Waiting 10 seconds before next request...")
                time.sleep(10)
                
        except Exception as e:
            print(f"❌ Error with AbstractAPI request: {e}")
            continue
    
    print(f"\n=== FINAL RESULTS ===")
    print("AbstractAPI test completed")
    return []

if __name__ == "__main__":
    jobs = test_abstract_api()
    
    if jobs:
        print("🎉 SUCCESS: AbstractAPI bypassed protection and found jobs!")
    else:
        print("❌ AbstractAPI could not bypass Wellfound protection")