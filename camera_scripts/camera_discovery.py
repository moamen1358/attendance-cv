#!/usr/bin/env python3
"""
Camera Capability Discovery
Find what PTZ/zoom/focus controls are actually available
"""

import requests
from requests.auth import HTTPDigestAuth
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def discover_camera_capabilities():
    """Discover available camera endpoints and capabilities"""
    
    ip = "192.168.1.64"
    username = "admin"
    password = "Admin@123"
    auth = HTTPDigestAuth(username, password)
    base_url = f"http://{ip}"
    
    print("🔍 Discovering Camera Capabilities")
    print("=" * 45)
    
    # Common PTZ endpoints to test
    endpoints_to_test = [
        # Standard PTZ
        "/ISAPI/PTZ/channels/1/capabilities",
        "/ISAPI/PTZ/channels/1/status", 
        "/ISAPI/PTZ/channels/1/continuous",
        "/ISAPI/PTZ/channels/1/momentary",
        "/ISAPI/PTZ/channels/1/absolute",
        "/ISAPI/PTZ/channels/1/relative",
        
        # Focus specific
        "/ISAPI/PTZ/channels/1/focus",
        "/ISAPI/PTZ/channels/1/focusConfiguration",
        "/ISAPI/PTZ/channels/1/focusStatus",
        
        # Zoom specific  
        "/ISAPI/PTZ/channels/1/zoom",
        "/ISAPI/PTZ/channels/1/zoomStatus",
        
        # Alternative PTZ paths
        "/ISAPI/PTZ/channels/101/capabilities",
        "/ISAPI/PTZ/channels/101/continuous", 
        
        # System info
        "/ISAPI/System/capabilities",
        "/ISAPI/System/deviceInfo",
        "/ISAPI/System/status",
        
        # Streaming
        "/ISAPI/Streaming/channels/1/capabilities",
        "/ISAPI/Streaming/channels/1/picture",
        "/ISAPI/Streaming/channels/1/status",
        
        # Content management (some cameras use this for PTZ)
        "/ISAPI/ContentMgmt/record/tracks/101",
        "/ISAPI/ContentMgmt/PTZ/channels/1",
        
        # Image settings (might include zoom/focus)
        "/ISAPI/Image/channels/1/capabilities",
        "/ISAPI/Image/channels/1",
        
        # Event (sometimes PTZ is here)
        "/ISAPI/Event/channels/1/capabilities",
    ]
    
    working_endpoints = []
    
    for endpoint in endpoints_to_test:
        url = f"{base_url}{endpoint}"
        
        try:
            # Try GET first
            response = requests.get(url, auth=auth, timeout=3, verify=False)
            status = response.status_code
            
            if status == 200:
                content_type = response.headers.get('content-type', '')
                content_length = len(response.content)
                
                print(f"✅ GET  {endpoint}")
                print(f"    Content-Type: {content_type}")
                print(f"    Content-Length: {content_length}")
                
                # Show some content if it's XML or JSON
                if 'xml' in content_type or 'json' in content_type:
                    preview = response.text[:200].replace('\n', ' ')
                    print(f"    Preview: {preview}...")
                
                working_endpoints.append((endpoint, 'GET', response.text))
                
            elif status == 405:  # Method not allowed - try PUT
                try:
                    put_response = requests.put(url, auth=auth, timeout=3, verify=False)
                    if put_response.status_code in [200, 400]:  # 400 might mean needs data
                        print(f"🔄 PUT  {endpoint} (Status: {put_response.status_code})")
                        working_endpoints.append((endpoint, 'PUT', put_response.text))
                except:
                    pass
                    
            elif status in [401, 403]:
                print(f"🔐 AUTH {endpoint} (Status: {status})")
            elif status == 404:
                pass  # Don't show 404s to reduce clutter
            else:
                print(f"❓ {status} {endpoint}")
                
        except Exception as e:
            pass  # Silently ignore connection errors
    
    # Show detailed results
    print(f"\n📋 Working Endpoints Found: {len(working_endpoints)}")
    print("=" * 45)
    
    for endpoint, method, content in working_endpoints:
        print(f"\n🔗 {method} {endpoint}")
        
        # Parse and show interesting content
        if 'capabilities' in endpoint.lower():
            print("    📋 CAPABILITIES ENDPOINT")
            if content:
                # Look for PTZ-related keywords in the response
                ptz_keywords = ['pan', 'tilt', 'zoom', 'focus', 'preset', 'absolute', 'relative', 'continuous']
                found_keywords = [kw for kw in ptz_keywords if kw.lower() in content.lower()]
                if found_keywords:
                    print(f"    🎯 PTZ Keywords found: {', '.join(found_keywords)}")
                
        elif 'deviceinfo' in endpoint.lower():
            print("    ℹ️  DEVICE INFO")
            
        elif 'status' in endpoint.lower():
            print("    📊 STATUS ENDPOINT")
            
        # Show first 300 chars of response
        if content:
            preview = content[:300].replace('\n', ' ').replace('\r', '')
            print(f"    Content: {preview}...")
    
    return working_endpoints

def analyze_ptz_support(working_endpoints):
    """Analyze if camera supports PTZ based on discovered endpoints"""
    print(f"\n🔍 PTZ Support Analysis")
    print("=" * 30)
    
    ptz_indicators = []
    
    for endpoint, method, content in working_endpoints:
        if 'ptz' in endpoint.lower():
            ptz_indicators.append(f"PTZ endpoint: {endpoint}")
        
        if content and any(keyword in content.lower() for keyword in ['pan', 'tilt', 'zoom', 'focus']):
            ptz_indicators.append(f"PTZ content in: {endpoint}")
    
    if ptz_indicators:
        print("✅ Camera appears to support PTZ:")
        for indicator in ptz_indicators:
            print(f"   - {indicator}")
    else:
        print("❌ Camera does not appear to support PTZ")
        print("💡 This might be a fixed camera or uses different protocols")
        print("   - Try ONVIF protocol")
        print("   - Check camera manual")
        print("   - Some features might be in Image settings")

if __name__ == "__main__":
    working_endpoints = discover_camera_capabilities()
    analyze_ptz_support(working_endpoints)
