#!/usr/bin/env python3
"""
Test script for Gupy scraper
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from jobspy import scrape_jobs

def test_gupy_scraper():
    """Test the Gupy scraper with a simple search"""
    print("Testing Gupy scraper...")

    try:
        # Test with a common search term in Portuguese
        jobs = scrape_jobs(
            site_name=["gupy"],
            search_term="desenvolvedor",
            results_wanted=5,
            verbose=2
        )

        print(f"\nFound {len(jobs)} jobs")

        if len(jobs) > 0:
            print("\nFirst job details:")
            print(f"Title: {jobs.iloc[0]['title']}")

            # Check what columns are actually available
            print(f"\nAll columns: {list(jobs.columns)}")

            # Try to access company column safely
            company_col = None
            for col in ['company_name', 'company', 'employer']:
                if col in jobs.columns:
                    company_col = col
                    break

            if company_col:
                print(f"Company: {jobs.iloc[0][company_col]}")

            if 'location' in jobs.columns:
                print(f"Location: {jobs.iloc[0]['location']}")
            if 'job_url' in jobs.columns:
                print(f"URL: {jobs.iloc[0]['job_url']}")
            if 'site' in jobs.columns:
                print(f"Site: {jobs.iloc[0]['site']}")

            # Save results to CSV for inspection
            jobs.to_csv("gupy_test_results.csv", index=False)
            print("\nResults saved to gupy_test_results.csv")
        else:
            print("No jobs found - this might indicate:")
            print("1. The HTML structure has changed")
            print("2. The search query returned no results")
            print("3. There's an issue with the scraping logic")

    except Exception as e:
        print(f"Error testing Gupy scraper: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_gupy_scraper()