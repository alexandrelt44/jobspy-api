#!/usr/bin/env python3
"""
Test the integrated Wellfound scraper with scrape.do
"""
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from jobspy import scrape_jobs

def test_wellfound_integration():
    """Test Wellfound scraper integration with scrape.do"""
    print("Testing integrated Wellfound scraper with scrape.do...")
    
    try:
        # Test with Europe location (we know this works)
        results = scrape_jobs(
            site_name=["wellfound"],
            search_term="Product Manager",
            location="Europe", 
            results_wanted=10,
            verbose=2,  # Maximum verbosity for detailed logs
        )
        
        print(f"\\n=== RESULTS ===")
        print(f"Found {len(results)} jobs")
        
        if len(results) > 0:
            print("\\nJobs found:")
            for i, row in results.head(5).iterrows():
                print(f"{i+1}. {row['title']} at {row['company']} - {row['location']}")
                print(f"   URL: {row['job_url']}")
                print(f"   Description: {row['description'][:100]}...")
            
            print("\\n✅ SUCCESS: Wellfound integration with scrape.do working!")
            return True
        else:
            print("❌ No jobs found.")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Wellfound scraper: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_portugal_fallback():
    """Test Portugal location to see if it works or falls back"""
    print("\\n" + "="*60)
    print("Testing Portugal location (might fallback to Europe)...")
    
    try:
        results = scrape_jobs(
            site_name=["wellfound"],
            search_term="Product Manager", 
            location="Portugal",
            results_wanted=5,
            verbose=1,
        )
        
        print(f"Portugal test found {len(results)} jobs")
        
        if len(results) > 0:
            print("Sample jobs:")
            for i, row in results.head(3).iterrows():
                print(f"  {i+1}. {row['title']} at {row['company']}")
        
        return len(results) > 0
        
    except Exception as e:
        print(f"Portugal test error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Wellfound integration with scrape.do...")
    
    # Test main integration
    success = test_wellfound_integration()
    
    # Test Portugal fallback
    portugal_success = test_portugal_fallback()
    
    print(f"\\n=== FINAL RESULTS ===")
    print(f"Europe test: {'✅ SUCCESS' if success else '❌ FAILED'}")
    print(f"Portugal test: {'✅ SUCCESS' if portugal_success else '❌ FAILED'}")
    
    if success:
        print("\\n🎉 Wellfound is now integrated and working with scrape.do!")
    else:
        print("\\n❌ Integration needs more work")