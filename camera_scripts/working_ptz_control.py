#!/usr/bin/env python3
"""
Hikvision Camera Zoom and Focus Control (Working Version)
Uses the correct endpoints discovered from the camera
"""

import requests
import time
import json
import xml.etree.ElementTree as ET
from requests.auth import HTTPDigestAuth
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class HikvisionPTZController:
    def __init__(self, ip: str, username: str, password: str, channel: int = 1):
        self.ip = ip
        self.username = username
        self.password = password
        self.channel = channel
        self.base_url = f"http://{ip}"
        self.auth = HTTPDigestAuth(username, password)
        
        print(f"🎥 Hikvision PTZ Controller (Working Version)")
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
    
    def get_ptz_status(self):
        """Get current PTZ status"""
        try:
            url = f"{self.base_url}/ISAPI/PTZCtrl/channels/{self.channel}/status"
            response = requests.get(url, auth=self.auth, timeout=5, verify=False)
            
            if response.status_code == 200:
                print("✅ PTZ Status retrieved")
                
                # Parse XML response
                root = ET.fromstring(response.content)
                
                # Extract current position
                pan = root.find(".//azimuth")
                tilt = root.find(".//elevation")
                zoom = root.find(".//absoluteZoom")
                
                pan_val = pan.text if pan is not None else "N/A"
                tilt_val = tilt.text if tilt is not None else "N/A"
                zoom_val = zoom.text if zoom is not None else "N/A"
                
                print(f"📊 Current PTZ Status:")
                print(f"   🔄 Pan (Azimuth): {pan_val}")
                print(f"   ↕️  Tilt (Elevation): {tilt_val}")
                print(f"   🔍 Zoom: {zoom_val}")
                
                return {"pan": pan_val, "tilt": tilt_val, "zoom": zoom_val}
            else:
                print(f"❌ PTZ status failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ PTZ status error: {e}")
            return None
    
    def zoom_in(self, speed: int = 4, duration: float = 1.0):
        """Zoom in for specified duration"""
        print(f"🔍 Zooming IN (speed: {speed}, duration: {duration}s)")
        
        # Start zoom in
        if self._start_zoom(speed):
            time.sleep(duration)
            # Stop zoom
            self._stop_zoom()
            return True
        return False
    
    def zoom_out(self, speed: int = 4, duration: float = 1.0):
        """Zoom out for specified duration"""
        print(f"🔍 Zooming OUT (speed: {speed}, duration: {duration}s)")
        
        # Start zoom out
        if self._start_zoom(-speed):
            time.sleep(duration)
            # Stop zoom
            self._stop_zoom()
            return True
        return False
    
    def _start_zoom(self, speed: int):
        """Start continuous zoom (positive = in, negative = out)"""
        try:
            url = f"{self.base_url}/ISAPI/PTZCtrl/channels/{self.channel}/continuous"
            
            xml_data = f'''<?xml version="1.0" encoding="UTF-8"?>
            <PTZData>
                <pan>0</pan>
                <tilt>0</tilt>
                <zoom>{speed}</zoom>
            </PTZData>'''
            
            headers = {
                'Content-Type': 'application/xml',
                'Accept': 'application/xml'
            }
            
            response = requests.put(url, data=xml_data, auth=self.auth, 
                                  headers=headers, timeout=5, verify=False)
            
            if response.status_code == 200:
                return True
            else:
                print(f"❌ Zoom start failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Zoom start error: {e}")
            return False
    
    def _stop_zoom(self):
        """Stop zoom movement"""
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
            
            if response.status_code == 200:
                print("   ⏹️  Zoom stopped")
                return True
            else:
                print(f"   ❌ Zoom stop failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ Zoom stop error: {e}")
            return False
    
    def focus_adjustment(self, direction: str, duration: float = 0.5):
        """Adjust focus (direction: 'near' or 'far')"""
        print(f"🎯 Focus adjustment: {direction.upper()} (duration: {duration}s)")
        
        try:
            url = f"{self.base_url}/ISAPI/System/Video/inputs/channels/{self.channel}/focus"
            
            # Try different XML formats for focus
            xml_formats = [
                f'''<?xml version="1.0" encoding="UTF-8"?>
                <FocusConfiguration>
                    <focusMode>manual</focusMode>
                    <direction>{direction}</direction>
                    <speed>5</speed>
                </FocusConfiguration>''',
                
                f'''<?xml version="1.0" encoding="UTF-8"?>
                <VideoInputChannel>
                    <focus>
                        <mode>manual</mode>
                        <direction>{direction}</direction>
                    </focus>
                </VideoInputChannel>''',
                
                f'''<?xml version="1.0" encoding="UTF-8"?>
                <focus>
                    <direction>{direction}</direction>
                    <duration>{duration}</duration>
                </focus>'''
            ]
            
            headers = {
                'Content-Type': 'application/xml',
                'Accept': 'application/xml'
            }
            
            for i, xml_data in enumerate(xml_formats, 1):
                print(f"   Trying format {i}...")
                response = requests.put(url, data=xml_data, auth=self.auth, 
                                      headers=headers, timeout=5, verify=False)
                
                print(f"   Response: {response.status_code}")
                
                if response.status_code in [200, 204]:
                    print(f"   ✅ Focus {direction} successful!")
                    return True
                elif response.status_code == 400:
                    print(f"   Response text: {response.text[:200]}")
            
            print(f"   ❌ All focus formats failed")
            return False
                
        except Exception as e:
            print(f"❌ Focus error: {e}")
            return False
    
    def focus_near(self, duration: float = 0.5):
        """Focus to near objects"""
        return self.focus_adjustment("near", duration)
    
    def focus_far(self, duration: float = 0.5):
        """Focus to far objects"""
        return self.focus_adjustment("far", duration)
    
    def get_image_settings(self):
        """Get current image settings (might include focus info)"""
        try:
            url = f"{self.base_url}/ISAPI/Image/channels/{self.channel}"
            response = requests.get(url, auth=self.auth, timeout=5, verify=False)
            
            if response.status_code == 200:
                print("✅ Image settings retrieved")
                
                # Parse XML to look for focus information
                root = ET.fromstring(response.content)
                
                # Look for focus-related elements
                focus_elements = root.findall(".//focus") + root.findall(".//Focus")
                zoom_elements = root.findall(".//zoom") + root.findall(".//Zoom")
                
                if focus_elements:
                    print("🎯 Focus settings found:")
                    for elem in focus_elements:
                        print(f"   {elem.tag}: {elem.text}")
                
                if zoom_elements:
                    print("🔍 Zoom settings found:")
                    for elem in zoom_elements:
                        print(f"   {elem.tag}: {elem.text}")
                
                return True
            else:
                print(f"❌ Image settings failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Image settings error: {e}")
            return False
    
    def pan_tilt(self, pan_speed: int = 0, tilt_speed: int = 0, duration: float = 1.0):
        """Pan and tilt camera (for testing)"""
        print(f"🔄 Pan: {pan_speed}, Tilt: {tilt_speed} (duration: {duration}s)")
        
        try:
            url = f"{self.base_url}/ISAPI/PTZCtrl/channels/{self.channel}/continuous"
            
            # Start movement
            xml_data = f'''<?xml version="1.0" encoding="UTF-8"?>
            <PTZData>
                <pan>{pan_speed}</pan>
                <tilt>{tilt_speed}</tilt>
                <zoom>0</zoom>
            </PTZData>'''
            
            headers = {
                'Content-Type': 'application/xml',
                'Accept': 'application/xml'
            }
            
            response = requests.put(url, data=xml_data, auth=self.auth, 
                                  headers=headers, timeout=5, verify=False)
            
            if response.status_code == 200:
                time.sleep(duration)
                
                # Stop movement
                xml_data = '''<?xml version="1.0" encoding="UTF-8"?>
                <PTZData>
                    <pan>0</pan>
                    <tilt>0</tilt>
                    <zoom>0</zoom>
                </PTZData>'''
                
                response = requests.put(url, data=xml_data, auth=self.auth, 
                                      headers=headers, timeout=5, verify=False)
                
                print("   ✅ Pan/Tilt completed")
                return True
            else:
                print(f"❌ Pan/Tilt failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Pan/Tilt error: {e}")
            return False

