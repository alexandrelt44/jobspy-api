#!/usr/bin/env python3
"""
Test script for JobSpy API
"""

import requests
import json
import time


def test_api_endpoints(base_url="http://localhost:8000"):
    """Test the main API endpoints"""
    
    print("🔍 Testing JobSpy API endpoints...")
    print("=" * 50)
    
    # Test 1: Health check
    print("\n1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Health check passed")
            health_data = response.json()
            print(f"   Status: {health_data['status']}")
            print(f"   Version: {health_data['version']}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")
    
    # Test 2: Root endpoint
    print("\n2. Testing root endpoint...")
    try:
        response = requests.get(base_url, timeout=10)
        if response.status_code == 200:
            print("✅ Root endpoint accessible")
            root_data = response.json()
            print(f"   Message: {root_data['message']}")
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Root endpoint error: {e}")
    
    # Test 3: Supported sites
    print("\n3. Testing supported sites endpoint...")
    try:
        response = requests.get(f"{base_url}/api/jobs/sites", timeout=10)
        if response.status_code == 200:
            print("✅ Supported sites endpoint working")
            sites_data = response.json()
            print(f"   Total sites: {sites_data['total_sites']}")
            for site in list(sites_data['sites'].keys())[:3]:  # Show first 3
                print(f"   - {site}: {sites_data['sites'][site]['name']}")
        else:
            print(f"❌ Supported sites failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Supported sites error: {e}")
    
    # Test 4: Job search (small test)
    print("\n4. Testing job search endpoint (small test)...")
    try:
        search_data = {
            "search_term": "python developer",
            "location": "Porto, Portugal",
            "sites": ["indeed"],  # Only one site for quick test
            "results_wanted": 5,   # Small number for test
            "verbose": 0
        }
        
        print("   Making search request...")
        response = requests.post(
            f"{base_url}/api/jobs/search", 
            json=search_data,
            timeout=60  # Longer timeout for job search
        )
        
        if response.status_code == 200:
            print("✅ Job search completed successfully")
            search_results = response.json()
            print(f"   Found {search_results['total_jobs']} jobs")
            if search_results['jobs']:
                first_job = search_results['jobs'][0]
                print(f"   Sample job: {first_job.get('title', 'N/A')} at {first_job.get('company', 'N/A')}")
        else:
            print(f"❌ Job search failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Job search error: {e}")


def main():
    """Main test function"""
    print("🧪 JobSpy API Test Suite")
    print("Note: Make sure the API is running with: uvicorn api.main:app --reload")
    print("\nChecking if API is running...")
    
    # Check if API is running
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ API is running!")
            test_api_endpoints()
        else:
            print("❌ API responded with error")
    except requests.exceptions.ConnectionError:
        print("❌ API is not running. Please start it with:")
        print("uvicorn api.main:app --reload --host 0.0.0.0 --port 8000")
    except Exception as e:
        print(f"❌ Error checking API status: {e}")


if __name__ == "__main__":
    main()