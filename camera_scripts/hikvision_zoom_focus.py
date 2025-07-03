#!/usr/bin/env python3
"""
Hikvision Camera Zoom and Focus Control
Uses proper ISAPI endpoints for PTZ operations
"""

import requests
import time
import json
import xml.etree.ElementTree as ET
from requests.auth import HTTPDigestAuth
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class HikvisionZoomFocus:
    def __init__(self, ip: str, username: str, password: str, channel: int = 1):
        self.ip = ip
        self.username = username
        self.password = password
        self.channel = channel
        self.base_url = f"http://{ip}"
        self.auth = HTTPDigestAuth(username, password)
        
        print(f"🎥 Hikvision Zoom/Focus Controller")
        print(f"📡 Camera: {ip}")
        print(f"👤 User: {username}")
        print(f"📺 Channel: {channel}")
        
    def test_connection(self):
        """Test basic connection to camera"""
        try:
            url = f"{self.base_url}/ISAPI/System/deviceInfo"
            response = requests.get(url, auth=self.auth, timeout=5, verify=False)
            if response.status_code == 200:
                print("✅ Camera connection successful")
                return True
            else:
                print(f"❌ Connection failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def get_ptz_capabilities(self):
        """Get PTZ capabilities"""
        try:
            url = f"{self.base_url}/ISAPI/PTZCtrl/channels/{self.channel}/capabilities"
            response = requests.get(url, auth=self.auth, timeout=5, verify=False)
            
            if response.status_code == 200:
                print("✅ PTZ Capabilities retrieved")
                
                # Parse XML to check zoom and focus support
                root = ET.fromstring(response.content)
                
                # Look for zoom capabilities
                zoom_elements = root.findall(".//absoluteZoom") or root.findall(".//relativeZoom")
                focus_elements = root.findall(".//absoluteFocus") or root.findall(".//relativeFocus")
                
                print(f"🔍 Zoom support: {'✅' if zoom_elements else '❌'}")
                print(f"🎯 Focus support: {'✅' if focus_elements else '❌'}")
                
                return True
            else:
                print(f"❌ PTZ capabilities failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ PTZ capabilities error: {e}")
            return False
    
    def zoom_in(self, speed: int = 4):
        """Zoom in (speed: 1-7, where 7 is fastest)"""
        return self._continuous_zoom("ZOOMIN", speed)
    
    def zoom_out(self, speed: int = 4):
        """Zoom out (speed: 1-7, where 7 is fastest)"""
        return self._continuous_zoom("ZOOMOUT", speed)
    
    def focus_near(self, speed: int = 4):
        """Focus to near (speed: 1-7, where 7 is fastest)"""
        return self._continuous_focus("FOCUSNEAR", speed)
    
    def focus_far(self, speed: int = 4):
        """Focus to far (speed: 1-7, where 7 is fastest)"""
        return self._continuous_focus("FOCUSFAR", speed)
    
    def auto_focus(self):
        """Trigger auto focus"""
        try:
            url = f"{self.base_url}/ISAPI/PTZCtrl/channels/{self.channel}/autofocus"
            
            # XML payload for auto focus
            xml_data = '''<?xml version="1.0" encoding="UTF-8"?>
            <PTZData>
                <autofocus>true</autofocus>
            </PTZData>'''
            
            headers = {
                'Content-Type': 'application/xml',
                'Accept': 'application/xml'
            }
            
            response = requests.put(url, data=xml_data, auth=self.auth, 
                                  headers=headers, timeout=5, verify=False)
            
            if response.status_code in [200, 204]:
                print("✅ Auto focus triggered")
                return True
            else:
                print(f"❌ Auto focus failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Auto focus error: {e}")
            return False
    
    def _continuous_zoom(self, direction: str, speed: int):
        """Internal method for continuous zoom operations"""
        try:
            # Start zoom
            if self._start_continuous_action(direction, speed):
                print(f"🔍 {direction} at speed {speed}")
                return True
            return False
            
        except Exception as e:
            print(f"❌ Zoom error: {e}")
            return False
    
    def _continuous_focus(self, direction: str, speed: int):
        """Internal method for continuous focus operations"""
        try:
            # Start focus
            if self._start_continuous_action(direction, speed):
                print(f"🎯 {direction} at speed {speed}")
                return True
            return False
            
        except Exception as e:
            print(f"❌ Focus error: {e}")
            return False
    
    def _start_continuous_action(self, action: str, speed: int):
        """Start a continuous PTZ action"""
        try:
            url = f"{self.base_url}/ISAPI/PTZCtrl/channels/{self.channel}/continuous"
            
            # XML payload for continuous action
            xml_data = f'''<?xml version="1.0" encoding="UTF-8"?>
            <PTZData>
                <pan>0</pan>
                <tilt>0</tilt>
                <zoom>{speed if 'ZOOM' in action else 0}</zoom>
                <momentaryDuration>PT1S</momentaryDuration>
            </PTZData>'''
            
            # Adjust XML based on action type
            if action == "ZOOMIN":
                xml_data = f'''<?xml version="1.0" encoding="UTF-8"?>
                <PTZData>
                    <pan>0</pan>
                    <tilt>0</tilt>
                    <zoom>{speed}</zoom>
                </PTZData>'''
            elif action == "ZOOMOUT":
                xml_data = f'''<?xml version="1.0" encoding="UTF-8"?>
                <PTZData>
                    <pan>0</pan>
                    <tilt>0</tilt>
                    <zoom>-{speed}</zoom>
                </PTZData>'''
            elif action in ["FOCUSNEAR", "FOCUSFAR"]:
                # Focus might use different endpoint
                return self._focus_action(action, speed)
            
            headers = {
                'Content-Type': 'application/xml',
                'Accept': 'application/xml'
            }
            
            response = requests.put(url, data=xml_data, auth=self.auth, 
                                  headers=headers, timeout=5, verify=False)
            
            if response.status_code in [200, 204]:
                return True
            else:
                print(f"❌ Action failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Action error: {e}")
            return False
    
    def _focus_action(self, action: str, speed: int):
        """Handle focus actions with alternative endpoints"""
        try:
            # Try focus-specific endpoint
            url = f"{self.base_url}/ISAPI/PTZCtrl/channels/{self.channel}/focus"
            
            direction = "near" if action == "FOCUSNEAR" else "far"
            
            xml_data = f'''<?xml version="1.0" encoding="UTF-8"?>
            <FocusData>
                <focus>{direction}</focus>
                <speed>{speed}</speed>
            </FocusData>'''
            
            headers = {
                'Content-Type': 'application/xml',
                'Accept': 'application/xml'
            }
            
            response = requests.put(url, data=xml_data, auth=self.auth, 
                                  headers=headers, timeout=5, verify=False)
            
            if response.status_code in [200, 204]:
                return True
            else:
                # Try alternative format
                return self._focus_alternative(action, speed)
                
        except Exception as e:
            print(f"❌ Focus action error: {e}")
            return False
    
    def _focus_alternative(self, action: str, speed: int):
        """Alternative focus control method"""
        try:
            url = f"{self.base_url}/ISAPI/PTZCtrl/channels/{self.channel}/momentary"
            
            xml_data = f'''<?xml version="1.0" encoding="UTF-8"?>
            <PTZData>
                <pan>0</pan>
                <tilt>0</tilt>
                <zoom>0</zoom>
                <focus>{speed if action == "FOCUSFAR" else -speed}</focus>
                <momentaryDuration>PT1S</momentaryDuration>
            </PTZData>'''
            
            headers = {
                'Content-Type': 'application/xml',
                'Accept': 'application/xml'
            }
            
            response = requests.put(url, data=xml_data, auth=self.auth, 
                                  headers=headers, timeout=5, verify=False)
            
            if response.status_code in [200, 204]:
                return True
            else:
                print(f"❌ Alternative focus failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Alternative focus error: {e}")
            return False
    
    def stop_all_movement(self):
        """Stop all PTZ movements"""
        try:
            url = f"{self.base_url}/ISAPI/PTZCtrl/channels/{self.channel}/continuous"
            
            xml_data = '''<?xml version="1.0" encoding="UTF-8"?>
            <PTZData>
                <pan>0</pan>
                <tilt>0</tilt>
                <zoom>0</zoom>
            </PTZData>'''
            
            headers = {
                'Content-Type': 'application/xml',
                'Accept': 'application/xml'
            }
            
            response = requests.put(url, data=xml_data, auth=self.auth, 
                                  headers=headers, timeout=5, verify=False)
            
            if response.status_code in [200, 204]:
                print("⏹️  All movements stopped")
                return True
            else:
                print(f"❌ Stop failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Stop error: {e}")
            return False
    
    def get_current_position(self):
        """Get current zoom and focus position"""
        try:
            url = f"{self.base_url}/ISAPI/PTZCtrl/channels/{self.channel}/status"
            response = requests.get(url, auth=self.auth, timeout=5, verify=False)
            
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                
                # Extract position data
                zoom = root.find(".//zoom")
                focus = root.find(".//focus")
                
                zoom_val = zoom.text if zoom is not None else "N/A"
                focus_val = focus.text if focus is not None else "N/A"
                
                print(f"📊 Current Position:")
                print(f"   🔍 Zoom: {zoom_val}")
                print(f"   🎯 Focus: {focus_val}")
                
                return {"zoom": zoom_val, "focus": focus_val}
            else:
                print(f"❌ Status failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Status error: {e}")
            return None

def main():
    """Interactive zoom and focus control"""
    
    # Camera settings
    camera_ip = "192.168.1.64"
    username = "admin"
    password = "Admin@123"
    
    # Initialize controller
    controller = HikvisionZoomFocus(camera_ip, username, password)
    
    # Test connection
    if not controller.test_connection():
        print("❌ Cannot connect to camera!")
        return
    
    # Get capabilities
    controller.get_ptz_capabilities()
    
    # Get current position
    controller.get_current_position()
    
    print("\n🎮 Zoom and Focus Controls")
    print("=" * 40)
    print("Commands:")
    print("  zi [speed] - Zoom In (speed 1-7, default 4)")
    print("  zo [speed] - Zoom Out (speed 1-7, default 4)")
    print("  fn [speed] - Focus Near (speed 1-7, default 4)")
    print("  ff [speed] - Focus Far (speed 1-7, default 4)")
    print("  af         - Auto Focus")
    print("  stop       - Stop all movement")
    print("  status     - Get current position")
    print("  quit       - Exit")
    print()
    
    while True:
        try:
            cmd = input("Enter command: ").strip().lower().split()
            
            if not cmd:
                continue
                
            action = cmd[0]
            speed = int(cmd[1]) if len(cmd) > 1 else 4
            
            if action in ['quit', 'exit', 'q']:
                break
            elif action == 'zi':
                controller.zoom_in(speed)
            elif action == 'zo':
                controller.zoom_out(speed)
            elif action == 'fn':
                controller.focus_near(speed)
            elif action == 'ff':
                controller.focus_far(speed)
            elif action == 'af':
                controller.auto_focus()
            elif action == 'stop':
                controller.stop_all_movement()
            elif action == 'status':
                controller.get_current_position()
            else:
                print("❌ Unknown command. Type 'quit' to exit.")
                
        except KeyboardInterrupt:
            print("\n⏹️  Stopping all movements...")
            controller.stop_all_movement()
            break
        except ValueError:
            print("❌ Invalid speed value. Use 1-7.")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n👋 Goodbye!")

if __name__ == "__main__":
    main()
