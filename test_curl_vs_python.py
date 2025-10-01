#!/usr/bin/env python3
"""
Compare curl vs Python requests to understand the difference
"""
import requests
import subprocess
import urllib.parse

def test_curl_vs_python():
    """Test the exact same URL with both curl and Python"""
    
    token = "1badeb624be04cdfb4bc798a2c53e9c93728941d41e"
    target_url = "https://wellfound.com/role/l/product-manager/europe" 
    encoded_url = urllib.parse.quote(target_url)
    api_url = f"http://api.scrape.do/?url={encoded_url}&token={token}&super=true&render=true"
    
    print(f"API URL: {api_url}")
    print("="*80)
    
    # Test with curl
    print("\\n1. Testing with curl...")
    try:
        curl_result = subprocess.run([
            'curl', '--request', 'GET', '--location', api_url
        ], capture_output=True, text=True, timeout=60)
        
        if curl_result.returncode == 0:
            curl_content = curl_result.stdout
            print(f"Curl status: SUCCESS")
            print(f"Curl content length: {len(curl_content)}")
            
            # Check for challenges
            curl_has_challenge = any(keyword in curl_content.lower() 
                                   for keyword in ['datadome', 'captcha', 'challenge'])
            print(f"Curl has challenge: {curl_has_challenge}")
            
            # Check for job content
            curl_has_jobs = "results total" in curl_content and "Actively Hiring" in curl_content
            print(f"Curl has job listings: {curl_has_jobs}")
            
            if curl_has_jobs:
                print("✅ Curl successfully got job listings!")
            
        else:
            print(f"Curl failed: {curl_result.stderr}")
            
    except Exception as e:
        print(f"Curl error: {e}")
    
    print("\\n2. Testing with Python requests...")
    try:
        # Try to match curl as closely as possible
        headers = {
            'User-Agent': 'curl/7.68.0',  # Use curl's user agent
            'Accept': '*/*',              # Curl's default accept
        }
        
        response = requests.get(api_url, headers=headers, timeout=60)
        
        print(f"Python status: {response.status_code}")
        print(f"Python content length: {len(response.text)}")
        
        # Check for challenges
        python_has_challenge = any(keyword in response.text.lower() 
                                 for keyword in ['datadome', 'captcha', 'challenge'])
        print(f"Python has challenge: {python_has_challenge}")
        
        # Check for job content
        python_has_jobs = "results total" in response.text and "Actively Hiring" in response.text
        print(f"Python has job listings: {python_has_jobs}")
        
        if python_has_jobs:
            print("✅ Python successfully got job listings!")
        elif python_has_challenge:
            print("❌ Python got DataDome challenge")
            # Save challenge for inspection
            with open('python_challenge.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            print("Saved Python challenge to python_challenge.html")
        
    except Exception as e:
        print(f"Python error: {e}")
    
    print("\\n3. Testing Python with no headers...")
    try:
        response = requests.get(api_url, timeout=60)
        
        print(f"No headers status: {response.status_code}")
        print(f"No headers content length: {len(response.text)}")
        
        no_headers_has_challenge = any(keyword in response.text.lower() 
                                     for keyword in ['datadome', 'captcha', 'challenge'])
        print(f"No headers has challenge: {no_headers_has_challenge}")
        
        no_headers_has_jobs = "results total" in response.text and "Actively Hiring" in response.text
        print(f"No headers has job listings: {no_headers_has_jobs}")
        
        if no_headers_has_jobs:
            print("✅ No headers successfully got job listings!")
            
    except Exception as e:
        print(f"No headers error: {e}")

if __name__ == "__main__":
    test_curl_vs_python()