#!/usr/bin/env python3
"""
Test script to check the correct pychromecast API for friendly_name
"""
import pychromecast
import sys

def test_chromecast_api():
    """Test the correct API for accessing device properties"""
    try:
        print(f"🔍 Testing pychromecast API")
        
        # Try discovery first
        print("🔍 Discovering devices...")
        chromecasts, browser = pychromecast.get_chromecasts(timeout=10)
        
        if chromecasts:
            cast = chromecasts[0]
            print(f"✅ Found device to test with")
            
            # Test different ways to get friendly name
            print("\n🧪 Testing different API methods:")
            
            # Method 1: Direct property
            try:
                name = cast.name
                print(f"✅ cast.name: {name}")
            except AttributeError as e:
                print(f"❌ cast.name failed: {e}")
            
            # Method 2: cast_info property
            try:
                if hasattr(cast, 'cast_info'):
                    name = cast.cast_info.friendly_name
                    print(f"✅ cast.cast_info.friendly_name: {name}")
                else:
                    print("❌ cast.cast_info not available")
            except AttributeError as e:
                print(f"❌ cast.cast_info.friendly_name failed: {e}")
            
            # Method 3: status property
            try:
                cast.wait(timeout=5)
                if hasattr(cast, 'status') and cast.status:
                    if hasattr(cast.status, 'display_name'):
                        name = cast.status.display_name
                        print(f"✅ cast.status.display_name: {name}")
                    else:
                        print("❌ cast.status.display_name not available")
                else:
                    print("❌ cast.status not available")
            except Exception as e:
                print(f"❌ cast.status failed: {e}")
            
            # Method 4: Check all available attributes
            print(f"\n🔍 Available cast attributes:")
            for attr in dir(cast):
                if not attr.startswith('_'):
                    try:
                        value = getattr(cast, attr)
                        if not callable(value):
                            print(f"  {attr}: {type(value)} = {str(value)[:50]}")
                    except:
                        print(f"  {attr}: <unable to access>")
            
        else:
            print("❌ No devices found for testing")
        
        if browser:
            pychromecast.stop_discovery(browser)
            
    except Exception as e:
        print(f"❌ API test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_chromecast_api()
