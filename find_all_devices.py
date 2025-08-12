#!/usr/bin/env python3
"""
Comprehensive Google Home Device Discovery
Find all Chromecast devices on the network and their details
"""
import pychromecast
import time

def discover_all_devices():
    """Discover all Google Home/Chromecast devices on the network"""
    print("🔍 Comprehensive Google Home Discovery")
    print("=" * 50)
    
    try:
        print("🌐 Starting network discovery (this may take 10-15 seconds)...")
        
        # Method 1: Standard discovery with longer timeout
        print("\n📡 Method 1: Standard Discovery")
        chromecasts, browser = pychromecast.get_chromecasts(timeout=15)
        
        if chromecasts:
            print(f"✅ Found {len(chromecasts)} device(s):")
            for i, cast in enumerate(chromecasts, 1):
                print(f"\n  Device {i}:")
                print(f"    Name: {cast.name}")
                print(f"    Model: {cast.model_name}")
                print(f"    IP Address: {cast.cast_info.host}")
                print(f"    Port: {cast.cast_info.port}")
                print(f"    Type: {cast.cast_type}")
                print(f"    UUID: {cast.uuid}")
                
                # Check if it's Jacy's room speaker
                if "jacy" in cast.name.lower():
                    print(f"    🎯 THIS IS JACY'S ROOM SPEAKER!")
                elif "family" in cast.name.lower():
                    print(f"    🏠 This is the Family Room speaker")
        else:
            print("❌ No devices found via standard discovery")
        
        # Stop browser
        if browser:
            pychromecast.stop_discovery(browser)
        
        # Method 2: Discovery module for more details
        print("\n📡 Method 2: Discovery Module")
        try:
            import pychromecast.discovery as discovery
            services = discovery.discover_chromecasts(timeout=15)
            
            if services:
                print(f"✅ Found {len(services)} service(s):")
                for i, service in enumerate(services, 1):
                    if hasattr(service, 'friendly_name'):  # It's a CastInfo object
                        print(f"\n  Service {i}:")
                        print(f"    Name: {service.friendly_name}")
                        print(f"    Model: {service.model_name}")
                        print(f"    IP Address: {service.host}")
                        print(f"    Port: {service.port}")
                        print(f"    Type: {service.cast_type}")
                        print(f"    UUID: {service.uuid}")
                        
                        # Check if it's Jacy's room speaker
                        if "jacy" in service.friendly_name.lower():
                            print(f"    🎯 THIS IS JACY'S ROOM SPEAKER!")
                        elif "family" in service.friendly_name.lower():
                            print(f"    🏠 This is the Family Room speaker")
                    else:
                        print(f"  Service {i}: {type(service)} - {service}")
            else:
                print("❌ No services found via discovery module")
        except Exception as e:
            print(f"❌ Discovery module failed: {e}")
        
        print("\n" + "=" * 50)
        print("🎯 SUMMARY:")
        print("Look for a device named 'Jacy's room speaker' or similar.")
        print("If you see it, update the IP in google_home_direct.py")
        print("If you don't see it, check:")
        print("  1. Is the device powered on?")
        print("  2. Is it connected to the same WiFi network?")
        print("  3. Try saying 'Hey Google, what's my IP address?' to the device")
        
    except Exception as e:
        print(f"❌ Discovery failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    discover_all_devices()
