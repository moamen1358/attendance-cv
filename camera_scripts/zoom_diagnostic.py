#!/usr/bin/env python3
"""
Hikvision Camera Zoom Diagnostic Tool
Tests different zoom methods to find what works
"""

import requests
import xml.etree.ElementTree as ET
import time
import urllib3

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ZoomDiagnostic:
    def __init__(self, ip="192.168.1.64", username="admin", password="Admin@123"):
        self.ip = ip
        self.username = username
        self.password = password
        self.auth = (username, password)  # Use the working credentials
        self.base_url = f"http://{ip}"
        
    def test_connection(self):
        """Test basic connection"""
        try:
            url = f"{self.base_url}/ISAPI/System/deviceInfo"
            response = requests.get(url, auth=self.auth, timeout=5, verify=False)
            
            if response.status_code == 200:
                print("✅ Camera connection successful!")
                
                # Parse device info
                root = ET.fromstring(response.text)
                model = root.find('.//model')
                if model is not None:
                    print(f"📷 Camera Model: {model.text}")
                return True
            else:
                print(f"❌ Connection failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def check_ptz_capabilities(self):
        """Check what PTZ capabilities are supported"""
        print("\n🔍 Checking PTZ Capabilities...")
        print("-" * 40)
        
        endpoints = [
            "/ISAPI/PTZCtrl/channels/1/capabilities",
            "/ISAPI/System/capabilities",
            "/ISAPI/Image/channels/1/capabilities"
        ]
        
        for endpoint in endpoints:
            try:
                url = f"{self.base_url}{endpoint}"
                response = requests.get(url, auth=self.auth, timeout=5, verify=False)
                
                print(f"📍 {endpoint}: Status {response.status_code}")
                
                if response.status_code == 200:
                    # Look for zoom-related content
                    content = response.text.lower()
                    if 'zoom' in content:
                        print("   ✅ Contains zoom capabilities")
                        
                        # Try to parse and find zoom info
                        try:
                            root = ET.fromstring(response.text)
                            zoom_elements = (root.findall(".//absoluteZoom") + 
                                           root.findall(".//relativeZoom") + 
                                           root.findall(".//continuousZoom"))
                            
                            for elem in zoom_elements:
                                print(f"   📍 Found: {elem.tag}")
                                
                        except:
                            pass
                    else:
                        print("   ❌ No zoom capabilities found")
                        
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
    def test_current_position(self):
        """Get current PTZ position"""
        print("\n📍 Getting Current Position...")
        print("-" * 30)
        
        endpoints = [
            "/ISAPI/PTZCtrl/channels/1/status",
            "/ISAPI/PTZCtrl/channels/1/position", 
            "/ISAPI/Image/channels/1"
        ]
        
        for endpoint in endpoints:
            try:
                url = f"{self.base_url}{endpoint}"
                response = requests.get(url, auth=self.auth, timeout=5, verify=False)
                
                print(f"📍 {endpoint}: Status {response.status_code}")
                
                if response.status_code == 200:
                    print(f"   Response length: {len(response.text)} chars")
                    
                    # Look for position/zoom info
                    content = response.text.lower()
                    if 'zoom' in content or 'position' in content:
                        print("   ✅ Contains position/zoom data")
                        try:
                            root = ET.fromstring(response.text)
                            
                            # Look for zoom values
                            zoom_elements = (root.findall(".//zoom") + 
                                           root.findall(".//absoluteZoom") +
                                           root.findall(".//zoomLevel"))
                            
                            for elem in zoom_elements:
                                print(f"   🔍 {elem.tag}: {elem.text}")
                                
                        except Exception as e:
                            print(f"   ⚠️ Parse error: {e}")
                            
            except Exception as e:
                print(f"   ❌ Error: {e}")
    
    def test_zoom_methods(self):
        """Test different zoom control methods"""
        print("\n🔧 Testing Zoom Control Methods...")
        print("-" * 40)
        
        # Method 1: Absolute zoom control
        self.test_absolute_zoom()
        
        # Method 2: Continuous zoom
        self.test_continuous_zoom()
        
        # Method 3: Relative zoom
        self.test_relative_zoom()
        
    def test_absolute_zoom(self):
        """Test absolute zoom positioning"""
        print("\n1️⃣ Testing Absolute Zoom...")
        
        endpoints = [
            "/ISAPI/PTZCtrl/channels/1/absolute",
            "/ISAPI/PTZCtrl/channels/1/position",
            "/ISAPI/Image/channels/1/zoom"
        ]
        
        for endpoint in endpoints:
            try:
                url = f"{self.base_url}{endpoint}"
                
                # Try different XML formats
                xml_formats = [
                    # Format 1: Standard PTZ
                    '''<?xml version="1.0" encoding="UTF-8"?>
                    <PTZData>
                        <AbsoluteHigh>
                            <azimuth>0</azimuth>
                            <elevation>0</elevation>
                            <absoluteZoom>500</absoluteZoom>
                        </AbsoluteHigh>
                    </PTZData>''',
                    
                    # Format 2: Simple PTZ
                    '''<?xml version="1.0" encoding="UTF-8"?>
                    <PTZData>
                        <zoom>500</zoom>
                    </PTZData>''',
                    
                    # Format 3: Image zoom
                    '''<?xml version="1.0" encoding="UTF-8"?>
                    <ZoomData>
                        <zoom>500</zoom>
                    </ZoomData>''',
                    
                    # Format 4: Direct zoom
                    '''<?xml version="1.0" encoding="UTF-8"?>
                    <zoom>500</zoom>'''
                ]
                
                print(f"   📍 Testing {endpoint}")
                
                for i, xml_data in enumerate(xml_formats, 1):
                    try:
                        headers = {'Content-Type': 'application/xml'}
                        response = requests.put(url, data=xml_data, auth=self.auth, 
                                             headers=headers, timeout=5, verify=False)
                        
                        print(f"     Format {i}: Status {response.status_code}")
                        
                        if response.status_code in [200, 204]:
                            print(f"     ✅ SUCCESS with format {i}!")
                            return True
                        elif response.status_code == 404:
                            print(f"     📍 Endpoint not supported")
                            break
                        else:
                            print(f"     ❌ Failed: {response.text[:50]}...")
                            
                    except Exception as e:
                        print(f"     ❌ Error: {e}")
                        
            except Exception as e:
                print(f"   ❌ Endpoint error: {e}")
                
        return False
    
    def test_continuous_zoom(self):
        """Test continuous zoom control"""
        print("\n2️⃣ Testing Continuous Zoom...")
        
        endpoint = "/ISAPI/PTZCtrl/channels/1/continuous"
        url = f"{self.base_url}{endpoint}"
        
        # Test zoom in
        xml_data = '''<?xml version="1.0" encoding="UTF-8"?>
        <PTZData>
            <pan>0</pan>
            <tilt>0</tilt>
            <zoom>3</zoom>
        </PTZData>'''
        
        try:
            headers = {'Content-Type': 'application/xml'}
            response = requests.put(url, data=xml_data, auth=self.auth, 
                                 headers=headers, timeout=5, verify=False)
            
            print(f"   Zoom In: Status {response.status_code}")
            
            if response.status_code in [200, 204]:
                print("   ✅ Continuous zoom started!")
                time.sleep(2)
                
                # Stop zoom
                stop_xml = '''<?xml version="1.0" encoding="UTF-8"?>
                <PTZData>
                    <pan>0</pan>
                    <tilt>0</tilt>
                    <zoom>0</zoom>
                </PTZData>'''
                
                requests.put(url, data=stop_xml, auth=self.auth, headers=headers, timeout=5, verify=False)
                print("   ⏹️ Zoom stopped")
                return True
            else:
                print(f"   ❌ Failed: {response.text[:50]}...")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            
        return False
    
    def test_relative_zoom(self):
        """Test relative zoom control"""
        print("\n3️⃣ Testing Relative Zoom...")
        
        endpoint = "/ISAPI/PTZCtrl/channels/1/relative"
        url = f"{self.base_url}{endpoint}"
        
        xml_data = '''<?xml version="1.0" encoding="UTF-8"?>
        <PTZData>
            <RelativeHigh>
                <azimuth>0</azimuth>
                <elevation>0</elevation>
                <relativeZoom>100</relativeZoom>
            </RelativeHigh>
        </PTZData>'''
        
        try:
            headers = {'Content-Type': 'application/xml'}
            response = requests.put(url, data=xml_data, auth=self.auth, 
                                 headers=headers, timeout=5, verify=False)
            
            print(f"   Relative Zoom: Status {response.status_code}")
            
            if response.status_code in [200, 204]:
                print("   ✅ Relative zoom working!")
                return True
            else:
                print(f"   ❌ Failed: {response.text[:50]}...")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            
        return False

def main():
    """Run diagnostic tests"""
    print("🔧 Hikvision Camera Zoom Diagnostic")
    print("=" * 50)
    
    diagnostic = ZoomDiagnostic()
    
    # Test connection
    if not diagnostic.test_connection():
        print("❌ Cannot connect to camera. Exiting.")
        return
    
    # Check capabilities
    diagnostic.check_ptz_capabilities()
    
    # Get current position
    diagnostic.test_current_position()
    
    # Test zoom methods
    diagnostic.test_zoom_methods()
    
    print("\n🔍 Diagnostic Complete!")
    print("Look for ✅ SUCCESS messages above to see which zoom method works.")

if __name__ == "__main__":
    main()
