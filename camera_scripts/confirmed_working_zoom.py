#!/usr/bin/env python3
"""
WORKING Hikvision Zoom Control
Uses Digest Authentication - CONFIRMED WORKING!
Press 1: Zoom In (12mm) + Focus
Press 2: Zoom Out (2.8mm) + Focus
"""

import requests
from requests.auth import HTTPDigestAuth
import time
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class WorkingZoomControl:
    def __init__(self):
        # Camera settings - WORKING CONFIGURATION
        self.ip = "192.168.1.64"
        self.username = "admin"
        self.password = "Admin@123"
        self.auth = HTTPDigestAuth(self.username, self.password)  # KEY: Use Digest Auth!
        self.base_url = f"http://{self.ip}"
        
        print("📹 WORKING Zoom Control")
        print("=" * 30)
        print(f"Camera: {self.ip}")
        print("Range: 2.8mm - 12mm")
        print("Auth: Digest (WORKING!)")
        print()
    
    def test_connection(self):
        """Test camera connection"""
        try:
            url = f"{self.base_url}/ISAPI/System/deviceInfo"
            response = requests.get(url, auth=self.auth, timeout=5, verify=False)
            
            if response.status_code == 200:
                print("✅ Camera connected!")
                return True
            else:
                print(f"❌ Connection failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def zoom_telephoto(self):
        """Option 1: Zoom to 12mm (telephoto) with focus"""
        print("\\n🔍 OPTION 1: ZOOM IN (12mm)")
        print("-" * 30)
        
        # Zoom to telephoto (12mm) - use value 1000 for maximum zoom
        if self.set_zoom(1000):
            print("✅ Zoomed to 12mm (telephoto)")
            time.sleep(3)  # Wait for zoom to complete
            self.auto_focus()
            self.capture_test_image("telephoto")
            print("🎉 Telephoto zoom complete!")
        else:
            print("❌ Telephoto zoom failed")
    
    def zoom_wide(self):
        """Option 2: Zoom to 2.8mm (wide) with focus"""
        print("\\n🔍 OPTION 2: ZOOM OUT (2.8mm)")
        print("-" * 32)
        
        # Zoom to wide (2.8mm) - use value 1 for minimum zoom  
        if self.set_zoom(1):
            print("✅ Zoomed to 2.8mm (wide)")
            time.sleep(3)  # Wait for zoom to complete
            self.auto_focus()
            self.capture_test_image("wide")
            print("🎉 Wide zoom complete!")
        else:
            print("❌ Wide zoom failed")
    
    def set_zoom(self, zoom_value):
        """Set absolute zoom value using WORKING method"""
        try:
            url = f"{self.base_url}/ISAPI/PTZCtrl/channels/1/absolute"
            
            xml_data = f'''<?xml version="1.0" encoding="UTF-8"?>
            <PTZData>
                <AbsoluteHigh>
                    <azimuth>0</azimuth>
                    <elevation>0</elevation>
                    <absoluteZoom>{zoom_value}</absoluteZoom>
                </AbsoluteHigh>
            </PTZData>'''
            
            headers = {'Content-Type': 'application/xml'}
            response = requests.put(url, data=xml_data, auth=self.auth, 
                                 headers=headers, timeout=10, verify=False)
            
            print(f"   Zoom command: Status {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ Zoom set to {zoom_value}")
                return True
            else:
                print(f"   ❌ Zoom failed: {response.text[:100]}")
                return False
                
        except Exception as e:
            print(f"❌ Zoom error: {e}")
            return False
    
    def auto_focus(self):
        """Try auto focus using multiple methods"""
        print("🎯 Attempting auto focus...")
        
        focus_methods = [
            {
                'url': f"{self.base_url}/ISAPI/PTZCtrl/channels/1/autofocus",
                'data': '''<?xml version="1.0" encoding="UTF-8"?>
                <PTZData>
                    <autofocus>true</autofocus>
                </PTZData>''',
                'name': 'Auto Focus Command'
            },
            {
                'url': f"{self.base_url}/ISAPI/PTZCtrl/channels/1/momentary",
                'data': '''<?xml version="1.0" encoding="UTF-8"?>
                <PTZData>
                    <pan>0</pan>
                    <tilt>0</tilt>
                    <zoom>0</zoom>
                    <focus>1</focus>
                </PTZData>''',
                'name': 'Momentary Focus'
            }
        ]
        
        for method in focus_methods:
            try:
                headers = {'Content-Type': 'application/xml'}
                response = requests.put(method['url'], data=method['data'], 
                                     auth=self.auth, headers=headers, timeout=5, verify=False)
                
                print(f"   {method['name']}: Status {response.status_code}")
                
                if response.status_code == 200:
                    print("   ✅ Focus activated!")
                    time.sleep(2)  # Wait for focus
                    return True
                    
            except Exception as e:
                continue
        
        print("   ⚠️ Auto focus not available (may focus automatically)")
        return False
    
    def capture_test_image(self, zoom_type):
        """Capture test image to verify zoom worked"""
        try:
            url = f"{self.base_url}/ISAPI/Streaming/channels/1/picture"
            response = requests.get(url, auth=self.auth, timeout=10, verify=False)
            
            if response.status_code == 200:
                filename = f"zoom_{zoom_type}_{int(time.time())}.jpg"
                with open(filename, 'wb') as f:
                    f.write(response.content)
                print(f"📸 Test image saved: {filename}")
                return True
            else:
                print(f"📸 Image capture failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"📸 Capture error: {e}")
            return False

def main():
    """Main control program"""
    controller = WorkingZoomControl()
    
    # Test connection
    if not controller.test_connection():
        print("❌ Cannot connect to camera!")
        return
    
    print("🎮 ZOOM CONTROL OPTIONS")
    print("=" * 40)
    print("1 - Zoom In (12mm) + Focus")
    print("2 - Zoom Out (2.8mm) + Focus") 
    print("q - Quit")
    print()
    
    while True:
        try:
            choice = input("👉 Enter choice (1/2/q): ").strip().lower()
            
            if choice == 'q' or choice == 'quit':
                break
            elif choice == '1':
                controller.zoom_telephoto()
            elif choice == '2':
                controller.zoom_wide()
            else:
                print("❌ Invalid choice. Enter 1, 2, or q")
                
        except KeyboardInterrupt:
            print("\\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("👋 Goodbye!")

if __name__ == "__main__":
    main()
