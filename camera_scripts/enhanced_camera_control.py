#!/usr/bin/env python3
"""
Enhanced Hikvision Camera Control with Zoom and Focus
Supports multiple authentication methods and precise zoom/focus control
"""

import requests
import time
import cv2
import base64
from requests.auth import HTTPDigestAuth, HTTPBasicAuth
import json
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class EnhancedHikvisionController:
    def __init__(self, camera_ip="192.168.1.64", username="admin", password="Admin@123"):
        """Initialize camera controller with multiple auth options"""
        self.camera_ip = camera_ip
        self.base_url = f"http://{camera_ip}"
        self.username = username
        self.password = password
        
        # Try different authentication methods
        self.auth_digest = HTTPDigestAuth(username, password)
        self.auth_basic = HTTPBasicAuth(username, password)
        self.current_auth = None
        
        # API endpoints
        self.ptz_url = f"{self.base_url}/ISAPI/PTZ/channels/1"
        self.device_info_url = f"{self.base_url}/ISAPI/System/deviceInfo"
        self.stream_url = f"{self.base_url}/ISAPI/Streaming/channels/1/picture"
        
        print(f"🎥 Enhanced Hikvision Camera Controller")
        print(f"📡 Camera IP: {camera_ip}")
        print(f"👤 Username: {username}")
        print(f"🔐 Trying multiple authentication methods...")

    def test_connection(self):
        """Test connection with multiple authentication methods"""
        auth_methods = [
            ("Digest Auth", self.auth_digest),
            ("Basic Auth", self.auth_basic),
        ]
        
        for auth_name, auth_method in auth_methods:
            try:
                print(f"🔄 Trying {auth_name}...")
                response = requests.get(
                    self.device_info_url, 
                    auth=auth_method, 
                    timeout=5,
                    verify=False
                )
                
                if response.status_code == 200:
                    print(f"✅ {auth_name} successful!")
                    self.current_auth = auth_method
                    return True
                else:
                    print(f"❌ {auth_name} failed. Status: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ {auth_name} error: {e}")
        
        # Try without authentication
        try:
            print("🔄 Trying no authentication...")
            response = requests.get(self.device_info_url, timeout=5, verify=False)
            if response.status_code == 200:
                print("✅ No authentication needed!")
                self.current_auth = None
                return True
        except Exception as e:
            print(f"❌ No auth error: {e}")
        
        return False

    def send_ptz_command(self, pan=0, tilt=0, zoom=0):
        """Send PTZ command with current working auth"""
        xml_data = f'''<?xml version="1.0" encoding="UTF-8"?>
        <PTZData>
            <pan>{pan}</pan>
            <tilt>{tilt}</tilt>
            <zoom>{zoom}</zoom>
        </PTZData>'''
        
        try:
            url = f"{self.ptz_url}/continuous"
            response = requests.put(
                url,
                data=xml_data,
                auth=self.current_auth,
                headers={'Content-Type': 'application/xml'},
                timeout=5,
                verify=False
            )
            return response.status_code == 200
        except Exception as e:
            print(f"❌ PTZ command error: {e}")
            return False

    def zoom_control(self, zoom_level, duration=1):
        """
        Precise zoom control
        zoom_level: -100 (zoom out) to +100 (zoom in)
        duration: how long to zoom (seconds)
        """
        if zoom_level > 0:
            print(f"🔍 Zooming IN (level: {zoom_level}, duration: {duration}s)")
        else:
            print(f"🔍 Zooming OUT (level: {abs(zoom_level)}, duration: {duration}s)")
        
        # Start zoom
        success = self.send_ptz_command(zoom=zoom_level)
        if success:
            time.sleep(duration)
            # Stop zoom
            self.send_ptz_command(zoom=0)
            return True
        return False

    def zoom_in(self, speed=50, duration=1):
        """Zoom in with specified speed and duration"""
        return self.zoom_control(speed, duration)

    def zoom_out(self, speed=50, duration=1):
        """Zoom out with specified speed and duration"""
        return self.zoom_control(-speed, duration)

    def zoom_to_wide(self, iterations=5):
        """Zoom out to maximum wide angle"""
        print("📐 Zooming to maximum wide angle...")
        for i in range(iterations):
            print(f"  📉 Zoom out iteration {i+1}/{iterations}")
            self.zoom_out(speed=80, duration=2)
            time.sleep(0.5)
        print("✅ Wide angle achieved")

    def zoom_to_max(self, iterations=5):
        """Zoom in to maximum telephoto"""
        print("🔭 Zooming to maximum telephoto...")
        for i in range(iterations):
            print(f"  📈 Zoom in iteration {i+1}/{iterations}")
            self.zoom_in(speed=80, duration=2)
            time.sleep(0.5)
        print("✅ Maximum zoom achieved")

    def set_focus_mode(self, mode="auto"):
        """
        Set focus mode
        mode: 'auto', 'manual', 'onepush'
        """
        xml_data = f'''<?xml version="1.0" encoding="UTF-8"?>
        <FocusConfiguration>
            <focusMode>{mode}</focusMode>
        </FocusConfiguration>'''
        
        try:
            url = f"{self.ptz_url}/focus"
            response = requests.put(
                url,
                data=xml_data,
                auth=self.current_auth,
                headers={'Content-Type': 'application/xml'},
                timeout=5,
                verify=False
            )
            
            if response.status_code == 200:
                print(f"✅ Focus mode set to: {mode}")
                return True
            else:
                print(f"❌ Failed to set focus mode. Status: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Focus mode error: {e}")
            return False

    def focus_near(self, speed=50, duration=1):
        """Focus to near (closer objects)"""
        print(f"🔍 Focusing NEAR (speed: {speed}, duration: {duration}s)")
        
        xml_data = f'''<?xml version="1.0" encoding="UTF-8"?>
        <FocusData>
            <focus>{-speed}</focus>
        </FocusData>'''
        
        try:
            url = f"{self.ptz_url}/focus"
            response = requests.put(
                url,
                data=xml_data,
                auth=self.current_auth,
                headers={'Content-Type': 'application/xml'},
                timeout=5,
                verify=False
            )
            
            if response.status_code == 200:
                time.sleep(duration)
                # Stop focus movement
                self.stop_focus()
                return True
            return False
        except Exception as e:
            print(f"❌ Focus near error: {e}")
            return False

    def focus_far(self, speed=50, duration=1):
        """Focus to far (distant objects)"""
        print(f"🔍 Focusing FAR (speed: {speed}, duration: {duration}s)")
        
        xml_data = f'''<?xml version="1.0" encoding="UTF-8"?>
        <FocusData>
            <focus>{speed}</focus>
        </FocusData>'''
        
        try:
            url = f"{self.ptz_url}/focus"
            response = requests.put(
                url,
                data=xml_data,
                auth=self.current_auth,
                headers={'Content-Type': 'application/xml'},
                timeout=5,
                verify=False
            )
            
            if response.status_code == 200:
                time.sleep(duration)
                # Stop focus movement
                self.stop_focus()
                return True
            return False
        except Exception as e:
            print(f"❌ Focus far error: {e}")
            return False

    def stop_focus(self):
        """Stop focus movement"""
        xml_data = '''<?xml version="1.0" encoding="UTF-8"?>
        <FocusData>
            <focus>0</focus>
        </FocusData>'''
        
        try:
            url = f"{self.ptz_url}/focus"
            response = requests.put(
                url,
                data=xml_data,
                auth=self.current_auth,
                headers={'Content-Type': 'application/xml'},
                timeout=5,
                verify=False
            )
            return response.status_code == 200
        except Exception as e:
            return False

    def auto_focus_trigger(self):
        """Trigger one-time auto focus"""
        print("🎯 Triggering auto focus...")
        return self.set_focus_mode("onepush")

    def capture_image(self, filename=None):
        """Capture image from camera"""
        if filename is None:
            filename = f"camera_capture_{int(time.time())}.jpg"
        
        try:
            response = requests.get(
                self.stream_url, 
                auth=self.current_auth, 
                timeout=10,
                verify=False
            )
            
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

    def zoom_and_focus_sequence(self):
        """Complete zoom and focus demonstration sequence"""
        print("\n🎬 Starting Zoom and Focus Sequence")
        print("=" * 50)
        
        # Step 1: Set auto focus
        print("1️⃣ Setting auto focus mode...")
        self.set_focus_mode("auto")
        time.sleep(2)
        
        # Step 2: Wide angle
        print("\n2️⃣ Going to wide angle...")
        self.zoom_to_wide()
        self.capture_image("01_wide_angle.jpg")
        time.sleep(3)
        
        # Step 3: Medium zoom
        print("\n3️⃣ Medium zoom...")
        self.zoom_in(speed=60, duration=3)
        self.auto_focus_trigger()
        time.sleep(2)
        self.capture_image("02_medium_zoom.jpg")
        time.sleep(3)
        
        # Step 4: Maximum zoom
        print("\n4️⃣ Maximum zoom...")
        self.zoom_to_max()
        self.auto_focus_trigger()
        time.sleep(2)
        self.capture_image("03_max_zoom.jpg")
        time.sleep(3)
        
        # Step 5: Test manual focus
        print("\n5️⃣ Testing manual focus...")
        self.set_focus_mode("manual")
        time.sleep(1)
        
        print("  🔍 Focus near...")
        self.focus_near(speed=70, duration=2)
        self.capture_image("04_focus_near.jpg")
        time.sleep(2)
        
        print("  🔍 Focus far...")
        self.focus_far(speed=70, duration=2)
        self.capture_image("05_focus_far.jpg")
        time.sleep(2)
        
        # Step 6: Return to auto focus and wide
        print("\n6️⃣ Returning to auto focus and wide angle...")
        self.set_focus_mode("auto")
        self.zoom_to_wide()
        self.capture_image("06_final_wide.jpg")
        
        print("\n✅ Zoom and Focus Sequence Complete!")
        print("📁 Check the captured images to see the results")

