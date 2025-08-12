#!/usr/bin/env python3
"""
Test script to verify the enhanced open_website function with NoneType guards
and sandbox fallback works correctly.
"""

from tools import open_website

def test_margate_research():
    """Test the Margate NJ research query that was failing before"""
    print("Testing enhanced open_website function...")
    print("=" * 50)
    
    # Test the query that was failing before
    query = "Things to do in Margate NJ"
    print(f"🔍 Testing query: '{query}'")
    
    result = open_website(query=query)
    
    print(f"\n📊 Result type: {type(result)}")
    
    if isinstance(result, dict):
        print("✅ Received disambiguation dictionary")
        print(f"   - needs_disambiguation: {result.get('needs_disambiguation')}")
        print(f"   - Number of options: {len(result.get('options', []))}")
        print("   - Options:")
        for i, option in enumerate(result.get('options', []), 1):
            print(f"     {i}. {option}")
    else:
        print("✅ Received direct result")
        print(f"   Preview: {str(result)[:200]}...")
    
    print("\n" + "=" * 50)
    print("✅ Test completed successfully - no NoneType errors!")
    return result

if __name__ == "__main__":
    try:
        result = test_margate_research()
        print(f"\n🎉 Success! Function returned: {type(result)}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
