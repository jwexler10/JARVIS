#!/usr/bin/env python3
"""
Simple test to check if Google Home is responding on Cast port
"""
import socket
import time

def test_port_connection(ip, port, timeout=5):
    """Test if a port is open on the given IP"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()
        return result == 0
    except Exception as e:
        print(f"Socket test failed: {e}")
        return False

def main():
    google_home_ip = "192.168.1.29"
    cast_port = 8009
    
    print(f"🔍 Testing Google Home at {google_home_ip}")
    print(f"📡 Checking if port {cast_port} is open...")
    
    if test_port_connection(google_home_ip, cast_port):
        print(f"✅ Port {cast_port} is OPEN on {google_home_ip}")
        print("   Your Google Home is responding on the Cast port!")
        
        # Test other common ports
        other_ports = [8008, 8443]
        for port in other_ports:
            if test_port_connection(google_home_ip, port):
                print(f"✅ Port {port} is also open")
            else:
                print(f"❌ Port {port} is closed")
                
    else:
        print(f"❌ Port {cast_port} is CLOSED on {google_home_ip}")
        print("   Possible issues:")
        print("   1. Google Home is not at this IP address")
        print("   2. Google Home is not powered on")
        print("   3. Firewall is blocking the connection")
        print("   4. Google Home is in a different mode")
        
        # Test if the IP responds to ping
        print(f"\n🏓 Testing ping to {google_home_ip}...")
        import subprocess
        try:
            result = subprocess.run(
                ["ping", "-n", "1", google_home_ip], 
                capture_output=True, 
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                print(f"✅ {google_home_ip} responds to ping")
                print("   The device is online but Cast port may be blocked")
            else:
                print(f"❌ {google_home_ip} does not respond to ping")
                print("   The device may be offline or at a different IP")
        except Exception as e:
            print(f"❌ Ping test failed: {e}")

if __name__ == "__main__":
    main()
