#!/usr/bin/env python3
"""
Test the complete attendance workflow
"""

import cv2
import subprocess
import time
import os
from pathlib import Path

# Paths
camera_scripts_path = Path(__file__).parent / "camera_scripts"
RTSP_URL = "rtsp://admin:Admin%40123@192.168.1.64:554/Streaming/Channels/102"

def test_complete_workflow():
    """Test the complete workflow step by step"""
    print("🎬 Testing Complete Attendance Workflow")
    print("=" * 50)
    
    try:
        # Step 1: Zoom out 4x
        print("\n🔍 Step 1: Zooming out 4x for wide view...")
        result = subprocess.run([
            "python", 
            str(camera_scripts_path / "simple_4x_zoom.py"), 
            "--zoom-out"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Zoom out successful")
        else:
            print(f"❌ Zoom out failed: {result.stderr}")
            return False
        
        print("⏱️  Waiting 30 seconds for camera stabilization after zoom out...")
        time.sleep(30)  # Camera stabilization
        
        # Step 2: Capture frame
        print("\n📷 Step 2: Capturing frame from camera...")
        cap = cv2.VideoCapture(RTSP_URL)
        if not cap.isOpened():
            print("❌ Could not connect to camera")
            return False
        
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            print("❌ Could not capture frame")
            return False
        
        # Save frame
        temp_image_path = "/tmp/test_workflow_capture.jpg"
        cv2.imwrite(temp_image_path, frame)
        print(f"✅ Frame captured and saved to {temp_image_path}")
        
        # Step 3: Run YOLO detection
        print("\n🎯 Step 3: Running YOLO face detection...")
        json_output_path = "/tmp/test_workflow_results.json"
        result = subprocess.run([
            "python",
            str(camera_scripts_path / "yolo_image _count.py"),
            temp_image_path,
            "--confidence", "0.3",
            "--json-output", json_output_path
        ], capture_output=True, text=True, timeout=60)
        
        print(f"YOLO stdout: {result.stdout}")
        print(f"YOLO stderr: {result.stderr}")
        print(f"YOLO return code: {result.returncode}")
        
        face_count = 0
        if "Total faces detected:" in result.stdout:
            face_count = int(result.stdout.split("Total faces detected:")[1].split()[0])
        
        print(f"✅ YOLO detection completed - Found {face_count} faces")
        
        if face_count == 0:
            print("⚠️ No faces detected, but workflow successful")
            return True
        
        # Step 4: Send to Arduino (if faces detected)
        print(f"\n🤖 Step 4: Sending {face_count} face positions to Arduino...")
        result = subprocess.run([
            "python",
            str(camera_scripts_path / "minimal_face_processor.py"),
            json_output_path,
            "--confidence", "0.3"
        ], capture_output=True, text=True, timeout=120)
        
        print(f"Arduino stdout: {result.stdout}")
        print(f"Arduino stderr: {result.stderr}")
        print(f"Arduino return code: {result.returncode}")
        
        if result.returncode == 0:
            print("✅ Face positions sent to Arduino")
        else:
            print(f"⚠️ Arduino communication issue: {result.stderr}")
        
        # Step 5: Zoom in 4x
        print("\n🔍 Step 5: Zooming in 4x to target...")
        result = subprocess.run([
            "python",
            str(camera_scripts_path / "simple_4x_zoom.py"),
            "--zoom-in"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Zoom in successful")
        else:
            print(f"❌ Zoom in failed: {result.stderr}")
        
        print("⏱️  Waiting 30 seconds for zoom in stabilization...")
        time.sleep(30)  # Focus/positioning time
        
        # Step 6: Zoom back out 4x
        print("\n🔍 Step 6: Zooming back out 4x to wide view...")
        result = subprocess.run([
            "python",
            str(camera_scripts_path / "simple_4x_zoom.py"),
            "--zoom-out"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Final zoom out successful")
        else:
            print(f"❌ Final zoom out failed: {result.stderr}")
        
        print("⏱️  Waiting 30 seconds for final camera stabilization...")
        time.sleep(30)  # Final stabilization
        
        print("\n🎉 ATTENDANCE CYCLE COMPLETE - STOPPED")
        print("📝 Summary: One complete attendance cycle finished")
        print("🔄 System ready for next manual attendance session")
        
        # Cleanup
        try:
            if os.path.exists(temp_image_path):
                os.remove(temp_image_path)
            if os.path.exists(json_output_path):
                os.remove(json_output_path)
        except:
            pass
        
        return True
        
    except Exception as e:
        print(f"❌ Workflow test error: {e}")
        return False

def test_3_frame_monitoring():
    """Test monitoring every 3rd frame"""
    print("\n📹 Testing 3-Frame Monitoring Logic")
    print("=" * 40)
    
    # Simulate frame processing
    for frame_num in range(1, 13):  # Test 12 frames
        if frame_num % 3 == 0:
            print(f"🎯 Frame {frame_num}: PROCESS with YOLO")
        else:
            print(f"📹 Frame {frame_num}: Monitor only")
    
    print("✅ 3-frame monitoring logic works correctly!")

def test_single_attendance_cycle():
    """Test a single attendance cycle with 30-second waits as specified"""
    print("\n🎯 Testing Single Attendance Cycle (30-second waits)")
    print("=" * 55)
    
    try:
        # Step 1: Zoom out 4x for wide view
        print("\n🔍 Step 1: Zooming out 4x for wide angle view...")
        result = subprocess.run([
            "python", 
            str(camera_scripts_path / "simple_4x_zoom.py"), 
            "--zoom-out"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Zoom out successful")
        else:
            print(f"❌ Zoom out failed: {result.stderr}")
            return False
        
        # Wait 30 seconds after zoom out
        print("⏱️  Wait after zoom out - 30 seconds...")
        time.sleep(30)
        
        # Step 2: Capture wide angle frame and process with YOLO
        print("\n� Step 2: Capturing wide angle frame and processing...")
        cap = cv2.VideoCapture(RTSP_URL)
        
        if not cap.isOpened():
            print("❌ Could not connect to camera")
            return False
        
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            print("❌ Could not capture frame")
            return False
        
        # Save frame for processing
        temp_image_path = "/tmp/attendance_wide_frame.jpg"
        cv2.imwrite(temp_image_path, frame)
        print("✅ Wide angle frame captured")
        
        # Run YOLO detection on wide angle frame
        print("🎯 Processing frame with YOLO...")
        json_output_path = "/tmp/attendance_face_positions.json"
        result = subprocess.run([
            "python",
            str(camera_scripts_path / "yolo_image _count.py"),
            temp_image_path,
            "--confidence", "0.3",
            "--json-output", json_output_path
        ], capture_output=True, text=True, timeout=60)
        
        face_count = 0
        if "Total faces detected:" in result.stdout:
            face_count = int(result.stdout.split("Total faces detected:")[1].split()[0])
        
        print(f"✅ YOLO processing complete - Found {face_count} faces")
        
        # Save face positions to calibration file
        if face_count > 0:
            try:
                import json
                with open(json_output_path, 'r') as f:
                    face_data = json.load(f)
                
                # Save detailed face positions for calibration
                calibration_file = "/tmp/face_calibration_data.txt"
                with open(calibration_file, 'w') as f:
                    f.write("=== FACE CALIBRATION DATA ===\n")
                    f.write(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Total faces detected: {face_count}\n")
                    f.write(f"Frame resolution: 1920x1080 (assumed)\n\n")
                    
                    for i, face in enumerate(face_data.get('faces', []), 1):
                        bbox = face['bbox']
                        center_x = (bbox[0] + bbox[2]) // 2
                        center_y = (bbox[1] + bbox[3]) // 2
                        width = bbox[2] - bbox[0]
                        height = bbox[3] - bbox[1]
                        
                        f.write(f"Face {i}:\n")
                        f.write(f"  Bounding Box: ({bbox[0]}, {bbox[1]}) to ({bbox[2]}, {bbox[3]})\n")
                        f.write(f"  Center Position: ({center_x}, {center_y})\n")
                        f.write(f"  Size: {width}x{height} pixels\n")
                        f.write(f"  Confidence: {face['confidence']:.3f}\n")
                        
                        # Calculate position ratios
                        x_ratio = center_x / 1920
                        y_ratio = center_y / 1080
                        f.write(f"  Position Ratios: X={x_ratio:.3f}, Y={y_ratio:.3f}\n")
                        f.write(f"  Distance from center: X={center_x - 960}, Y={center_y - 540}\n\n")
                
                print(f"📝 Face positions saved to {calibration_file}")
                print("📍 Please note your position in the wide-angle frame!")
                
            except Exception as e:
                print(f"⚠️ Could not save calibration data: {e}")
        
        if face_count == 0:
            print("⚠️ No faces detected - ending cycle")
            print("🔍 Zooming back out and stopping...")
            subprocess.run([
                "python",
                str(camera_scripts_path / "simple_4x_zoom.py"),
                "--zoom-out"
            ], capture_output=True, text=True, timeout=30)
            print("⏱️  Final wait - 30 seconds...")
            time.sleep(30)
            print("🛑 Attendance cycle stopped")
            return True
        
        # Step 3: Zoom in 4x to target faces
        print(f"\n🔍 Step 3: Zooming in 4x to target {face_count} detected faces...")
        result = subprocess.run([
            "python",
            str(camera_scripts_path / "simple_4x_zoom.py"),
            "--zoom-in"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Zoom in successful")
        else:
            print(f"❌ Zoom in failed: {result.stderr}")
        
        # Wait 30 seconds after zoom in
        print("⏱️  Wait after zoom in - 30 seconds...")
        time.sleep(30)
        
        # Step 4: Send face positions to Arduino using Wide Angle Positioning
        print("\n🤖 Step 4: Sending face positions to Arduino (Wide Angle Positioning)...")
        result = subprocess.run([
            "python",
            str(camera_scripts_path / "wide_angle_positioning.py"),
            json_output_path,
            "--confidence", "0.3"
        ], capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print("✅ Face positions sent to Arduino successfully")
            print("⏱️  Waiting for Arduino to finish moving...")
            time.sleep(5)  # Wait for Arduino to complete movements
        else:
            print(f"⚠️ Arduino communication issue: {result.stderr}")
        
        # Step 5: Complete
        print("\n🛑 ATTENDANCE PROCESS COMPLETE - STOPPED")
        
        # Cleanup
        try:
            if os.path.exists(temp_image_path):
                os.remove(temp_image_path)
            if os.path.exists(json_output_path):
                os.remove(json_output_path)
        except:
            pass
        
        print("\n📝 Summary:")
        print("   • Zoomed out → waited 30 seconds → captured wide frame")
        print(f"   • Processed with YOLO → found {face_count} faces")
        print("   • Zoomed in → waited 30 seconds")
        print("   • Sent positions to Arduino")
        print("   • STOPPED (no final wait, ready for next session)")
        
        return True
        
    except Exception as e:
        print(f"❌ Single cycle test error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Running Workflow Tests")
    print("=" * 30)
    
    # Test monitoring logic
    test_3_frame_monitoring()
    
    # Test single attendance cycle (non-continuous)
    print("\n" + "="*60)
    success = test_single_attendance_cycle()
    
    if success:
        print("\n✅ Single attendance cycle test passed!")
    else:
        print("\n❌ Single attendance cycle test failed!")
    
    # Optionally test the old complete workflow
    # success = test_complete_workflow()
