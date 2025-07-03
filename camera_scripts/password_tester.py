#!/usr/bin/env python3
"""
Password Testing Tool for Hikvision Camera
Tests different password formats and encoding
"""

import requests
from requests.auth import HTTPDigestAuth, HTTPBasicAuth
import urllib.parse
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_password_variations(ip, username, base_password):
    """Test different password encoding variations"""
    print(f"🔐 Testing password variations for: {base_password}")
    
    # Different password variations to try
    password_variations = [
        base_password,                           # Original
        urllib.parse.quote(base_password),       # URL encoded
        urllib.parse.quote_plus(base_password),  # URL encoded with +
        base_password.replace('@', '%40'),       # Manual @ encoding
        base_password.replace('@', '@'),         # Keep @ as is
        base_password.replace('%40', '@'),       # Decode if already encoded
        base_password.replace('%', '%25'),       # Double encoding
    ]
    
    # Remove duplicates while preserving order
    unique_passwords = []
    for pwd in password_variations:
        if pwd not in unique_passwords:
            unique_passwords.append(pwd)
    
    url = f"http://{ip}/ISAPI/System/deviceInfo"
    
    for i, password in enumerate(unique_passwords, 1):
        print(f"\n{i}. Testing password: '{password}'")
        
        # Test Digest Auth
        try:
            auth = HTTPDigestAuth(username, password)
            response = requests.get(url, auth=auth, timeout=5, verify=False)
            print(f"   Digest Auth: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ SUCCESS with Digest Auth!")
                print(f"   Working password: '{password}'")
                return password, "digest"
                
        except Exception as e:
            print(f"   Digest Auth Error: {e}")
        
        # Test Basic Auth
        try:
            auth = HTTPBasicAuth(username, password)
            response = requests.get(url, auth=auth, timeout=5, verify=False)
            print(f"   Basic Auth: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ SUCCESS with Basic Auth!")
                print(f"   Working password: '{password}'")
                return password, "basic"
                
        except Exception as e:
            print(f"   Basic Auth Error: {e}")
    
    return None, None

def test_common_passwords(ip, username):
    """Test common default passwords"""
    print(f"🔑 Testing common default passwords...")
    
    common_passwords = [
        "admin",
        "12345",
        "password", 
        "123456",
        "admin123",
        "Admin@123",
        "admin@123",
        "1234",
        "",  # Empty password
        "888888",
        "000000",
        "hikvision",
        "Admin123",
        "abcd1234",
    ]
    
    url = f"http://{ip}/ISAPI/System/deviceInfo"
    
    for password in common_passwords:
        print(f"\n🔍 Testing: '{password}'")
        
        for auth_type, auth_class in [("Digest", HTTPDigestAuth), ("Basic", HTTPBasicAuth)]:
            try:
                auth = auth_class(username, password)
                response = requests.get(url, auth=auth, timeout=3, verify=False)
                print(f"   {auth_type}: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"   ✅ SUCCESS! Password is: '{password}'")
                    return password, auth_type.lower()
                    
            except Exception as e:
                print(f"   {auth_type} Error: {e}")
    
    return None, None

def test_camera_with_working_auth(ip, username, password, auth_type):
    """Test camera controls once we have working authentication"""
    print(f"\n🎥 Testing camera controls with working authentication...")
    
    auth = HTTPDigestAuth(username, password) if auth_type == "digest" else HTTPBasicAuth(username, password)
    
    # Test different endpoints
    endpoints = [
        ("/ISAPI/System/deviceInfo", "Device Info"),
        ("/ISAPI/PTZ/channels/1/status", "PTZ Status"),
        ("/ISAPI/Streaming/channels/1/picture", "Capture Image"),
        ("/ISAPI/PTZ/channels/1/capabilities", "PTZ Capabilities"),
    ]
    
    working_endpoints = []
    
    for endpoint, description in endpoints:
        url = f"http://{ip}{endpoint}"
        try:
            response = requests.get(url, auth=auth, timeout=5, verify=False)
            print(f"✅ {description}: Status {response.status_code}")
            
            if response.status_code == 200:
                working_endpoints.append(endpoint)
                
        except Exception as e:
            print(f"❌ {description}: Error {e}")
    
    return working_endpoints

def main():
    """Main password testing function"""
    print("🔐 Hikvision Camera Password Tester")
    print("=" * 45)
    
    ip = input("Enter camera IP (default: 192.168.1.64): ").strip()
    ip = ip if ip else "192.168.1.64"
    
    username = input("Enter username (default: admin): ").strip()
    username = username if username else "admin"
    
    # Test 1: Common passwords
    print(f"\n🔍 Testing common default passwords...")
    password, auth_type = test_common_passwords(ip, username)
    
    if password is not None:
        print(f"\n🎉 Found working credentials!")
        print(f"   IP: {ip}")
        print(f"   Username: {username}")
        print(f"   Password: {password}")
        print(f"   Auth Type: {auth_type}")
        
        # Test camera controls
        working_endpoints = test_camera_with_working_auth(ip, username, password, auth_type)
        
        if working_endpoints:
            print(f"\n✅ Camera controls are accessible!")
            print("🎥 You can now use the enhanced camera control script")
        
        return
    
    # Test 2: User provided password variations
    user_password = input("\nEnter your suspected password: ").strip()
    if user_password:
        print(f"\n🔍 Testing variations of your password...")
        password, auth_type = test_password_variations(ip, username, user_password)
        
        if password is not None:
            print(f"\n🎉 Found working credentials!")
            print(f"   IP: {ip}")
            print(f"   Username: {username}")
            print(f"   Password: {password}")
            print(f"   Auth Type: {auth_type}")
            
            # Test camera controls
            working_endpoints = test_camera_with_working_auth(ip, username, password, auth_type)
            return
    
    # No success
    print(f"\n❌ Unable to find working password")
    print(f"\n💡 Next steps:")
    print(f"   1. Access camera web interface: http://{ip}")
    print(f"   2. Reset camera to factory defaults")
    print(f"   3. Check camera manual for default password")
    print(f"   4. Contact camera administrator")

if __name__ == "__main__":
    main()
