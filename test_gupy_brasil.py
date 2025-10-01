#!/usr/bin/env python3
"""
Test Gupy scraper with Brasil location
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from jobspy import scrape_jobs

def test_gupy_brasil():
    """Test Gupy scraper with Brasil location"""
    print("Testing Gupy scraper with Brasil location...")

    try:
        # Test with Product Manager in Brasil
        jobs = scrape_jobs(
            site_name=["gupy"],
            search_term="Product Manager",
            location="Brasil",
            results_wanted=10,
            verbose=2
        )

        print(f"\nFound {len(jobs)} jobs")

        if len(jobs) > 0:
            print("\nFirst few jobs:")
            for i in range(min(3, len(jobs))):
                job = jobs.iloc[i]
                print(f"{i+1}. {job['title']} at {job['company']} - {job['location']}")

            # Save results to CSV for inspection
            jobs.to_csv("gupy_product_manager_brasil.csv", index=False)
            print(f"\nResults saved to gupy_product_manager_brasil.csv")
        else:
            print("No jobs found")

    except Exception as e:
        print(f"Error testing Gupy scraper: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_gupy_brasil()