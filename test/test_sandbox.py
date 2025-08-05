#!/usr/bin/env python3
"""
Phase 5B: Test script for Docker-Based Sandbox integration
Test all sandbox tools to ensure they're working correctly.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from tools import (
    check_sandbox_health,
    open_page_sandbox, 
    get_page_title_sandbox,
    get_page_url_sandbox,
    extract_text_sandbox,
    click_sandbox,
    fill_input_sandbox,
    wait_for_element_sandbox,
    get_element_attribute_sandbox,
    reset_sandbox
)

def test_sandbox_integration():
    """Test all sandbox tools to ensure they work correctly."""
    
    print("🔧 Phase 5B: Testing Docker-Based Sandbox Integration")
    print("=" * 60)
    
    # Test 1: Health Check
    print("\n1. Testing sandbox health...")
    try:
        health = check_sandbox_health()
        print(f"✅ Health check: {health}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        print("Make sure to run the sandbox first: python run_sandbox.ps1")
        return False
    
    # Test 2: Open Page
    print("\n2. Testing page opening...")
    try:
        result = open_page_sandbox("https://httpbin.org/html")
        print(f"✅ Page opened: {result}")
    except Exception as e:
        print(f"❌ Page opening failed: {e}")
        return False
    
    # Test 3: Get Page Title
    print("\n3. Testing page title extraction...")
    try:
        title = get_page_title_sandbox()
        print(f"✅ Page title: {title}")
    except Exception as e:
        print(f"❌ Title extraction failed: {e}")
        return False
    
    # Test 4: Get Page URL
    print("\n4. Testing URL extraction...")
    try:
        url = get_page_url_sandbox()
        print(f"✅ Current URL: {url}")
    except Exception as e:
        print(f"❌ URL extraction failed: {e}")
        return False
    
    # Test 5: Extract Text
    print("\n5. Testing text extraction...")
    try:
        text = extract_text_sandbox("h1")
        print(f"✅ Extracted text: {text}")
    except Exception as e:
        print(f"❌ Text extraction failed: {e}")
        return False
    
    # Test 6: Open a form page
    print("\n6. Testing form interaction...")
    try:
        result = open_page_sandbox("https://httpbin.org/forms/post")
        print(f"✅ Form page opened: {result}")
        
        # Test input filling
        fill_result = fill_input_sandbox("input[name='custname']", "Jarvis Test")
        print(f"✅ Input filled: {fill_result}")
        
        # Test getting attribute
        attr_result = get_element_attribute_sandbox("input[name='custname']", "value")
        print(f"✅ Input value: {attr_result}")
        
    except Exception as e:
        print(f"❌ Form interaction failed: {e}")
        return False
    
    # Test 7: Wait for element (should be immediate since page is loaded)
    print("\n7. Testing element waiting...")
    try:
        wait_result = wait_for_element_sandbox("form", timeout=5)
        print(f"✅ Element waiting: {wait_result}")
    except Exception as e:
        print(f"❌ Element waiting failed: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 All sandbox tests passed! Jarvis is ready for web automation.")
    print("\nYou can now use commands like:")
    print("- 'Open google.com in sandbox'")
    print("- 'Search for Python tutorial'") 
    print("- 'Click the first result'")
    print("- 'Extract the page title'")
    
    return True

if __name__ == "__main__":
    test_sandbox_integration()
