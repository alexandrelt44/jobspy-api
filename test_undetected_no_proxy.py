#!/usr/bin/env python3
"""
Test undetected ChromeDriver WITHOUT proxy first
"""
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from jobspy import scrape_jobs

def test_undetected_no_proxy():
    """Test Wellfound scraper with undetected ChromeDriver (no proxy)"""
    print("Testing Wellfound scraper with undetected ChromeDriver (no proxy)...")
    
    try:
        # Test with Portugal - no proxy to isolate the anti-detection effectiveness
        results = scrape_jobs(
            site_name=["wellfound"],
            search_term="Product Manager",
            location="Portugal",
            results_wanted=15,
            verbose=2,  # Maximum verbosity
            # No proxies parameter - test undetected ChromeDriver alone
        )
        
        print(f"\n=== RESULTS ===")
        print(f"Found {len(results)} jobs")
        
        if len(results) > 0:
            print("\nJobs found:")
            for i, row in results.head(10).iterrows():
                print(f"{i+1}. {row['title']} at {row['company']} - {row['location']}")
                print(f"   URL: {row['job_url']}")
        else:
            print("No jobs found.")
            
    except Exception as e:
        print(f"Error testing Wellfound scraper: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_undetected_no_proxy()