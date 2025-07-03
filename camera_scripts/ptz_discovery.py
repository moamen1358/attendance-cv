#!/usr/bin/env python3
"""
Hikvision PTZ Endpoint Discovery
Finds the correct endpoints for zoom and focus control
"""

import requests
import time
from requests.auth import HTTPDigestAuth
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class PTZEndpointDiscovery:
    def __init__(self, ip: str, username: str, password: str):
        self.ip = ip
        self.username = username
        self.password = password
        self.base_url = f"http://{ip}"
        self.auth = HTTPDigestAuth(username, password)
        
    def test_endpoints(self):
        """Test various PTZ endpoints"""
        
        print("🔍 Discovering PTZ Endpoints")
        print("=" * 50)
        
        # Common PTZ endpoints to test
        endpoints = [
            # Basic PTZ
            "/ISAPI/PTZCtrl/channels/1",
            "/ISAPI/PTZCtrl/channels/1/capabilities",
            "/ISAPI/PTZCtrl/channels/1/status",
            "/ISAPI/PTZCtrl/channels/1/continuous",
            "/ISAPI/PTZCtrl/channels/1/momentary",
            
            # Zoom specific
            "/ISAPI/PTZCtrl/channels/1/zoom",
            "/ISAPI/Image/channels/1/zoom",
            "/ISAPI/Streaming/channels/1/zoom",
            
            # Focus specific
            "/ISAPI/PTZCtrl/channels/1/focus",
            "/ISAPI/PTZCtrl/channels/1/autofocus",
            "/ISAPI/Image/channels/1/focus",
            "/ISAPI/Image/channels/1/autofocus",
            "/ISAPI/Streaming/channels/1/focus",
            
            # Alternative paths
            "/ISAPI/System/Video/inputs/channels/1/focus",
            "/ISAPI/ContentMgmt/InputProxy/channels/1/video/focus",
            
            # Image adjustment
            "/ISAPI/Image/channels/1",
            "/ISAPI/Image/channels/1/capabilities",
            
            # System capabilities
            "/ISAPI/System/capabilities",
            "/ISAPI/System/deviceInfo"
        ]
        
        working_endpoints = []
        
        for endpoint in endpoints:
            result = self.test_endpoint(endpoint, "GET")
            if result:
                working_endpoints.append((endpoint, "GET"))
                
            # Also test PUT for control endpoints
            if "PTZCtrl" in endpoint or "focus" in endpoint or "zoom" in endpoint:
                result = self.test_endpoint(endpoint, "PUT")
                if result:
                    working_endpoints.append((endpoint, "PUT"))
        
        print(f"\n✅ Working Endpoints ({len(working_endpoints)} found):")
        print("=" * 50)
        for endpoint, method in working_endpoints:
            print(f"   {method:4} {endpoint}")
        
        return working_endpoints
    
    def test_endpoint(self, endpoint: str, method: str = "GET"):
        """Test a single endpoint"""
        try:
            url = f"{self.base_url}{endpoint}"
            
            if method == "GET":
                response = requests.get(url, auth=self.auth, timeout=3, verify=False)
            elif method == "PUT":
                # Simple XML for PUT test
                xml_data = '''<?xml version="1.0" encoding="UTF-8"?>
                <test>
                    <value>0</value>
                </test>'''
                headers = {'Content-Type': 'application/xml'}
                response = requests.put(url, data=xml_data, auth=self.auth, 
                                      headers=headers, timeout=3, verify=False)
            else:
                return False
            
            status = response.status_code
            
            # Consider these as "working" endpoints
            if status in [200, 201, 204, 400]:  # 400 might mean wrong format but endpoint exists
                print(f"✅ {method:4} {endpoint:50} → {status}")
                return True
            elif status in [401, 403]:
                print(f"🔐 {method:4} {endpoint:50} → {status} (Auth)")
                return False
            elif status == 404:
                print(f"❌ {method:4} {endpoint:50} → {status} (Not Found)")
                return False
            else:
                print(f"❓ {method:4} {endpoint:50} → {status}")
                return False
                
        except requests.exceptions.Timeout:
            print(f"⏰ {method:4} {endpoint:50} → Timeout")
            return False
        except Exception as e:
            print(f"💥 {method:4} {endpoint:50} → Error: {e}")
            return False
    
    def test_zoom_methods(self):
        """Test different zoom control methods"""
        print("\n🔍 Testing Zoom Control Methods")
        print("=" * 40)
        
        # Method 1: Continuous PTZ with zoom
        print("\n1️⃣  Testing continuous PTZ zoom...")
        self.test_zoom_continuous()
        
        # Method 2: Direct zoom endpoint
        print("\n2️⃣  Testing direct zoom endpoint...")
        self.test_zoom_direct()
        
        # Method 3: Image channel zoom
        print("\n3️⃣  Testing image channel zoom...")
        self.test_zoom_image()
    
    def test_zoom_continuous(self):
        """Test zoom via continuous PTZ"""
        try:
            url = f"{self.base_url}/ISAPI/PTZCtrl/channels/1/continuous"
            
            # Test zoom in
            xml_data = '''<?xml version="1.0" encoding="UTF-8"?>
            <PTZData>
                <pan>0</pan>
                <tilt>0</tilt>
                <zoom>3</zoom>
            </PTZData>'''
            
            headers = {'Content-Type': 'application/xml'}
            response = requests.put(url, data=xml_data, auth=self.auth, 
                                  headers=headers, timeout=5, verify=False)
            
            print(f"   Zoom In: {response.status_code}")
            
            if response.status_code in [200, 204]:
                time.sleep(1)
                
                # Stop zoom
                xml_data = '''<?xml version="1.0" encoding="UTF-8"?>
                <PTZData>
                    <pan>0</pan>
                    <tilt>0</tilt>
                    <zoom>0</zoom>
                </PTZData>'''
                
                response = requests.put(url, data=xml_data, auth=self.auth, 
                                      headers=headers, timeout=5, verify=False)
                print(f"   Zoom Stop: {response.status_code}")
                
        except Exception as e:
            print(f"   Error: {e}")
    
    def test_zoom_direct(self):
        """Test direct zoom endpoint"""
        endpoints = [
            "/ISAPI/PTZCtrl/channels/1/zoom",
            "/ISAPI/Image/channels/1/zoom"
        ]
        
        for endpoint in endpoints:
            try:
                url = f"{self.base_url}{endpoint}"
                
                xml_data = '''<?xml version="1.0" encoding="UTF-8"?>
                <ZoomData>
                    <zoom>50</zoom>
                </ZoomData>'''
                
                headers = {'Content-Type': 'application/xml'}
                response = requests.put(url, data=xml_data, auth=self.auth, 
                                      headers=headers, timeout=5, verify=False)
                
                print(f"   {endpoint}: {response.status_code}")
                
            except Exception as e:
                print(f"   {endpoint}: Error - {e}")
    
    def test_zoom_image(self):
        """Test zoom via image channel"""
        try:
            url = f"{self.base_url}/ISAPI/Image/channels/1"
            
            # Get current settings first
            response = requests.get(url, auth=self.auth, timeout=5, verify=False)
            print(f"   Get Image Settings: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   Response length: {len(response.content)} bytes")
                
        except Exception as e:
            print(f"   Error: {e}")

def main():
    # Camera settings
    camera_ip = "192.168.1.64"
    username = "admin"
    password = "Admin@123"
    
    # Initialize discovery
    discovery = PTZEndpointDiscovery(camera_ip, username, password)
    
    # Test all endpoints
    working_endpoints = discovery.test_endpoints()
    
    # Test zoom methods
    discovery.test_zoom_methods()
    
    print(f"\n📋 Summary: Found {len(working_endpoints)} working endpoints")

if __name__ == "__main__":
    main()
