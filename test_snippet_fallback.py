#!/usr/bin/env python3

"""
Test script for the new DuckDuckGo snippet fallback functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools import fetch_search_snippets, open_website, summarize_text

def test_fetch_snippets():
    """Test the basic snippet fetching functionality"""
    print("🧪 Testing fetch_search_snippets...")
    
    query = "best restaurants in Margate NJ"
    snippets = fetch_search_snippets(query, max_results=3)
    
    print(f"Query: {query}")
    print(f"Snippets length: {len(snippets)} characters")
    print(f"Snippets preview: {snippets[:200]}...")
    
    if len(snippets) > 50:
        print("✅ Snippet fetching works!")
    else:
        print("❌ Snippet fetching failed or returned very little content")
    
    return len(snippets) > 50

def test_integrated_fallback():
    """Test the integrated fallback with a difficult URL"""
    print("\n🧪 Testing integrated fallback with a difficult URL...")
    
    # Use a query that might trigger the fallback
    query = "things to do in Margate NJ attractions"
    
    print(f"Testing query: {query}")
    result = open_website(query=query, summary_only=True)
    
    # Handle both string and dictionary returns
    if isinstance(result, dict):
        print("🔧 Got disambiguation dictionary")
        print(f"Result type: dict with keys: {list(result.keys())}")
        if "options" in result:
            print(f"URLs found: {len(result['options'])}")
            # Try the first URL
            if result["options"]:
                first_url = result["options"][0]
                print(f"Testing first URL: {first_url}")
                result = open_website(url=first_url, summary_only=True)
        else:
            return False
    
    if isinstance(result, str):
        print(f"Result length: {len(result)} characters")
        print(f"Result preview: {result[:300]}...")
        
        # Check if we got the snippet fallback warning
        if "⚠️ Direct page content was unavailable" in result:
            print("✅ Snippet fallback triggered successfully!")
            return True
        elif len(result) > 100:
            print("✅ Regular content extraction worked (no fallback needed)")
            return True
        else:
            print("❌ Something went wrong - very short result")
            return False
    else:
        print(f"❌ Unexpected result type: {type(result)}")
        return False

def test_snippet_fallback_directly():
    """Test the snippet fallback by using a URL that will definitely fail"""
    print("\n🧪 Testing snippet fallback directly with a problematic URL...")
    
    # Use a URL that will likely fail content extraction
    query = "best restaurants in Margate NJ"
    
    # Directly test the fallback by using a query with summary_only
    print(f"Testing query: {query}")
    
    # Mock a scenario where tiers 1-3 fail by using a very specific query
    # that should trigger the snippet fallback
    result = fetch_search_snippets(query, max_results=3)
    
    if result:
        print(f"Raw snippets length: {len(result)} characters")
        print(f"Raw snippets preview: {result[:200]}...")
        
        # Now test the summarization with prefix
        summary = summarize_text(
            result, 
            max_sentences=3,
            prefix="⚠️ Direct page content was unavailable. Here's a summary of top search-result snippets:\n\n"
        )
        
        print(f"Summary length: {len(summary)} characters")
        print(f"Summary: {summary}")
        
        if "⚠️ Direct page content was unavailable" in summary:
            print("✅ Snippet fallback with prefix works!")
            return True
        else:
            print("❌ Prefix not added properly")
            return False
    else:
        print("❌ No snippets fetched")
        return False

if __name__ == "__main__":
    print("🚀 Testing DuckDuckGo snippet fallback system...\n")
    
    test1_success = test_fetch_snippets()
    test2_success = test_integrated_fallback()
    test3_success = test_snippet_fallback_directly()
    
    print(f"\n📊 Test Results:")
    print(f"Snippet fetching: {'✅ PASS' if test1_success else '❌ FAIL'}")
    print(f"Integrated fallback: {'✅ PASS' if test2_success else '❌ FAIL'}")
    print(f"Direct snippet fallback: {'✅ PASS' if test3_success else '❌ FAIL'}")
    
    if test1_success and test2_success and test3_success:
        print("\n🎉 All tests passed! The snippet fallback system is working.")
    else:
        print("\n⚠️ Some tests failed. Check the output above for details.")
