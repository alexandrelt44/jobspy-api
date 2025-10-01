#!/usr/bin/env python3
"""
Test script for Wellfound scraper with Selenium
"""
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from jobspy import scrape_jobs

def test_wellfound_scraper():
    """Test the Wellfound scraper with Selenium"""
    print("Testing Wellfound scraper with Selenium...")
    
    try:
        # Test scraping from Wellfound with Portugal (broader search)
        results = scrape_jobs(
            site_name=["wellfound"],
            search_term="Product Owner",
            location="Portugal", 
            results_wanted=10,
            verbose=2  # Maximum verbosity to see what's happening
        )
        
        print(f"\n=== RESULTS ===")
        print(f"Found {len(results)} jobs")
        
        if len(results) > 0:
            print("\nFirst job details:")
            for col in results.columns:
                print(f"{col}: {results.iloc[0][col]}")
        else:
            print("No jobs found. This might be expected if:")
            print("1. ChromeDriver is not installed")
            print("2. Wellfound changed their page structure")
            print("3. Cloudflare is still blocking us")
            
    except Exception as e:
        print(f"Error testing Wellfound scraper: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_wellfound_scraper()