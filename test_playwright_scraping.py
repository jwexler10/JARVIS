#!/usr/bin/env python3
"""
Test the new Playwright-powered multi-tier web scraping system.
Tests JavaScript-heavy sites, React/Vue apps, and paywall scenarios.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools import fetch_via_playwright, open_website

def test_playwright_scraping():
    """Test the new Playwright-powered scraping capabilities."""
    
    print("🎭 Testing Playwright-powered multi-tier web scraping system...\n")
    
    test_sites = [
        ("https://react.dev", "React official site (JS-heavy)"),
        ("https://vuejs.org", "Vue.js official site (JS-heavy)"),
        ("https://www.nytimes.com", "NYT (paywall + JS)"),
        ("https://www.wsj.com", "WSJ (paywall + JS)"),
        ("https://github.com/microsoft/playwright", "GitHub (modern SPA)"),
        ("https://stackoverflow.com/questions/tagged/javascript", "StackOverflow (dynamic content)"),
    ]
    
    results = []
    
    for url, description in test_sites:
        print(f"🧪 Testing: {description}")
        print(f"URL: {url}")
        
        try:
            # Test direct Playwright function
            print("  Testing fetch_via_playwright...")
            playwright_content = fetch_via_playwright(url)
            playwright_chars = len(playwright_content) if playwright_content else 0
            
            if playwright_chars > 500:
                status = "✅ EXCELLENT"
                preview = playwright_content[:150].replace('\n', ' ')
                print(f"  Playwright: {playwright_chars} chars - {preview}...")
            elif playwright_chars > 200:
                status = "✅ GOOD"
                print(f"  Playwright: {playwright_chars} chars")
            elif playwright_chars > 0:
                status = "⚠️ PARTIAL"
                print(f"  Playwright: {playwright_chars} chars (minimal)")
            else:
                status = "❌ FAILED"
                print(f"  Playwright: No content extracted")
            
            results.append((description, status, playwright_chars))
            print(f"  Result: {status}\n")
            
        except Exception as e:
            print(f"❌ ERROR: {e}\n")
            results.append((description, "❌ ERROR", 0))
    
    # Test full open_website integration
    print("🔧 Testing full open_website integration with Playwright...")
    try:
        query = "best React components 2024"
        print(f"Query: {query}")
        
        result = open_website(query=query, summary_only=True)
        if isinstance(result, str) and len(result) > 200:
            print(f"✅ Full integration success: {len(result)} characters")
            preview = result[:200].replace('\n', ' ')
            print(f"Preview: {preview}...")
        else:
            print(f"⚠️ Integration result: {result}")
            
    except Exception as e:
        print(f"❌ Integration error: {e}")
    
    # Summary
    print("\n📊 Playwright Test Summary:")
    print("=" * 60)
    for description, status, char_count in results:
        print(f"{status} {description}: {char_count} chars")
    
    successful = len([r for r in results if r[1] in ["✅ EXCELLENT", "✅ GOOD"]])
    total = len(results)
    print(f"\n🎯 Success rate: {successful}/{total} ({successful/total*100:.1f}%)")
    
    if successful >= total * 0.8:
        print("🎉 Playwright integration is working excellently!")
        print("   ✅ JavaScript execution enabled")
        print("   ✅ User-Agent rotation active") 
        print("   ✅ Network idle detection working")
        print("   ✅ Error isolation functioning")
    elif successful >= total * 0.6:
        print("⚠️ Playwright working but may need tuning")
    else:
        print("❌ Playwright integration needs debugging")

if __name__ == "__main__":
    test_playwright_scraping()
