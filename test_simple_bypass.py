#!/usr/bin/env python3
"""
Simple test to see if we can bypass DataDome with basic requests and different headers/sessions
"""
import requests
import time
from urllib.parse import urljoin

def test_simple_requests():
    """Test basic requests with various user agents and headers"""
    
    headers_sets = [
        {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
        },
        {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
        }
    ]
    
    # Test URLs
    urls = [
        "https://wellfound.com/role/l/product-manager/portugal",
        "https://wellfound.com/remote/product-manager-jobs"
    ]
    
    for i, headers in enumerate(headers_sets):
        print(f"\n=== Testing header set {i+1} ===")
        
        session = requests.Session()
        session.headers.update(headers)
        
        for url in urls:
            try:
                print(f"Testing: {url}")
                
                response = session.get(url, timeout=30)
                print(f"Status: {response.status_code}")
                print(f"Content length: {len(response.text)}")
                
                # Check for DataDome
                content_lower = response.text.lower()
                if any(keyword in content_lower for keyword in ['datadome', 'captcha', 'challenge']):
                    print("❌ DataDome challenge detected")
                else:
                    print("✅ No challenge detected!")
                    # Save successful response
                    with open(f'simple_success_{i}_{url.split("/")[-1]}.html', 'w') as f:
                        f.write(response.text)
                    print(f"Saved response to file")
                
                time.sleep(3)  # Delay between requests
                
            except Exception as e:
                print(f"Error: {e}")
        
        time.sleep(5)  # Delay between header sets

if __name__ == "__main__":
    test_simple_requests()