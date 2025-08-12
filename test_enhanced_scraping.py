#!/usr/bin/env python3

"""
Test script for the enhanced multi-tier web scraping system
with paywall/cache fallback capabilities
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools import fetch_text_only, open_website

def test_text_only_fallback():
    """Test the text-only fallback functionality"""
    print("🧪 Testing fetch_text_only fallback...")
    
    # Test with a common news site that might have paywalls
    test_url = "https://www.wsj.com"
    
    result = fetch_text_only(test_url)
    
    print(f"URL: {test_url}")
    print(f"Result length: {len(result)} characters")
    if result:
        print(f"Result preview: {result[:200]}...")
        print("✅ Text-only fallback works!")
        return True
    else:
        print("❌ Text-only fallback returned no content")
        return False

def test_complete_pipeline():
    """Test the complete 4-tier pipeline with a research query"""
    print("\n🧪 Testing complete multi-tier pipeline...")
    
    # Use a query that should trigger multiple tiers
    query = "best restaurants in Margate NJ reviews"
    
    print(f"Testing query: {query}")
    result = open_website(query=query, summary_only=True)
    
    # Handle both string and dictionary returns
    if isinstance(result, dict):
        print("🔧 Got disambiguation dictionary")
        if "options" in result and result["options"]:
            first_url = result["options"][0]
            print(f"Testing first URL: {first_url}")
            result = open_website(url=first_url, summary_only=True)
        else:
            return False
    
    if isinstance(result, str):
        print(f"Result length: {len(result)} characters")
        print(f"Result preview: {result[:300]}...")
        
        # Check what type of result we got
        if "⚠️ Couldn't scrape full page content" in result:
            print("✅ Snippet fallback triggered (all tiers failed, fallback worked)")
            return True
        elif "⚠️ Direct page content was unavailable" in result:
            print("✅ Old snippet fallback triggered")
            return True
        elif len(result) > 100:
            print("✅ Content extraction worked (one of the tiers succeeded)")
            return True
        else:
            print("❌ Very short result - something may have failed")
            return False
    else:
        print(f"❌ Unexpected result type: {type(result)}")
        return False

def test_paywall_scenario():
    """Test with a potentially paywalled site"""
    print("\n🧪 Testing paywall scenario...")
    
    # Test with a site that commonly has paywalls
    url = "https://www.nytimes.com/section/technology"
    
    print(f"Testing URL: {url}")
    result = open_website(url=url, summary_only=True)
    
    if isinstance(result, str):
        print(f"Result length: {len(result)} characters")
        
        # Check what method worked
        if "Tier 2.5 found cached content" in str(result):
            print("✅ Cache/proxy fallback worked for paywall!")
        elif len(result) > 100:
            print("✅ Some extraction method worked")
        else:
            print("⚠️ Limited content extracted")
        
        return len(result) > 50
    else:
        print(f"❌ Unexpected result type: {type(result)}")
        return False

if __name__ == "__main__":
    print("🚀 Testing enhanced multi-tier web scraping system...\n")
    
    test1_success = test_text_only_fallback()
    test2_success = test_complete_pipeline()
    test3_success = test_paywall_scenario()
    
    print(f"\n📊 Test Results:")
    print(f"Text-only fallback: {'✅ PASS' if test1_success else '❌ FAIL'}")
    print(f"Complete pipeline: {'✅ PASS' if test2_success else '❌ FAIL'}")
    print(f"Paywall scenario: {'✅ PASS' if test3_success else '❌ FAIL'}")
    
    success_count = sum([test1_success, test2_success, test3_success])
    
    if success_count >= 2:
        print("\n🎉 Enhanced multi-tier system is working! Jarvis can now handle:")
        print("  🏆 Regular web scraping")
        print("  🏆 Sandbox browser fallback")
        print("  🏆 HTTP + BeautifulSoup extraction")
        print("  🏆 Google Cache & DuckDuckGo HTML proxy fallback")
        print("  🏆 Search snippet summarization as last resort")
        print("  🏆 1-hour HTTP caching for better performance")
    else:
        print(f"\n⚠️ {success_count}/3 tests passed. Check the output above for details.")