def main():
    """Main function with enhanced menu"""
    print("🎥 Enhanced Hikvision Camera Control")
    print("=" * 50)
    
    # Get camera credentials
    ip = input("Enter camera IP (default: 192.168.1.64): ").strip()
    ip = ip if ip else "192.168.1.64"
    
    username = input("Enter username (default: admin): ").strip()
    username = username if username else "admin"
    
    password = input("Enter password: ").strip()
    if not password:
        print("⚠️ Using default password: Admin@123")
        password = "Admin@123"
    
    # Initialize camera
    camera = EnhancedHikvisionController(ip, username, password)
    
    # Test connection
    if not camera.test_connection():
        print("\n❌ Cannot connect to camera.")
        print("💡 Try these solutions:")
        print("   1. Check IP address is correct")
        print("   2. Try password without URL encoding: Admin@123")
        print("   3. Check camera is on same network")
        print("   4. Try accessing camera web interface first")
        return
    
    print("\n✅ Camera connected successfully!")
    
    while True:
        print("\n🎮 Camera Control Menu:")
        print("1. 🔍 Zoom Controls")
        print("2. 🎯 Focus Controls") 
        print("3. 📸 Capture Image")
        print("4. 🎬 Full Zoom & Focus Sequence")
        print("5. ❓ Help")
        print("q. Quit")
        
        choice = input("\nEnter choice: ").strip().lower()
        
        if choice == 'q':
            print("👋 Goodbye!")
            break
        elif choice == '1':
            zoom_menu(camera)
        elif choice == '2':
            focus_menu(camera)
        elif choice == '3':
            filename = input("Enter filename (or press Enter): ").strip()
            camera.capture_image(filename if filename else None)
        elif choice == '4':
            camera.zoom_and_focus_sequence()
        elif choice == '5':
            show_help()
        else:
            print("❌ Invalid choice")