def main():
    """Interactive PTZ control"""
    
    # Camera settings
    camera_ip = "192.168.1.64"
    username = "admin"
    password = "Admin@123"
    
    # Initialize controller
    controller = HikvisionPTZController(camera_ip, username, password)
    
    # Test connection
    if not controller.test_connection():
        print("❌ Cannot connect to camera!")
        return
    
    # Get initial status
    controller.get_ptz_status()
    controller.get_image_settings()
    
    print("\n🎮 PTZ Controls (Working Version)")
    print("=" * 45)
    print("Zoom Commands:")
    print("  zi [speed] [duration] - Zoom In (speed: 1-7, duration: seconds)")
    print("  zo [speed] [duration] - Zoom Out (speed: 1-7, duration: seconds)")
    print()
    print("Focus Commands:")
    print("  fn [duration] - Focus Near (duration: seconds)")
    print("  ff [duration] - Focus Far (duration: seconds)")
    print()
    print("Pan/Tilt Commands (for testing):")
    print("  pt [pan] [tilt] [duration] - Pan/Tilt movement")
    print()
    print("Status Commands:")
    print("  status - Get current PTZ status")
    print("  image  - Get image settings")
    print("  quit   - Exit")
    print()
    
    while True:
        try:
            cmd = input("Enter command: ").strip().lower().split()
            
            if not cmd:
                continue
                
            action = cmd[0]
            
            if action in ['quit', 'exit', 'q']:
                break
            elif action == 'zi':
                speed = int(cmd[1]) if len(cmd) > 1 else 4
                duration = float(cmd[2]) if len(cmd) > 2 else 1.0
                controller.zoom_in(speed, duration)
            elif action == 'zo':
                speed = int(cmd[1]) if len(cmd) > 1 else 4
                duration = float(cmd[2]) if len(cmd) > 2 else 1.0
                controller.zoom_out(speed, duration)
            elif action == 'fn':
                duration = float(cmd[1]) if len(cmd) > 1 else 0.5
                controller.focus_near(duration)
            elif action == 'ff':
                duration = float(cmd[1]) if len(cmd) > 1 else 0.5
                controller.focus_far(duration)
            elif action == 'pt':
                pan = int(cmd[1]) if len(cmd) > 1 else 0
                tilt = int(cmd[2]) if len(cmd) > 2 else 0
                duration = float(cmd[3]) if len(cmd) > 3 else 1.0
                controller.pan_tilt(pan, tilt, duration)
            elif action == 'status':
                controller.get_ptz_status()
            elif action == 'image':
                controller.get_image_settings()
            else:
                print("❌ Unknown command. Type 'quit' to exit.")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except ValueError:
            print("❌ Invalid parameter. Check command format.")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n👋 Goodbye!")

if __name__ == "__main__":
    main()
