#!/usr/bin/env python3
"""
Quick Camera Test - Zoom and Focus
Test script to verify camera zoom and focus controls work
"""

import requests
from requests.auth import HTTPDigestAuth
import time
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_camera_controls():
    """Test basic camera zoom and focus controls"""
    
    # Camera settings
    ip = "192.168.1.64"
    username = "admin"
    password = "Admin@123"
    auth = HTTPDigestAuth(username, password)
    
    base_url = f"http://{ip}"
    
    print("🎥 Testing Hikvision Camera Controls")
    print("=" * 40)
    
    # Test 1: Capture initial image
    print("📸 Test 1: Capturing initial image...")
    try:
        response = requests.get(f"{base_url}/ISAPI/Streaming/channels/1/picture", 
                               auth=auth, timeout=10)
        if response.status_code == 200:
            with open("test_01_initial.jpg", 'wb') as f:
                f.write(response.content)
            print("✅ Initial image captured: test_01_initial.jpg")
        else:
            print(f"❌ Image capture failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Image capture error: {e}")
    
    # Test 2: Try zoom commands
    print("\n🔍 Test 2: Testing zoom controls...")
    
    zoom_commands = [
        (50, "Zoom IN"),
        (-50, "Zoom OUT"),
        (0, "Stop Zoom")
    ]
    
    for zoom_value, description in zoom_commands:
        print(f"  🔄 {description} (value: {zoom_value})")
        
        xml_data = f'''<?xml version="1.0" encoding="UTF-8"?>
        <PTZData>
            <pan>0</pan>
            <tilt>0</tilt>
            <zoom>{zoom_value}</zoom>
        </PTZData>'''
        
        try:
            response = requests.put(f"{base_url}/ISAPI/PTZ/channels/1/continuous",
                                  data=xml_data,
                                  auth=auth,
                                  headers={'Content-Type': 'application/xml'},
                                  timeout=5)
            print(f"    Status: {response.status_code}")
            if response.status_code != 200:
                print(f"    Response: {response.text[:200]}")
            
            if zoom_value != 0:
                time.sleep(2)  # Let zoom run for 2 seconds
                # Stop zoom
                stop_xml = '''<?xml version="1.0" encoding="UTF-8"?>
                <PTZData>
                    <pan>0</pan>
                    <tilt>0</tilt>
                    <zoom>0</zoom>
                </PTZData>'''
                requests.put(f"{base_url}/ISAPI/PTZ/channels/1/continuous",
                           data=stop_xml, auth=auth,
                           headers={'Content-Type': 'application/xml'})
                
        except Exception as e:
            print(f"    ❌ Error: {e}")
    
    # Test 3: Try focus commands
    print("\n🎯 Test 3: Testing focus controls...")
    
    focus_commands = [
        ("auto", "Auto Focus"),
        ("manual", "Manual Focus"),
    ]
    
    for focus_mode, description in focus_commands:
        print(f"  🔄 {description}")
        
        xml_data = f'''<?xml version="1.0" encoding="UTF-8"?>
        <FocusConfiguration>
            <focusMode>{focus_mode}</focusMode>
        </FocusConfiguration>'''
        
        try:
            response = requests.put(f"{base_url}/ISAPI/PTZ/channels/1/focus",
                                  data=xml_data,
                                  auth=auth,
                                  headers={'Content-Type': 'application/xml'},
                                  timeout=5)
            print(f"    Status: {response.status_code}")
            if response.status_code != 200:
                print(f"    Response: {response.text[:200]}")
                
        except Exception as e:
            print(f"    ❌ Error: {e}")
    
    # Test 4: Capture final image
    print("\n📸 Test 4: Capturing final image...")
    try:
        response = requests.get(f"{base_url}/ISAPI/Streaming/channels/1/picture", 
                               auth=auth, timeout=10)
        if response.status_code == 200:
            with open("test_02_final.jpg", 'wb') as f:
                f.write(response.content)
            print("✅ Final image captured: test_02_final.jpg")
        else:
            print(f"❌ Image capture failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Image capture error: {e}")
    
    print("\n📋 Test Summary:")
    print("- Check test_01_initial.jpg and test_02_final.jpg")
    print("- Compare images to see if zoom/focus changes worked")
    print("- If PTZ commands failed, camera may not support them")

if __name__ == "__main__":
    test_camera_controls()
