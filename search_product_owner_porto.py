#!/usr/bin/env python3
"""
Search for Product Owner jobs in Porto, Portugal using JobSpy
"""

import csv
import pandas as pd
from jobspy import scrape_jobs

def main():
    print("🔍 Searching for Product Owner jobs in Porto, Portugal...")
    print("=" * 60)
    
    try:
        # Search for Product Owner jobs in Porto, Portugal
        jobs = scrape_jobs(
            site_name=["indeed", "linkedin", "google"],  # Main job boards (Glassdoor not available for Portugal)
            search_term="Product Owner",
            location="Porto, Portugal",
            results_wanted=30,  # Reduced to avoid rate limiting with description fetching
            hours_old=168,  # Jobs posted in the last week (7 days * 24 hours)
            country_indeed='Portugal',  # Set country for Indeed
            linkedin_fetch_description=True,  # Fetch full descriptions and direct URLs from LinkedIn
            verbose=2  # Show detailed logs
        )
        
        print(f"\n✅ Found {len(jobs)} jobs!")
        
        if len(jobs) > 0:
            # Display basic info
            print("\n📋 Job Summary:")
            print(f"Total jobs found: {len(jobs)}")
            print(f"Sites searched: {', '.join(jobs['site'].unique())}")
            
            # Show first few jobs with enhanced details
            print("\n🎯 Sample Results (First 5 jobs):")
            print("=" * 100)
            for idx, row in jobs.head(5).iterrows():
                print(f"\n📌 {row['title']}")
                print(f"🏢 Company: {row['company']}")
                print(f"📍 Location: {row['location']}")
                print(f"🌐 Site: {row['site']}")
                if pd.notna(row.get('date_posted')):
                    print(f"📅 Posted: {row['date_posted']}")
                if pd.notna(row['min_amount']) and pd.notna(row['max_amount']):
                    print(f"💰 Salary: {row['min_amount']} - {row['max_amount']} {row.get('currency', 'EUR')} ({row.get('interval', 'yearly')})")
                if pd.notna(row.get('job_url_direct')) and row['site'] == 'linkedin':
                    print(f"🔗 LinkedIn URL: {row['job_url']}")
                    print(f"🎯 Direct URL: {row['job_url_direct']}")
                else:
                    print(f"🔗 URL: {row['job_url']}")
                
                # Show description preview for LinkedIn jobs
                if row['site'] == 'linkedin' and pd.notna(row.get('description')):
                    description = str(row['description'])[:300] + "..." if len(str(row['description'])) > 300 else str(row['description'])
                    print(f"📝 Description Preview: {description}")
                print("=" * 100)
            
            # Save to CSV
            csv_filename = "product_owner_jobs_porto.csv"
            jobs.to_csv(csv_filename, quoting=csv.QUOTE_NONNUMERIC, escapechar="\\", index=False)
            print(f"\n💾 Results saved to: {csv_filename}")
            
            # Show some statistics
            print("\n📊 Statistics:")
            print(f"Jobs by site:")
            site_counts = jobs['site'].value_counts()
            for site, count in site_counts.items():
                print(f"  - {site}: {count} jobs")
                
            # Show job types if available
            if 'job_type' in jobs.columns and jobs['job_type'].notna().any():
                print(f"\nJob types:")
                job_type_counts = jobs['job_type'].value_counts()
                for job_type, count in job_type_counts.items():
                    if job_type:  # Skip None values
                        print(f"  - {job_type}: {count} jobs")
        else:
            print("❌ No jobs found. Try adjusting the search parameters.")
            
    except Exception as e:
        print(f"❌ Error occurred while scraping: {str(e)}")
        print("This might be due to rate limiting or network issues.")
        print("Try running the script again after a few minutes.")

if __name__ == "__main__":
    main()
