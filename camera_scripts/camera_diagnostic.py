#!/usr/bin/env python3
"""
Camera Network Diagnostic Tool
Helps troubleshoot Hikvision camera connection issues
"""

import requests
import socket
import subprocess
import platform
import time
from requests.auth import HTTPDigestAuth, HTTPBasicAuth
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def ping_test(ip_address):
    """Test if camera IP is reachable"""
    print(f"🏓 Ping test to {ip_address}...")
    
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, '3', ip_address]
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ Camera IP is reachable")
            return True
        else:
            print("❌ Camera IP is not reachable")
            return False
    except subprocess.TimeoutExpired:
        print("⏰ Ping timeout - camera may be unreachable")
        return False
    except Exception as e:
        print(f"❌ Ping error: {e}")
        return False

def port_scan(ip_address, ports=[80, 8080, 443, 554]):
    """Scan common camera ports"""
    print(f"🔍 Port scan on {ip_address}...")
    open_ports = []
    
    for port in ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((ip_address, port))
            if result == 0:
                print(f"✅ Port {port} is open")
                open_ports.append(port)
            else:
                print(f"❌ Port {port} is closed")
            sock.close()
        except Exception as e:
            print(f"❌ Error testing port {port}: {e}")
    
    return open_ports

def test_web_interface(ip_address, ports=[80, 8080]):
    """Test if camera web interface is accessible"""
    print(f"🌐 Testing web interface access...")
    
    for port in ports:
        for protocol in ['http', 'https']:
            url = f"{protocol}://{ip_address}:{port}"
            try:
                print(f"  🔄 Trying {url}...")
                response = requests.get(url, timeout=5, verify=False)
                print(f"    Status: {response.status_code}")
                if response.status_code in [200, 401, 403]:
                    print(f"✅ Web interface found at {url}")
                    return url
            except requests.exceptions.ConnectTimeout:
                print(f"    ⏰ Timeout")
            except requests.exceptions.ConnectionError:
                print(f"    ❌ Connection refused")
            except Exception as e:
                print(f"    ❌ Error: {e}")
    
    print("❌ No accessible web interface found")
    return None

def test_hikvision_auth(base_url, username, password):
    """Test different Hikvision authentication methods"""
    print(f"🔐 Testing Hikvision authentication...")
    
    auth_endpoints = [
        "/ISAPI/System/deviceInfo",
        "/ISAPI/System/status",
        "/doc/page/login.asp",
        "/",
    ]
    
    auth_methods = [
        ("Digest Auth", HTTPDigestAuth(username, password)),
        ("Basic Auth", HTTPBasicAuth(username, password)),
    ]
    
    for endpoint in auth_endpoints:
        print(f"\n  📍 Testing endpoint: {endpoint}")
        url = f"{base_url}{endpoint}"
        
        # Test without auth first
        try:
            response = requests.get(url, timeout=5, verify=False)
            print(f"    No Auth: {response.status_code}")
            if response.status_code == 200:
                print(f"    ✅ Endpoint accessible without authentication")
                continue
        except Exception as e:
            print(f"    No Auth Error: {e}")
        
        # Test with authentication
        for auth_name, auth_method in auth_methods:
            try:
                response = requests.get(url, auth=auth_method, timeout=5, verify=False)
                print(f"    {auth_name}: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"    ✅ {auth_name} successful on {endpoint}")
                    return auth_method, endpoint
                elif response.status_code == 401:
                    print(f"    🔐 {auth_name} authentication required")
                elif response.status_code == 403:
                    print(f"    🚫 {auth_name} forbidden (correct auth, no permission)")
                    
            except Exception as e:
                print(f"    {auth_name} Error: {e}")
    
    return None, None

def suggest_solutions(ip_address, username, password):
    """Suggest solutions based on diagnostic results"""
    print(f"\n💡 Troubleshooting Suggestions:")
    print("=" * 40)
    
    print("1. 🔧 Check Camera Configuration:")
    print(f"   - Access web interface: http://{ip_address}")
    print("   - Verify HTTP API is enabled")
    print("   - Check ISAPI service is running")
    
    print("\n2. 🔐 Authentication Issues:")
    print("   - Try default passwords: admin, 12345, password")
    print("   - Check if password contains special characters")
    print("   - Verify username is correct (usually 'admin')")
    
    print("\n3. 🌐 Network Issues:")
    print("   - Ensure camera and computer are on same network")
    print("   - Check firewall settings")
    print("   - Try different camera ports (80, 8080, 443)")
    
    print("\n4. 📱 Alternative Access Methods:")
    print("   - Use iVMS-4200 software")
    print("   - Access via mobile app first")
    print("   - Use ONVIF protocol if supported")
    
    print("\n5. 🔄 Reset Options:")
    print("   - Factory reset camera (hardware button)")
    print("   - Update camera firmware")
    print("   - Check Hikvision documentation")

def main():
    """Main diagnostic function"""
    print("🔧 Camera Network Diagnostic Tool")
    print("=" * 40)
    
    # Get parameters
    ip = input("Enter camera IP address: ").strip()
    username = input("Enter username (default: admin): ").strip() or "admin"
    password = input("Enter password: ").strip()
    
    if not ip:
        print("❌ IP address is required")
        return
    
    print(f"\n🔍 Diagnosing camera: {ip}")
    print("=" * 40)
    
    # Step 1: Ping test
    ping_success = ping_test(ip)
    
    # Step 2: Port scan
    open_ports = port_scan(ip)
    
    # Step 3: Web interface test
    web_url = test_web_interface(ip, open_ports if open_ports else [80, 8080])
    
    # Step 4: Authentication test
    if web_url and password:
        auth_method, working_endpoint = test_hikvision_auth(web_url, username, password)
        
        if auth_method and working_endpoint:
            print(f"\n✅ Found working authentication!")
            print(f"   URL: {web_url}{working_endpoint}")
            print(f"   Auth: {type(auth_method).__name__}")
        else:
            print(f"\n❌ Authentication failed on all endpoints")
    
    # Step 5: Suggestions
    suggest_solutions(ip, username, password)
    
    print(f"\n📋 Summary:")
    print(f"   Ping: {'✅' if ping_success else '❌'}")
    print(f"   Open Ports: {open_ports if open_ports else 'None found'}")
    print(f"   Web Interface: {'✅' if web_url else '❌'}")

if __name__ == "__main__":
    main()
