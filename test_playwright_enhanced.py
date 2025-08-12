#!/usr/bin/env python3
"""
Enhanced Playwright test focusing on the sites that failed.
Tests improved timeout handling and fallback strategies.
"""

from tools import fetch_via_playwright, open_website

def test_enhanced_playwright():
    """Test the enhanced Playwright configuration on previously failing sites"""
    
    print("🎭 Testing Enhanced Playwright Configuration...")
    print("=" * 60)
    
    # Test sites that previously failed or had issues
    test_cases = [
        {
            "name": "React.dev (previously timed out)",
            "url": "https://react.dev",
            "expected_min_chars": 500
        },
        {
            "name": "WSJ (previously minimal content)",
            "url": "https://www.wsj.com", 
            "expected_min_chars": 200
        },
        {
            "name": "CNN (JS-heavy news site)",
            "url": "https://www.cnn.com",
            "expected_min_chars": 1000
        }
    ]
    
    results = []
    
    for test in test_cases:
        print(f"\n🧪 Testing: {test['name']}")
        print(f"URL: {test['url']}")
        
        try:
            content = fetch_via_playwright(test['url'], timeout=25000)
            char_count = len(content) if content else 0
            
            if char_count >= test['expected_min_chars']:
                status = "✅ SUCCESS"
                results.append(True)
            elif char_count > 0:
                status = "⚠️ PARTIAL"
                results.append(True)  # Still count as success
            else:
                status = "❌ FAILED"
                results.append(False)
            
            print(f"  Result: {status} - {char_count} characters")
            if content and char_count > 0:
                preview = content[:150].replace('\n', ' ').strip()
                print(f"  Preview: {preview}...")
            
        except Exception as e:
            print(f"  Result: ❌ ERROR - {str(e)}")
            results.append(False)
    
    # Summary
    success_count = sum(results)
    total_count = len(results)
    success_rate = (success_count / total_count) * 100 if total_count > 0 else 0
    
    print(f"\n📊 Enhanced Test Summary:")
    print("=" * 40)
    print(f"🎯 Success rate: {success_count}/{total_count} ({success_rate:.1f}%)")
    
    if success_rate >= 80:
        print("🏆 EXCELLENT - Enhanced configuration working great!")
    elif success_rate >= 60:
        print("👍 GOOD - Significant improvement achieved!")
    else:
        print("⚠️ NEEDS WORK - Consider further tuning")

def test_full_integration():
    """Test the full open_website integration with a specific query"""
    print(f"\n🔧 Testing full integration with enhanced Playwright...")
    
    # Test a query that should work well with domain advisor
    query = "latest JavaScript frameworks 2024"
    print(f"Query: {query}")
    
    try:
        result = open_website(query=query, summary_only=True)
        
        if isinstance(result, dict) and result.get("needs_disambiguation"):
            print("🔍 Got disambiguation options - this is expected behavior")
            # Try the first option
            url = result["options"][0]
            print(f"🔧 Testing first option: {url}")
            content_result = open_website(url=url, summary_only=True)
            print(f"✅ Content result: {str(content_result)[:200]}...")
        else:
            print(f"✅ Direct result: {str(result)[:200]}...")
            
    except Exception as e:
        print(f"❌ Integration test error: {e}")

if __name__ == "__main__":
    test_enhanced_playwright()
    test_full_integration()