def zoom_menu(camera):
    """Zoom control submenu"""
    while True:
        print("\n🔍 Zoom Controls:")
        print("1. Zoom In (fast)")
        print("2. Zoom Out (fast)")
        print("3. Zoom to Wide Angle")
        print("4. Zoom to Maximum")
        print("5. Custom Zoom")
        print("b. Back to main menu")
        
        choice = input("Zoom choice: ").strip()
        
        if choice == 'b':
            break
        elif choice == '1':
            camera.zoom_in(speed=70, duration=2)
        elif choice == '2':
            camera.zoom_out(speed=70, duration=2)
        elif choice == '3':
            camera.zoom_to_wide()
        elif choice == '4':
            camera.zoom_to_max()
        elif choice == '5':
            try:
                speed = int(input("Zoom speed (1-100): "))
                duration = float(input("Duration (seconds): "))
                direction = input("Direction (in/out): ").strip().lower()
                
                if direction == 'in':
                    camera.zoom_in(speed, duration)
                elif direction == 'out':
                    camera.zoom_out(speed, duration)
                else:
                    print("❌ Invalid direction")
            except ValueError:
                print("❌ Invalid input")

def focus_menu(camera):
    """Focus control submenu"""
    while True:
        print("\n🎯 Focus Controls:")
        print("1. Auto Focus")
        print("2. Manual Focus Near")
        print("3. Manual Focus Far") 
        print("4. Set Auto Focus Mode")
        print("5. Set Manual Focus Mode")
        print("6. Trigger One-Shot Auto Focus")
        print("b. Back to main menu")
        
        choice = input("Focus choice: ").strip()
        
        if choice == 'b':
            break
        elif choice == '1':
            camera.set_focus_mode("auto")
        elif choice == '2':
            camera.focus_near(speed=60, duration=1.5)
        elif choice == '3':
            camera.focus_far(speed=60, duration=1.5)
        elif choice == '4':
            camera.set_focus_mode("auto")
        elif choice == '5':
            camera.set_focus_mode("manual")
        elif choice == '6':
            camera.auto_focus_trigger()

def show_help():
    """Show help information"""
    print("\n❓ Help Information:")
    print("=" * 40)
    print("🔍 Zoom: Controls camera zoom level")
    print("   - Wide angle: See more of the scene")
    print("   - Telephoto: See distant objects closer")
    print("")
    print("🎯 Focus: Controls image sharpness")
    print("   - Auto: Camera focuses automatically")
    print("   - Manual Near: Focus on close objects")
    print("   - Manual Far: Focus on distant objects")
    print("")
    print("📸 Tips:")
    print("   - Use auto focus for best results")
    print("   - Zoom first, then focus")
    print("   - Capture images to verify results")

if __name__ == "__main__":
    main()
