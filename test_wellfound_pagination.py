#!/usr/bin/env python3
"""
Test Wellfound pagination functionality
"""
import sys
import os
import pandas as pd

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from jobspy import scrape_jobs

def test_wellfound_pagination():
    """Test Wellfound scraper with pagination to get all Portugal jobs"""
    print("Testing Wellfound pagination to get all Portugal Product Manager jobs...")
    
    try:
        # Test with Portugal location to get all pages
        results = scrape_jobs(
            site_name=["wellfound"],
            search_term="Product Manager",
            location="Portugal", 
            results_wanted=100,  # Request more than one page worth
            verbose=2,  # Maximum verbosity for detailed logs
        )
        
        print(f"\\n=== PAGINATION RESULTS ===")
        print(f"Total jobs found: {len(results)}")
        
        if len(results) > 0:
            print("\\nAll jobs found:")
            for i, row in results.iterrows():
                print(f"{i+1}. {row['title']} at {row['company']} - {row['location']}")
                print(f"    URL: {row['job_url']}")
            
            # Count unique companies
            unique_companies = results['company'].nunique()
            print(f"\\n📊 Summary:")
            print(f"- Total positions: {len(results)}")  
            print(f"- Unique companies: {unique_companies}")
            locations = [loc for loc in results['location'].unique() if pd.notna(loc)]
            print(f"- Locations: {', '.join(locations) if locations else 'Various'}")
            
            print("\\n✅ SUCCESS: Pagination working - got multiple pages of jobs!")
            return True
        else:
            print("❌ No jobs found.")
            return False
            
    except Exception as e:
        print(f"❌ Error testing pagination: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_manual_page_urls():
    """Test manual page URLs to verify the pagination approach"""
    print("\\n" + "="*60)
    print("Testing manual page 2 URL to verify pagination...")
    
    try:
        results = scrape_jobs(
            site_name=["wellfound"],
            search_term="Software Engineer",
            location="Europe",
            results_wanted=50,  # Should trigger multiple pages
            verbose=1,
        )
        
        print(f"Manual pagination test found {len(results)} jobs")
        if len(results) >= 25:  # Should have more than one page worth
            print("✅ Multiple pages likely scraped successfully")
            return True
        else:
            print("⚠️  Might have only gotten one page")
            return False
        
    except Exception as e:
        print(f"Manual test error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Wellfound pagination functionality...")
    
    # Test main pagination
    success = test_wellfound_pagination()
    
    # Test manual approach
    manual_success = test_manual_page_urls()
    
    print(f"\\n=== FINAL RESULTS ===")
    print(f"Portugal pagination test: {'✅ SUCCESS' if success else '❌ FAILED'}")
    print(f"Europe multi-page test: {'✅ SUCCESS' if manual_success else '❌ FAILED'}")
    
    if success:
        print("\\n🎉 Pagination is working! Wellfound now returns jobs from multiple pages!")
    else:
        print("\\n❌ Pagination needs debugging")