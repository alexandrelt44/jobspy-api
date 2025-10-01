#!/usr/bin/env python3
"""
Test the API endpoint with Wellfound integration
"""
import requests
import json

def test_api_wellfound():
    """Test the API with Wellfound site"""
    print("🚀 Testing API endpoint with Wellfound...")
    
    # API endpoint
    url = "http://localhost:8000/api/jobs/search"
    
    # Test payload
    payload = {
        "site_name": ["wellfound"],
        "search_term": "Product Manager",
        "location": "Portugal",
        "results_wanted": 20,
        "use_proxies": True
    }
    
    try:
        print(f"Making POST request to: {url}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(url, json=payload, timeout=120)
        
        print(f"\\nResponse status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"\\n✅ SUCCESS!")
            print(f"Jobs found: {len(data.get('jobs', []))}")
            print(f"Sites scraped: {data.get('sites_scraped', [])}")
            print(f"Total results: {data.get('total_results', 0)}")
            
            # Show sample jobs
            jobs = data.get('jobs', [])
            if jobs:
                print("\\n📋 Sample jobs:")
                for i, job in enumerate(jobs[:5]):
                    print(f"  {i+1}. {job.get('title')} at {job.get('company')}")
                    print(f"     Location: {job.get('location')}")
                    print(f"     Site: {job.get('site')}")
                    print(f"     URL: {job.get('job_url')}")
                    print()
            
            return True
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - make sure API is running on localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_api_multi_site():
    """Test API with multiple sites including Wellfound"""
    print("\\n" + "="*60)
    print("🚀 Testing API with multiple sites (including Wellfound)...")
    
    url = "http://localhost:8000/api/jobs/search"
    
    payload = {
        "site_name": ["linkedin", "wellfound"],  # Include both
        "search_term": "Software Engineer",
        "location": "Europe",
        "results_wanted": 10,
        "use_proxies": True
    }
    
    try:
        response = requests.post(url, json=payload, timeout=120)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ Multi-site SUCCESS!")
            print(f"Total jobs: {len(data.get('jobs', []))}")
            
            # Group by site
            jobs_by_site = {}
            for job in data.get('jobs', []):
                site = job.get('site', 'unknown')
                if site not in jobs_by_site:
                    jobs_by_site[site] = 0
                jobs_by_site[site] += 1
            
            print("\\n📊 Jobs by site:")
            for site, count in jobs_by_site.items():
                print(f"  {site}: {count} jobs")
            
            return True
        else:
            print(f"❌ Multi-site failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Multi-site error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Wellfound API integration...")
    
    # Test Wellfound only
    wellfound_success = test_api_wellfound()
    
    # Test multi-site
    multi_success = test_api_multi_site()
    
    print("\\n" + "="*60)
    print("🏁 FINAL RESULTS:")
    print(f"Wellfound-only test: {'✅ SUCCESS' if wellfound_success else '❌ FAILED'}")
    print(f"Multi-site test: {'✅ SUCCESS' if multi_success else '❌ FAILED'}")
    
    if wellfound_success:
        print("\\n🎉 Wellfound is successfully integrated with the API!")
    else:
        print("\\n❌ API integration needs debugging")