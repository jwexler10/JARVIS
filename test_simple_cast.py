# test_simple_cast.py
# Simple test to see what works with pychromecast

import pychromecast
import time

def test_simple_connection():
    """Test the simplest possible connection to Google Cast device."""
    
    print("🔍 Testing simple Cast connection methods...")
    
    # Method 1: Try basic discovery first
    print("\n1. Testing basic discovery...")
    try:
        chromecasts, browser = pychromecast.get_chromecasts()
        print(f"   Found {len(chromecasts)} devices via get_chromecasts")
        
        for cast in chromecasts:
            print(f"   - {cast.device.friendly_name} at {cast.host}:{cast.port}")
        
        if browser:
            pychromecast.stop_discovery(browser)
            
        if chromecasts:
            return chromecasts[0]  # Return first device found
            
    except Exception as e:
        print(f"   get_chromecasts failed: {e}")
    
    # Method 2: Try get_listed_chromecasts
    print("\n2. Testing get_listed_chromecasts...")
    try:
        chromecasts, browser = pychromecast.get_listed_chromecasts()
        print(f"   Found {len(chromecasts)} devices via get_listed_chromecasts")
        
        for cast in chromecasts:
            print(f"   - {cast.device.friendly_name} at {cast.host}:{cast.port}")
        
        if browser:
            pychromecast.stop_discovery(browser)
            
        if chromecasts:
            return chromecasts[0]  # Return first device found
            
    except Exception as e:
        print(f"   get_listed_chromecasts failed: {e}")
    
    # Method 3: Try discovery module
    print("\n3. Testing discovery module...")
    try:
        import pychromecast.discovery as discovery
        services = discovery.discover_chromecasts(timeout=10)
        print(f"   Found {len(services)} services")
        
        if services:
            # Try to connect to first service
            service = list(services)[0]
            print(f"   Trying to connect to service: {service}")
            
            # Extract connection info from service
            if hasattr(service, 'addresses') and service.addresses:
                host = str(service.addresses[0])
                port = service.port if hasattr(service, 'port') else 8009
                
                print(f"   Attempting connection to {host}:{port}")
                
                # Try creating Chromecast directly
                cast = pychromecast.Chromecast(host, port)
                cast.wait(timeout=10)
                
                print(f"   ✅ Connected to {cast.device.friendly_name}")
                return cast
                
    except Exception as e:
        print(f"   Discovery module failed: {e}")
    
    print("\n❌ All simple connection methods failed")
    return None

def test_device_functions(cast):
    """Test basic device functions."""
    if not cast:
        print("❌ No cast device to test")
        return
    
    print(f"\n🧪 Testing device functions for {cast.device.friendly_name}...")
    
    try:
        # Test getting status
        print(f"   Device model: {cast.device.model_name}")
        print(f"   Current volume: {int(cast.status.volume_level * 100)}%")
        print(f"   Is muted: {cast.status.volume_muted}")
        
        # Test volume control
        original_volume = cast.status.volume_level
        print(f"   Original volume: {int(original_volume * 100)}%")
        
        # Set volume to 30%
        cast.set_volume(0.3)
        time.sleep(1)
        print(f"   Set volume to 30%")
        
        # Restore original volume
        cast.set_volume(original_volume)
        time.sleep(1)
        print(f"   Restored volume to {int(original_volume * 100)}%")
        
        print("   ✅ Basic device functions work!")
        
    except Exception as e:
        print(f"   ❌ Device function test failed: {e}")

if __name__ == "__main__":
    print("🎯 Simple Cast Connection Test")
    cast = test_simple_connection()
    test_device_functions(cast)
    
    if cast:
        print(f"\n✅ SUCCESS: Connected to {cast.device.friendly_name}")
        print("   This device can be used for Jarvis integration!")
    else:
        print("\n❌ FAILED: Could not connect to any Cast device")
        print("   Check network connection and device availability")
