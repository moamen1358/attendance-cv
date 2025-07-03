#!/usr/bin/env python3
"""
Simple Hikvision Camera Zoom & Focus Control
Two options: 
1. Zoom In (12mm) + Auto Focus
2. Zoom Out (2.8mm) + Auto Focus
"""

import requests
import time
import json
from requests.auth import HTTPDigestAuth

class SimpleZoomFocus:
    def __init__(self, ip="192.168.1.64", username="admin", password="Admin@123"):
        self.ip = ip
        self.username = username
        self.password = password
        self.auth = HTTPDigestAuth(username, password)
        self.base_url = f"http://{ip}"
        
        # Zoom settings for your camera (2.8mm to 12mm)
        self.zoom_wide = 1      # Minimum zoom (2.8mm)
        self.zoom_tele = 1000   # Maximum zoom (12mm) - will need to calibrate
        
        print(f"🎥 Simple Zoom & Focus Control")
        print(f"📡 Camera: {ip}")
        print(f"🔍 Zoom range: 2.8mm - 12mm")
        print("=" * 50)
    
    def test_connection(self):
        """Test camera connection"""
        try:
            url = f"{self.base_url}/ISAPI/System/deviceInfo"
            response = requests.get(url, auth=self.auth, timeout=5)
            if response.status_code == 200:
                print("✅ Camera connection successful!")
                return True
            else:
                print(f"❌ Camera connection failed. Status: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def get_current_zoom(self):
        """Get current zoom level"""
        try:
            url = f"{self.base_url}/ISAPI/Image/channels/1"
            response = requests.get(url, auth=self.auth, timeout=5)
            if response.status_code == 200:
                # Parse XML response to get zoom info
                content = response.text
                if "zoom" in content.lower():
                    print("📊 Current camera settings retrieved")
                    return True
            print("⚠️ Could not get current zoom level")
            return False
        except Exception as e:
            print(f"❌ Error getting zoom: {e}")
            return False
    
    def set_zoom_absolute(self, zoom_value):
        """Set absolute zoom position"""
        try:
            # Method 1: Try absolute zoom control
            url = f"{self.base_url}/ISAPI/PTZCtrl/channels/1/absolute"
            
            # XML payload for absolute zoom
            xml_data = f"""<?xml version="1.0" encoding="UTF-8"?>
<PTZData>
    <AbsoluteHigh>
        <zoom>{zoom_value}</zoom>
    </AbsoluteHigh>
</PTZData>"""
            
            headers = {'Content-Type': 'application/xml'}
            response = requests.put(url, data=xml_data, auth=self.auth, headers=headers, timeout=10)
            
            if response.status_code in [200, 204]:
                print(f"✅ Zoom set to {zoom_value}")
                return True
            else:
                print(f"⚠️ Zoom response: {response.status_code}")
                return self._try_alternative_zoom(zoom_value)
                
        except Exception as e:
            print(f"❌ Zoom error: {e}")
            return self._try_alternative_zoom(zoom_value)
    
    def _try_alternative_zoom(self, zoom_value):
        """Try alternative zoom method"""
        try:
            # Method 2: Try continuous zoom
            url = f"{self.base_url}/ISAPI/PTZCtrl/channels/1/continuous"
            
            # Determine zoom direction
            zoom_speed = 50 if zoom_value > 500 else -50
            zoom_time = 2.0  # seconds
            
            xml_data = f"""<?xml version="1.0" encoding="UTF-8"?>
<PTZData>
    <pan>0</pan>
    <tilt>0</tilt>
    <zoom>{zoom_speed}</zoom>
</PTZData>"""
            
            headers = {'Content-Type': 'application/xml'}
            
            # Start zoom
            response = requests.put(url, data=xml_data, auth=self.auth, headers=headers, timeout=5)
            if response.status_code in [200, 204]:
                print(f"🔄 Zooming {'in' if zoom_speed > 0 else 'out'}...")
                time.sleep(zoom_time)
                
                # Stop zoom
                stop_xml = """<?xml version="1.0" encoding="UTF-8"?>
<PTZData>
    <pan>0</pan>
    <tilt>0</tilt>
    <zoom>0</zoom>
</PTZData>"""
                requests.put(url, data=stop_xml, auth=self.auth, headers=headers, timeout=5)
                print("✅ Zoom completed")
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Alternative zoom failed: {e}")
            return False
    
    def auto_focus(self):
        """Trigger auto focus"""
        try:
            # Method 1: Try focus control
            url = f"{self.base_url}/ISAPI/Image/channels/1/focus"
            
            xml_data = """<?xml version="1.0" encoding="UTF-8"?>
<FocusData>
    <autoFocusMode>auto</autoFocusMode>
</FocusData>"""
            
            headers = {'Content-Type': 'application/xml'}
            response = requests.put(url, data=xml_data, auth=self.auth, headers=headers, timeout=10)
            
            if response.status_code in [200, 204]:
                print("🎯 Auto focus triggered")
                return True
            else:
                return self._try_alternative_focus()
                
        except Exception as e:
            print(f"⚠️ Focus method 1 failed, trying alternative...")
            return self._try_alternative_focus()
    
    def _try_alternative_focus(self):
        """Try alternative focus methods"""
        try:
            # Method 2: Try PTZ focus
            url = f"{self.base_url}/ISAPI/PTZCtrl/channels/1/momentary"
            
            xml_data = """<?xml version="1.0" encoding="UTF-8"?>
<PTZData>
    <pan>0</pan>
    <tilt>0</tilt>
    <zoom>0</zoom>
    <focus>1</focus>
</PTZData>"""
            
            headers = {'Content-Type': 'application/xml'}
            response = requests.put(url, data=xml_data, auth=self.auth, headers=headers, timeout=5)
            
            if response.status_code in [200, 204]:
                print("🎯 Auto focus activated")
                time.sleep(2)  # Give time for focus to complete
                return True
            else:
                print("⚠️ Focus may not be available on this camera")
                return False
                
        except Exception as e:
            print(f"❌ Focus error: {e}")
            return False
    
    def zoom_in_and_focus(self):
        """Option 1: Zoom to 12mm (telephoto) and auto focus"""
        print("\n🔍 OPTION 1: Zoom In (12mm) + Auto Focus")
        print("-" * 40)
        
        # Set zoom to maximum (12mm)
        if self.set_zoom_absolute(self.zoom_tele):
            print("📷 Zoomed to 12mm (telephoto)")
            time.sleep(1)  # Wait for zoom to complete
            
            # Auto focus
            if self.auto_focus():
                print("✅ Zoom in + focus completed!")
            else:
                print("⚠️ Zoom completed, but auto focus may have failed")
        else:
            print("❌ Zoom in failed")
    
    def zoom_out_and_focus(self):
        """Option 2: Zoom to 2.8mm (wide) and auto focus"""
        print("\n🔍 OPTION 2: Zoom Out (2.8mm) + Auto Focus")
        print("-" * 40)
        
        # Set zoom to minimum (2.8mm)
        if self.set_zoom_absolute(self.zoom_wide):
            print("📷 Zoomed to 2.8mm (wide angle)")
            time.sleep(1)  # Wait for zoom to complete
            
            # Auto focus
            if self.auto_focus():
                print("✅ Zoom out + focus completed!")
            else:
                print("⚠️ Zoom completed, but auto focus may have failed")
        else:
            print("❌ Zoom out failed")
    
    def capture_test_image(self, filename=None):
        """Capture a test image to verify zoom/focus"""
        try:
            if filename is None:
                filename = f"test_image_{int(time.time())}.jpg"
            
            url = f"{self.base_url}/ISAPI/Streaming/channels/1/picture"
            response = requests.get(url, auth=self.auth, timeout=10)
            
            if response.status_code == 200:
                with open(filename, 'wb') as f:
                    f.write(response.content)
                print(f"📸 Test image saved: {filename}")
                return filename
            else:
                print(f"❌ Image capture failed: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Image capture error: {e}")
            return None

def main():
    """Main control interface"""
    # Initialize camera controller
    camera = SimpleZoomFocus()
    
    # Test connection
    if not camera.test_connection():
        print("❌ Cannot connect to camera. Exiting.")
        return
    
    # Get current status
    camera.get_current_zoom()
    
    print("\n🎮 SIMPLE ZOOM & FOCUS CONTROL")
    print("=" * 50)
    print("1 - Zoom In (12mm) + Auto Focus")
    print("2 - Zoom Out (2.8mm) + Auto Focus")
    print("3 - Capture Test Image")
    print("q - Quit")
    print("=" * 50)
    
    while True:
        try:
            choice = input("\n👉 Choose option (1/2/3/q): ").strip().lower()
            
            if choice == '1':
                camera.zoom_in_and_focus()
            
            elif choice == '2':
                camera.zoom_out_and_focus()
            
            elif choice == '3':
                filename = f"zoom_test_{int(time.time())}.jpg"
                camera.capture_test_image(filename)
            
            elif choice == 'q':
                print("👋 Goodbye!")
                break
            
            else:
                print("❌ Invalid choice. Please enter 1, 2, 3, or q")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
