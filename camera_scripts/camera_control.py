#!/usr/bin/env python3
"""
Hikvision IP Camera PTZ Control Script
Controls zoom, focus, pan, tilt, and preset positions
"""

import requests
import time
import cv2
import base64
from requests.auth import HTTPDigestAuth
import json

class HikvisionCameraController:
    def __init__(self, camera_ip="192.168.1.64", username="admin", password="Admin%40123"):
        """Initialize camera controller with IP and credentials"""
        self.camera_ip = camera_ip
        self.base_url = f"http://{camera_ip}"
        self.username = username
        self.password = password
        self.auth = HTTPDigestAuth(username, password)
        
        # PTZ command URLs
        self.ptz_url = f"{self.base_url}/ISAPI/PTZ/channels/1/continuous"
        self.preset_url = f"{self.base_url}/ISAPI/PTZ/channels/1/presets"
        self.focus_url = f"{self.base_url}/ISAPI/PTZ/channels/1/focusStatus"
        self.zoom_url = f"{self.base_url}/ISAPI/PTZ/channels/1/zoom"
        
        # Video stream URL
        self.stream_url = f"{self.base_url}/ISAPI/Streaming/channels/1/picture"
        
        print(f"🎥 Hikvision Camera Controller initialized")
        print(f"📡 Camera IP: {camera_ip}")
        print(f"👤 Username: {username}")

    def test_connection(self):
        """Test connection to camera"""
        try:
            response = requests.get(f"{self.base_url}/ISAPI/System/deviceInfo", 
                                  auth=self.auth, timeout=5)
            if response.status_code == 200:
                print("✅ Camera connection successful!")
                return True
            else:
                print(f"❌ Camera connection failed. Status: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False

    def send_ptz_command(self, pan=0, tilt=0, zoom=0, speed=50):
        """
        Send PTZ command to camera
        pan: -100 to 100 (left to right)
        tilt: -100 to 100 (down to up)
        zoom: -100 to 100 (zoom out to zoom in)
        speed: 1 to 100
        """
        xml_data = f'''<?xml version="1.0" encoding="UTF-8"?>
        <PTZData>
            <pan>{pan}</pan>
            <tilt>{tilt}</tilt>
            <zoom>{zoom}</zoom>
            <Momentary>
                <duration>1000</duration>
            </Momentary>
        </PTZData>'''
        
        try:
            response = requests.put(self.ptz_url, 
                                  data=xml_data,
                                  auth=self.auth,
                                  headers={'Content-Type': 'application/xml'},
                                  timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ PTZ command error: {e}")
            return False

    def zoom_in(self, speed=50, duration=2):
        """Zoom in for specified duration"""
        print(f"🔍 Zooming IN (speed: {speed}, duration: {duration}s)")
        self.send_ptz_command(zoom=speed)
        time.sleep(duration)
        self.stop_movement()

    def zoom_out(self, speed=50, duration=2):
        """Zoom out for specified duration"""
        print(f"🔍 Zooming OUT (speed: {speed}, duration: {duration}s)")
        self.send_ptz_command(zoom=-speed)
        time.sleep(duration)
        self.stop_movement()

    def pan_left(self, speed=50, duration=2):
        """Pan left"""
        print(f"⬅️ Panning LEFT (speed: {speed}, duration: {duration}s)")
        self.send_ptz_command(pan=-speed)
        time.sleep(duration)
        self.stop_movement()

    def pan_right(self, speed=50, duration=2):
        """Pan right"""
        print(f"➡️ Panning RIGHT (speed: {speed}, duration: {duration}s)")
        self.send_ptz_command(pan=speed)
        time.sleep(duration)
        self.stop_movement()

    def tilt_up(self, speed=50, duration=2):
        """Tilt up"""
        print(f"⬆️ Tilting UP (speed: {speed}, duration: {duration}s)")
        self.send_ptz_command(tilt=speed)
        time.sleep(duration)
        self.stop_movement()

    def tilt_down(self, speed=50, duration=2):
        """Tilt down"""
        print(f"⬇️ Tilting DOWN (speed: {speed}, duration: {duration}s)")
        self.send_ptz_command(tilt=-speed)
        time.sleep(duration)
        self.stop_movement()

    def stop_movement(self):
        """Stop all PTZ movement"""
        self.send_ptz_command(pan=0, tilt=0, zoom=0)

    def set_preset(self, preset_id=1):
        """Set current position as preset"""
        xml_data = f'''<?xml version="1.0" encoding="UTF-8"?>
        <PTZPreset>
            <id>{preset_id}</id>
            <presetName>Preset_{preset_id}</presetName>
        </PTZPreset>'''
        
        try:
            response = requests.post(f"{self.preset_url}/{preset_id}",
                                   data=xml_data,
                                   auth=self.auth,
                                   headers={'Content-Type': 'application/xml'})
            if response.status_code == 200:
                print(f"✅ Preset {preset_id} saved successfully")
                return True
            else:
                print(f"❌ Failed to save preset {preset_id}")
                return False
        except Exception as e:
            print(f"❌ Preset save error: {e}")
            return False

    def goto_preset(self, preset_id=1):
        """Go to specified preset position"""
        xml_data = f'''<?xml version="1.0" encoding="UTF-8"?>
        <PTZPreset>
            <id>{preset_id}</id>
        </PTZPreset>'''
        
        try:
            response = requests.put(f"{self.preset_url}/{preset_id}/goto",
                                  data=xml_data,
                                  auth=self.auth,
                                  headers={'Content-Type': 'application/xml'})
            if response.status_code == 200:
                print(f"✅ Moving to preset {preset_id}")
                return True
            else:
                print(f"❌ Failed to go to preset {preset_id}")
                return False
        except Exception as e:
            print(f"❌ Goto preset error: {e}")
            return False

    def capture_image(self, filename=None):
        """Capture image from camera"""
        if filename is None:
            filename = f"camera_capture_{int(time.time())}.jpg"
        
        try:
            response = requests.get(self.stream_url, auth=self.auth, timeout=10)
            if response.status_code == 200:
                with open(filename, 'wb') as f:
                    f.write(response.content)
                print(f"📸 Image captured: {filename}")
                return filename
            else:
                print(f"❌ Failed to capture image. Status: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Image capture error: {e}")
            return None

    def focus_auto(self):
        """Set focus to automatic"""
        xml_data = '''<?xml version="1.0" encoding="UTF-8"?>
        <FocusData>
            <focus>auto</focus>
        </FocusData>'''
        
        try:
            response = requests.put(f"{self.base_url}/ISAPI/PTZ/channels/1/focus",
                                  data=xml_data,
                                  auth=self.auth,
                                  headers={'Content-Type': 'application/xml'})
            if response.status_code == 200:
                print("✅ Auto focus enabled")
                return True
            else:
                print("❌ Failed to set auto focus")
                return False
        except Exception as e:
            print(f"❌ Auto focus error: {e}")
            return False

    def wide_angle_and_zoom_sequence(self, wait_time=3):
        """
        Start with wide angle view, then zoom in to maximum
        """
        print("🎬 Starting Wide Angle to Maximum Zoom Sequence")
        print("=" * 50)
        
        # Step 1: Go to wide angle (zoom out completely)
        print("📐 Step 1: Going to wide angle view...")
        for i in range(3):  # Multiple zoom out commands to ensure wide angle
            self.zoom_out(speed=80, duration=3)
            time.sleep(0.5)
        
        print(f"⏱️ Wide angle achieved. Waiting {wait_time} seconds...")
        time.sleep(wait_time)
        
        # Capture wide angle image
        wide_filename = "wide_angle_view.jpg"
        self.capture_image(wide_filename)
        
        # Step 2: Zoom in to maximum
        print("🔍 Step 2: Zooming in to maximum...")
        for i in range(5):  # Multiple zoom in commands for maximum zoom
            self.zoom_in(speed=80, duration=3)
            time.sleep(0.5)
        
        print(f"🎯 Maximum zoom achieved. Waiting {wait_time} seconds...")
        time.sleep(wait_time)
        
        # Capture zoomed image
        zoom_filename = "maximum_zoom_view.jpg"
        self.capture_image(zoom_filename)
        
        print("✅ Sequence completed!")
        print(f"📁 Images saved: {wide_filename}, {zoom_filename}")

def main():
    """Main function to demonstrate camera control"""
    print("🎥 Hikvision Camera PTZ Control Script")
    print("=" * 50)
    
    # Initialize camera controller
    # Update these credentials as needed
    camera = HikvisionCameraController(
        camera_ip="192.168.1.64",
        username="admin", 
        password="Admin%40123"  # URL encoded password
    )
    
    # Test connection
    if not camera.test_connection():
        print("❌ Cannot connect to camera. Check IP, username, and password.")
        return
    
    print("\n🎮 Camera Control Menu:")
    print("1. Wide angle to maximum zoom sequence")
    print("2. Manual PTZ control")
    print("3. Capture image")
    print("4. Set/Go to presets")
    print("5. Auto focus")
    
    while True:
        print("\n" + "="*30)
        choice = input("Enter choice (1-5) or 'q' to quit: ").strip().lower()
        
        if choice == 'q':
            print("👋 Goodbye!")
            break
        elif choice == '1':
            wait_time = input("Enter wait time between steps (default 3s): ").strip()
            wait_time = int(wait_time) if wait_time.isdigit() else 3
            camera.wide_angle_and_zoom_sequence(wait_time)
        elif choice == '2':
            manual_control(camera)
        elif choice == '3':
            filename = input("Enter filename (or press Enter for auto): ").strip()
            filename = filename if filename else None
            camera.capture_image(filename)
        elif choice == '4':
            preset_control(camera)
        elif choice == '5':
            camera.focus_auto()
        else:
            print("❌ Invalid choice. Please try again.")

def manual_control(camera):
    """Manual PTZ control interface"""
    print("\n🎮 Manual PTZ Control")
    print("Commands: w(up), s(down), a(left), d(right), +(zoom in), -(zoom out), space(stop), q(back)")
    
    while True:
        cmd = input("PTZ Command: ").strip().lower()
        
        if cmd == 'q':
            break
        elif cmd == 'w':
            camera.tilt_up()
        elif cmd == 's':
            camera.tilt_down()
        elif cmd == 'a':
            camera.pan_left()
        elif cmd == 'd':
            camera.pan_right()
        elif cmd == '+':
            camera.zoom_in()
        elif cmd == '-':
            camera.zoom_out()
        elif cmd == ' ' or cmd == 'stop':
            camera.stop_movement()
        else:
            print("Invalid command. Use w/s/a/d/+/-/space/q")

def preset_control(camera):
    """Preset position control"""
    print("\n📍 Preset Control")
    print("1. Save current position as preset")
    print("2. Go to preset position")
    
    choice = input("Enter choice (1-2): ").strip()
    
    if choice == '1':
        preset_id = input("Enter preset ID (1-255): ").strip()
        if preset_id.isdigit():
            camera.set_preset(int(preset_id))
    elif choice == '2':
        preset_id = input("Enter preset ID to go to: ").strip()
        if preset_id.isdigit():
            camera.goto_preset(int(preset_id))

if __name__ == "__main__":
    main()
