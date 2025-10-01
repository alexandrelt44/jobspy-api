#!/usr/bin/env python3
"""
Test scrape.do using their exact Python example
"""
import requests
import urllib.parse

def test_scrape_do_exact():
    """Test using scrape.do's exact Python example"""
    print("Testing scrape.do using their exact Python example...")
    
    # Their exact example for Europe
    targetUrl = urllib.parse.quote("https://wellfound.com/role/l/product-manager/europe")
    url = "http://api.scrape.do/?url=https%3A%2F%2Fwellfound.com%2Frole%2Fl%2Fproduct-manager%2Feurope&token=1badeb624be04cdfb4bc798a2c53e9c93728941d41e&super=true&render=true".format(targetUrl)
    headers = {}

    print(f"URL: {url}")
    response = requests.request("get", url, headers=headers)

    print(f"Status code: {response.status_code}")
    print(f"Content length: {len(response.text)}")
    
    if response.status_code == 200:
        content = response.text
        
        # Check for DataDome
        if any(keyword in content.lower() for keyword in ['datadome', 'captcha', 'challenge']):
            print("❌ DataDome challenge detected")
            with open('scrape_do_exact_challenge.html', 'w', encoding='utf-8') as f:
                f.write(content)
            print("Saved challenge to scrape_do_exact_challenge.html")
        else:
            print("✅ No challenge detected!")
            
            # Check for job content
            if any(keyword in content.lower() for keyword in ['product manager', 'job', 'position', 'role']):
                print("✅ Job content found!")
                
                # Save successful response
                with open('scrape_do_exact_success.html', 'w', encoding='utf-8') as f:
                    f.write(content)
                print("✓ Saved to scrape_do_exact_success.html")
                
                # Try our parser
                try:
                    from jobspy.wellfound.util import extract_jobs_from_html
                    jobs = extract_jobs_from_html(content, "https://wellfound.com")
                    print(f"Jobs extracted: {len(jobs)}")
                    
                    if jobs:
                        print("Sample jobs:")
                        for i, job in enumerate(jobs[:3]):
                            print(f"  {i+1}. {job.get('title', 'N/A')} at {job.get('company', 'N/A')}")
                        return True
                except Exception as e:
                    print(f"Parser error: {e}")
                    
                return True
            else:
                print("⚠️  No job content found")
                
    else:
        print(f"❌ Request failed: {response.text[:200]}")
    
    return False

if __name__ == "__main__":
    success = test_scrape_do_exact()
    if success:
        print("\n🎉 SUCCESS with scrape.do!")
    else:
        print("\n❌ Failed with scrape.do")