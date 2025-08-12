# test_cast.py
import pychromecast
import sys

if len(sys.argv) != 2:
    print("Usage: python test_cast.py 192.168.X.Y")
    sys.exit(1)

ip = sys.argv[1]
print(f"🔗 Trying simple connect to {ip}…")

try:
    print("🔍 First, let's see what devices are discoverable...")
    
    # Method 1: Basic discovery
    try:
        print("  Trying: get_chromecasts()")
        chromecasts, browser = pychromecast.get_chromecasts()
        print(f"  Found {len(chromecasts)} devices via get_chromecasts:")
        for i, c in enumerate(chromecasts):
            print(f"    {i+1}. {c.name} at {c.cast_info.host}:{c.cast_info.port}")
            if c.cast_info.host == ip:
                print(f"    ✅ MATCH! This is our target device")
        if browser:
            pychromecast.stop_discovery(browser)
    except Exception as e1:
        print(f"  ✗ get_chromecasts failed: {e1}")
    
    # Method 2: Listed discovery
    try:
        print("  Trying: get_listed_chromecasts()")
        chromecasts, browser = pychromecast.get_listed_chromecasts()
        print(f"  Found {len(chromecasts)} devices via get_listed_chromecasts:")
        for i, c in enumerate(chromecasts):
            print(f"    {i+1}. {c.name} at {c.cast_info.host}:{c.cast_info.port}")
            if c.cast_info.host == ip:
                print(f"    ✅ MATCH! This is our target device")
        if browser:
            pychromecast.stop_discovery(browser)
    except Exception as e2:
        print(f"  ✗ get_listed_chromecasts failed: {e2}")
    
    # Method 3: Discovery module
    try:
        print("  Trying: discovery module")
        import pychromecast.discovery as discovery
        services = discovery.discover_chromecasts(timeout=15)
        print(f"  Found {len(services)} services via discovery module:")
        for i, service in enumerate(services):
            print(f"    {i+1}. Service: {service}")
            if hasattr(service, 'addresses'):
                for addr in service.addresses:
                    addr_str = str(addr)
                    print(f"        Address: {addr_str}")
                    if addr_str == ip:
                        print(f"        ✅ MATCH! This service has our target IP")
    except Exception as e3:
        print(f"  ✗ Discovery module failed: {e3}")
    
    print("\n🎯 If no devices were found above, the issue is with discovery.")
    print("   This suggests:")
    print("   1. Google Home is not responding to mDNS")
    print("   2. Windows firewall is blocking multicast")
    print("   3. Network isolation is preventing discovery")
    print("   4. Google Home is in a different mode (guest network, etc.)")
    
    sys.exit(1)
        
except Exception as e:
    print(f"❌ Discovery test failed: {e!r}")
    sys.exit(2)
