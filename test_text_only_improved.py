#!/usr/bin/env python3
"""
Test the improved fetch_text_only function with various website types.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools import fetch_text_only

def test_fetch_text_only():
    """Test the improved text-only fallback with various site types."""
    
    test_sites = [
        ("https://www.wsj.com", "Paywall site (WSJ)"),
        ("https://www.nytimes.com", "Paywall site (NYT)"),
        ("https://en.wikipedia.org/wiki/Python_(programming_language)", "Wikipedia (should work)"),
        ("https://httpbin.org/html", "Simple test site"),
        ("https://example.com", "Basic HTML site")
    ]
    
    print("🔧 Testing improved fetch_text_only function...\n")
    
    results = []
    
    for url, description in test_sites:
        print(f"🧪 Testing {description}")
        print(f"URL: {url}")
        
        try:
            content = fetch_text_only(url)
            char_count = len(content) if content else 0
            
            print(f"Result: {char_count} characters")
            
            if char_count > 200:
                preview = content[:200].replace('\n', ' ')
                print(f"Preview: {preview}...")
                status = "✅ SUCCESS"
            elif char_count > 0:
                print(f"Content: {content[:100]}...")
                status = "⚠️ PARTIAL"
            else:
                status = "❌ FAILED"
            
            results.append((description, status, char_count))
            print(f"Status: {status}\n")
            
        except Exception as e:
            print(f"❌ ERROR: {e}\n")
            results.append((description, "❌ ERROR", 0))
    
    # Summary
    print("📊 Test Summary:")
    print("=" * 50)
    for description, status, char_count in results:
        print(f"{status} {description}: {char_count} chars")
    
    successful = len([r for r in results if r[1] == "✅ SUCCESS"])
    total = len(results)
    print(f"\n🎯 Success rate: {successful}/{total} ({successful/total*100:.1f}%)")

if __name__ == "__main__":
    test_fetch_text_only()
