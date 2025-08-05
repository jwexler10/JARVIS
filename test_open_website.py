#!/usr/bin/env python3
"""
Test script for the new open_website function
"""

import sys
import os

# Add the current directory to Python path to import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_open_website():
    """Test the open_website function with various inputs"""
    try:
        from tools import open_website
        print("✅ Successfully imported open_website function")
        
        # Test 1: URL detection
        print("\n🧪 Test 1: URL detection")
        test_url = "https://www.google.com"
        result = open_website(test_url)
        print(f"Input: {test_url}")
        print(f"Result: {result}")
        
        # Test 2: Search query (if sandbox is running)
        print("\n🧪 Test 2: Search query")
        test_query = "Python programming"
        result = open_website(test_query)
        print(f"Input: {test_query}")
        print(f"Result: {result}")
        
        # Test 3: URL with selector (if sandbox is running)
        print("\n🧪 Test 3: URL with selector")
        result = open_website("https://www.google.com", "title")
        print(f"Input: https://www.google.com with selector 'title'")
        print(f"Result: {result}")
        
        print("\n✅ All tests completed successfully!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Testing open_website function...")
    success = test_open_website()
    if success:
        print("\n🎉 Test completed successfully!")
    else:
        print("\n💥 Test failed!")
        sys.exit(1)
