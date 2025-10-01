#!/usr/bin/env python3
"""
Test undetected ChromeDriver with Decodo proxies for DataDome bypass
"""
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from jobspy import scrape_jobs

def test_undetected_with_proxy():
    """Test Wellfound scraper with undetected ChromeDriver and proxies"""
    print("Testing Wellfound scraper with undetected ChromeDriver and Decodo proxies...")
    
    # Use one of the Decodo proxies from the earlier conversation
    decodo_proxies = [
        "gate.decodo.com:10001:spg83ur5k3:Cv~wjcw3h44h2UdUNf",
        "gate.decodo.com:10002:spg83ur5k3:Cv~wjcw3h44h2UdUNf",
        "gate.decodo.com:10003:spg83ur5k3:Cv~wjcw3h44h2UdUNf"
    ]
    
    try:
        # Test with Portugal (broader search) using proxy - match the URL structure
        results = scrape_jobs(
            site_name=["wellfound"],
            search_term="Product Manager",  # This matches the URL /product-manager/
            location="Portugal",
            results_wanted=15,
            verbose=2,  # Maximum verbosity
            proxies=decodo_proxies[:1]  # Use just one proxy for testing
        )
        
        print(f"\n=== RESULTS ===")
        print(f"Found {len(results)} jobs")
        
        if len(results) > 0:
            print("\nFirst few jobs:")
            for i, row in results.head().iterrows():
                print(f"{i+1}. {row['title']} at {row['company']} - {row['location']}")
                print(f"   URL: {row['job_url']}")
        else:
            print("No jobs found. Checking potential issues:")
            print("1. DataDome might still be blocking despite undetected ChromeDriver + proxy")
            print("2. Portugal URL might not have jobs for 'Product Owner'")
            print("3. Proxy might be blocked or invalid")
            
    except Exception as e:
        print(f"Error testing Wellfound scraper: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_undetected_with_proxy()