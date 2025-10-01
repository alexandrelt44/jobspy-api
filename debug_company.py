#!/usr/bin/env python3
"""
Debug company name extraction specifically
"""
import sys
import os
import re

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bs4 import BeautifulSoup
from urllib.parse import urljoin

def debug_company_extraction():
    """Debug the company name extraction specifically"""
    
    html_file = "debug_wellfound_https__wellfound.com_role_l_product-manager_porto.html"
    
    if not os.path.exists(html_file):
        print(f"❌ File {html_file} not found. Run debug_wellfound.py first.")
        return
    
    with open(html_file, 'r', encoding='utf-8') as f:
        html = f.read()
    
    soup = BeautifulSoup(html, 'html.parser')
    
    print("=== Company Analysis ===")
    
    # Find all company links
    company_links = soup.find_all('a', href=re.compile(r'/company/'))
    print(f"Found {len(company_links)} company links:")
    
    for i, link in enumerate(company_links[:5]):
        print(f"\n{i+1}. Company Link: {link.get('href')}")
        print(f"   Direct text: '{link.get_text().strip()}'")
        
        # Look for h2 within the link
        h2_elem = link.find('h2')
        if h2_elem:
            print(f"   H2 text: '{h2_elem.get_text().strip()}'")
        else:
            print("   No H2 found")
        
        # Look for span within the link
        span_elem = link.find('span')
        if span_elem:
            print(f"   Span text: '{span_elem.get_text().strip()}'")
        else:
            print("   No span found")
        
        # Look for any text-containing elements
        text_elements = link.find_all(text=True)
        non_empty_texts = [text.strip() for text in text_elements if text.strip()]
        print(f"   All texts: {non_empty_texts}")

    # Let's also check for the specific case - "Sword Health"
    print(f"\n=== Looking for Sword Health specifically ===")
    sword_elements = soup.find_all(text=re.compile(r'Sword Health', re.I))
    print(f"Found {len(sword_elements)} elements containing 'Sword Health':")
    
    for i, elem in enumerate(sword_elements):
        parent = elem.parent if elem.parent else None
        print(f"{i+1}. Text: '{elem.strip()}'")
        if parent:
            print(f"   Parent tag: <{parent.name}> with class: {parent.get('class', 'none')}")
            # Go up a few levels to see the context
            grandparent = parent.parent if parent.parent else None
            if grandparent:
                print(f"   Grandparent: <{grandparent.name}> with class: {grandparent.get('class', 'none')}")

if __name__ == "__main__":
    debug_company_extraction()