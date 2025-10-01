#!/usr/bin/env python3
"""
Debug script to examine Gupy HTML structure
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from jobspy.gupy.util import build_search_url
from jobspy.util import create_session
from bs4 import BeautifulSoup

def debug_gupy_html():
    """Debug the HTML structure of Gupy search results"""

    # Create session
    session = create_session(is_tls=False)

    # Build search URL
    search_url = build_search_url(
        search_term="desenvolvedor",
        location="São Paulo",
        page=1
    )

    print(f"Search URL: {search_url}")

    try:
        response = session.get(search_url, timeout=30)
        response.raise_for_status()

        print(f"Response status: {response.status_code}")
        print(f"Response length: {len(response.text)}")

        # Save raw HTML for inspection
        with open("gupy_raw_response.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        print("Raw HTML saved to gupy_raw_response.html")

        # Parse with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Look for potential job containers
        print("\n=== Looking for potential job containers ===")

        # Check for common job-related class names
        job_keywords = ['job', 'vaga', 'position', 'cargo', 'oportunidade']

        for keyword in job_keywords:
            elements = soup.find_all(class_=lambda x: x and keyword in x.lower())
            if elements:
                print(f"\nFound elements with '{keyword}' in class:")
                for i, elem in enumerate(elements[:3]):  # Show first 3
                    print(f"  {i+1}. Tag: {elem.name}, Class: {elem.get('class')}")
                    print(f"     Text preview: {elem.get_text(strip=True)[:100]}...")

        # Check for data-testid attributes
        testid_elements = soup.find_all(attrs={'data-testid': True})
        if testid_elements:
            print(f"\nFound {len(testid_elements)} elements with data-testid:")
            for elem in testid_elements[:5]:  # Show first 5
                print(f"  data-testid: {elem.get('data-testid')}")

        # Check for links that might be job URLs
        links = soup.find_all('a', href=True)
        job_links = [link for link in links if any(keyword in link.get('href', '').lower()
                                                  for keyword in ['job', 'vaga', 'career'])]
        if job_links:
            print(f"\nFound {len(job_links)} potential job links:")
            for link in job_links[:3]:  # Show first 3
                print(f"  URL: {link.get('href')}")
                print(f"  Text: {link.get_text(strip=True)[:50]}...")

        # Check for any structured data or JSON
        scripts = soup.find_all('script')
        json_scripts = []
        for script in scripts:
            if script.string and ('job' in script.string.lower() or 'vaga' in script.string.lower()):
                json_scripts.append(script)

        if json_scripts:
            print(f"\nFound {len(json_scripts)} scripts that might contain job data")
            for i, script in enumerate(json_scripts[:2]):  # Show first 2
                print(f"  Script {i+1} preview: {script.string[:200]}...")

        # Look for any cards or list items
        cards = soup.find_all(['div', 'article', 'section'],
                             class_=lambda x: x and any(term in x.lower()
                                                       for term in ['card', 'item', 'list']))
        if cards:
            print(f"\nFound {len(cards)} potential card/list elements:")
            for i, card in enumerate(cards[:3]):
                print(f"  Card {i+1}: {card.name}, Class: {card.get('class')}")
                print(f"     Text preview: {card.get_text(strip=True)[:100]}...")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_gupy_html()