#!/usr/bin/env python3
"""
Simple Hikvision Camera Zoom Script
Two functions: zoom_in_4x() and zoom_out_4x()
Can be used as command line tool or imported as module
"""

import requests
from requests.auth import HTTPDigestAuth
import time
import urllib3
import argparse
import sys

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class SimpleZoom:
    def __init__(self):
        # Camera settings
        self.ip = "192.168.1.64"
        self.username = "admin"
        self.password = "Admin@123"
        self.auth = HTTPDigestAuth(self.username, self.password)
        self.base_url = f"http://{self.ip}"
        
        print("📹 Simple Zoom Control")
        print("=" * 30)
        print(f"Camera: {self.ip}")
        print()
    
    def _zoom_single_step(self, direction, speed=4):
        """Execute single zoom step exactly like 'zi' or 'zo' command"""
        try:
            url = f"{self.base_url}/ISAPI/PTZCtrl/channels/1/continuous"
            
            # Use exact same logic as hikvision_zoom_focus.py
            if direction == "in":
                xml_data = f'''<?xml version="1.0" encoding="UTF-8"?>
                <PTZData>
                    <pan>0</pan>
                    <tilt>0</tilt>
                    <zoom>{speed}</zoom>
                </PTZData>'''
            else:  # zoom out
                xml_data = f'''<?xml version="1.0" encoding="UTF-8"?>
                <PTZData>
                    <pan>0</pan>
                    <tilt>0</tilt>
                    <zoom>-{speed}</zoom>
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
                print(f"❌ Zoom {direction} failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Zoom {direction} error: {e}")
            return False
    
    def zoom_in_4x(self):
        """Zoom in 4 times - exactly like typing 'zi' 4 times"""
        print("\n🔍 ZOOMING IN 4 TIMES (like typing 'zi' 4 times)")
        print("-" * 50)
        
        success_count = 0
        
        for i in range(4):
            print(f"Command {i+1}/4: zi")
            if self._zoom_single_step("in", speed=4):
                print(f"🔍 ZOOMIN at speed 4")
                success_count += 1
                time.sleep(1)  # Brief pause between commands (like manual typing)
            else:
                print(f"   ❌ Command {i+1} failed")
        
        if success_count == 4:
            print("✅ Completed 4x zoom in successfully!")
        else:
            print(f"⚠️ Only {success_count}/4 commands succeeded")
        
        return success_count == 4
    
    def zoom_out_4x(self):
        """Zoom out 4 times - exactly like typing 'zo' 4 times"""
        print("\n🔍 ZOOMING OUT 4 TIMES (like typing 'zo' 4 times)")
        print("-" * 51)
        
        success_count = 0
        
        for i in range(4):
            print(f"Command {i+1}/4: zo")
            if self._zoom_single_step("out", speed=4):
                print(f"🔍 ZOOMOUT at speed 4")
                success_count += 1
                time.sleep(1)  # Brief pause between commands (like manual typing)
            else:
                print(f"   ❌ Command {i+1} failed")
        
        if success_count == 4:
            print("✅ Completed 4x zoom out successfully!")
        else:
            print(f"⚠️ Only {success_count}/4 commands succeeded")
        
        return success_count == 4
    
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
            print(f"❌ Connection error: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description='Simple Hikvision Camera Zoom Control')
    parser.add_argument('--zoom-in', action='store_true', help='Zoom in 4 times')
    parser.add_argument('--zoom-out', action='store_true', help='Zoom out 4 times')
    parser.add_argument('--interactive', action='store_true', help='Run in interactive mode')
    
    args = parser.parse_args()
    
    # If no arguments provided, default to interactive mode
    if not any(vars(args).values()):
        args.interactive = True
    
    zoom_controller = SimpleZoom()
    
    # Test connection first
    if not zoom_controller.test_connection():
        print("❌ Failed to connect to camera")
        sys.exit(1)
    
    if args.zoom_in:
        print("🔍 Zooming in 4 times...")
        success = zoom_controller.zoom_in_4x()
        sys.exit(0 if success else 1)
    
    elif args.zoom_out:
        print("🔍 Zooming out 4 times...")
        success = zoom_controller.zoom_out_4x()
        sys.exit(0 if success else 1)
    
    elif args.interactive:
        # Interactive mode (original menu)
        print("\n🎮 ZOOM OPTIONS")
        print("=" * 25)
        print("1 - Zoom In 4 Times")
        print("2 - Zoom Out 4 Times")
        print("q - Quit")
        print()
        
        while True:
            try:
                choice = input("👉 Enter choice (1/2/q): ").strip().lower()
                
                if choice == 'q' or choice == 'quit':
                    break
                elif choice == '1':
                    zoom_controller.zoom_in_4x()
                elif choice == '2':
                    zoom_controller.zoom_out_4x()
                else:
                    print("❌ Invalid choice. Enter 1, 2, or q")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
        
        print("👋 Goodbye!")

# Example usage as functions
def zoom_in_4_times():
    """Standalone function to zoom in 4 times"""
    zoom = SimpleZoom()
    if zoom.test_connection():
        return zoom.zoom_in_4x()
    return False

def zoom_out_4_times():
    """Standalone function to zoom out 4 times"""
    zoom = SimpleZoom()
    if zoom.test_connection():
        return zoom.zoom_out_4x()
    return False

if __name__ == "__main__":
    main()
