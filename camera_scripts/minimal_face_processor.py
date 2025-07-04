#!/usr/bin/env python3
"""
Minimal Face Processor for Memory-Optimized Arduino
Works with minimal_face_arduino.ino
Can process faces from YOLO detection results or command line
"""

import serial
import time
import argparse
import sys
import json

class MinimalFaceProcessor:
    def __init__(self, port="/dev/ttyACM0"):
        self.arduino = None
        self.port = port
        
        # Frame specifications for wide angle view
        self.frame_width = 1920
        self.frame_height = 1080
        self.frame_center_x = self.frame_width // 2   # 960
        self.frame_center_y = self.frame_height // 2  # 540
        
        # Motor specifications
        self.motor_center_pan = 90
        self.motor_center_tilt = 90
        
        # Calibration ratios (these should be calculated from manual calibration)
        # Default values - should be updated with real calibration data
        self.pan_ratio = -0.1  # degrees per pixel (negative because left is decrease)
        self.tilt_ratio = 0.08  # degrees per pixel (positive because up is increase)
        
        # Try to load calibration data if available
        self.load_calibration_data()
        
        print(f"🎯 Face Processor with Position Calculation")
        print(f"📐 Frame: {self.frame_width}x{self.frame_height}, Center: ({self.frame_center_x}, {self.frame_center_y})")
        print(f"🤖 Motor Center: Pan={self.motor_center_pan}°, Tilt={self.motor_center_tilt}°")
        print(f"📊 Calibration Ratios: Pan={self.pan_ratio:.6f}, Tilt={self.tilt_ratio:.6f}")
    
    def load_calibration_data(self):
        """Load calibration data from manual calibration if available"""
        try:
            import json
            with open("/tmp/manual_calibration_ratios.json", 'r') as f:
                calibration = json.load(f)
            
            self.pan_ratio = calibration['calibration_ratios']['pan']
            self.tilt_ratio = calibration['calibration_ratios']['tilt']
            
            print(f"✅ Loaded calibration ratios from manual calibration")
            
        except FileNotFoundError:
            print(f"⚠️ No manual calibration found, using default ratios")
        except Exception as e:
            print(f"⚠️ Error loading calibration: {e}, using default ratios")
    
    def connect(self):
        try:
            self.arduino = serial.Serial(self.port, 9600, timeout=3)
            time.sleep(3)
            self.arduino.reset_input_buffer()
            
            # Test connection
            self.arduino.write(b'PING\n')
            self.arduino.flush()
            
            start_time = time.time()
            while time.time() - start_time < 3:
                if self.arduino.in_waiting > 0:
                    response = self.arduino.readline().decode().strip()
                    if "PONG" in response:
                        print(f"✅ Connected to Arduino on {self.port}")
                        return True
                time.sleep(0.1)
            return False
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def calculate_face_motor_position(self, x1, y1, x2, y2):
        """Calculate motor position to point at face center"""
        # Calculate face center
        face_center_x = (x1 + x2) // 2
        face_center_y = (y1 + y2) // 2
        
        # Calculate offset from frame center
        offset_x = face_center_x - self.frame_center_x  # Negative = left, Positive = right
        offset_y = face_center_y - self.frame_center_y  # Negative = up, Positive = down
        
        # Calculate required motor movement
        pan_movement = offset_x * self.pan_ratio
        tilt_movement = offset_y * self.tilt_ratio
        
        # Calculate final motor positions
        target_pan = self.motor_center_pan + pan_movement
        target_tilt = self.motor_center_tilt + tilt_movement
        
        # Clamp to motor limits
        target_pan = max(0, min(180, target_pan))
        target_tilt = max(0, min(180, target_tilt))
        
        print(f"📍 Face center: ({face_center_x}, {face_center_y})")
        print(f"📏 Offset from center: X={offset_x}, Y={offset_y}")
        print(f"🎯 Motor target: Pan={target_pan:.1f}°, Tilt={target_tilt:.1f}°")
        
        return int(target_pan), int(target_tilt)
    
    def send_motor_position(self, pan, tilt):
        """Send motor to specific position"""
        try:
            cmd = f"MOVE {pan} {tilt}"
            print(f"📤 {cmd}")
            self.arduino.write((cmd + '\n').encode())
            self.arduino.flush()
            
            # Wait for movement to complete
            start_time = time.time()
            while time.time() - start_time < 15:  # Longer timeout for movement
                if self.arduino.in_waiting > 0:
                    response = self.arduino.readline().decode().strip()
                    if response:
                        print(f"📥 {response}")
                        if "MOVED" in response or "DONE" in response:
                            return True
                time.sleep(0.1)
            return True
        except Exception as e:
            print(f"❌ Motor command error: {e}")
            return False
        try:
            print(f"📤 {cmd}")
            self.arduino.write((cmd + '\n').encode())
            self.arduino.flush()
            
            # Read responses
            start_time = time.time()
            while time.time() - start_time < 10:
                if self.arduino.in_waiting > 0:
                    response = self.arduino.readline().decode().strip()
                    if response:
                        print(f"📥 {response}")
                        if "READY" in response:
                            return True
                time.sleep(0.1)
            return True
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def send_command(self, cmd):
        try:
            print(f"📤 {cmd}")
            self.arduino.write((cmd + '\n').encode())
            self.arduino.flush()
            
            # Read responses
            start_time = time.time()
            while time.time() - start_time < 10:
                if self.arduino.in_waiting > 0:
                    response = self.arduino.readline().decode().strip()
                    if response:
                        print(f"📥 {response}")
                        if "READY" in response:
                            return True
                time.sleep(0.1)
            return True
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def process_faces_with_positioning(self, face_positions):
        """Process faces and move motor to point at each one"""
        print(f"\n🎯 Processing {len(face_positions)} faces with precise positioning")
        
        # Move to home position first
        print("🏠 Moving to home position...")
        if not self.send_motor_position(self.motor_center_pan, self.motor_center_tilt):
            print("❌ Failed to move to home position")
            return False
        
        time.sleep(2)  # Allow time to reach home
        
        # Process each face
        for i, (x1, y1, x2, y2, conf) in enumerate(face_positions, 1):
            print(f"\n--- Face {i}/{len(face_positions)} ---")
            print(f"🎯 Face bbox: ({x1}, {y1}) to ({x2}, {y2}), confidence: {conf:.3f}")
            
            # Calculate motor position for this face
            target_pan, target_tilt = self.calculate_face_motor_position(x1, y1, x2, y2)
            
            # Move motor to point at this face
            print(f"🤖 Moving to point at face {i}...")
            if self.send_motor_position(target_pan, target_tilt):
                print(f"✅ Motor positioned for face {i}")
                time.sleep(3)  # Hold position for 3 seconds
            else:
                print(f"❌ Failed to position motor for face {i}")
        
        # Return to home position
        print(f"\n🏠 Returning to home position...")
        self.send_motor_position(self.motor_center_pan, self.motor_center_tilt)
        
        print(f"\n🎊 All {len(face_positions)} faces processed!")
        return True
    def process_faces(self, face_positions):
        """Legacy method - now calls the new positioning method"""
        return self.process_faces_with_positioning(face_positions)
    
    def disconnect(self):
        if self.arduino:
            self.arduino.close()
            print("🔌 Disconnected")

def process_faces_from_json(json_file_path, port="/dev/ttyACM0", min_confidence=0.3):
    """Process faces from JSON file output of YOLO detection"""
    try:
        with open(json_file_path, 'r') as f:
            face_data = json.load(f)
        
        # Convert to face_positions format
        face_positions = []
        for face in face_data.get('faces', []):
            if face['confidence'] >= min_confidence:
                bbox = face['bbox']
                face_positions.append((bbox[0], bbox[1], bbox[2], bbox[3], face['confidence']))
        
        if not face_positions:
            print(f"❌ No faces meet confidence threshold {min_confidence}")
            return False
        
        processor = MinimalFaceProcessor(port)
        
        if not processor.connect():
            print("❌ Cannot connect to Arduino")
            return False
        
        try:
            success = processor.process_faces(face_positions)
            return success
        finally:
            processor.disconnect()
            
    except Exception as e:
        print(f"❌ Error processing faces from JSON: {e}")
        return False

def interactive_mode():
    """Original interactive mode with hardcoded faces"""
    print("🎯 Minimal Face Processor")
    print("Memory-optimized for Arduino Uno")
    print("=" * 50)
    
    # Your complete face positions from YOLO detection
    face_positions = [
        (1163, 138, 1183, 165, 0.8073931932449341), (1095, 127, 1118, 156, 0.8052961230278015),
        (845, 141, 869, 172, 0.8009026050567627), (712, 115, 736, 145, 0.8005936741828918),
        (476, 264, 501, 299, 0.7926194667816162), (522, 284, 546, 319, 0.785941481590271),
        (585, 323, 619, 365, 0.7856873869895935), (361, 141, 378, 163, 0.7855387926101685),
        (1230, 178, 1248, 206, 0.7812513113021851), (444, 187, 464, 214, 0.7790361046791077),
        (462, 114, 480, 137, 0.7750246524810791), (378, 171, 397, 196, 0.774412214756012),
        (590, 148, 612, 177, 0.7742810249328613), (647, 359, 680, 398, 0.7726911902427673),
        (550, 118, 569, 143, 0.7703436613082886), (764, 130, 786, 158, 0.7658398747444153),
        (909, 103, 928, 125, 0.7584222555160522), (687, 117, 707, 144, 0.7494418621063232),
        (448, 110, 461, 128, 0.7472586631774902), (824, 82, 842, 106, 0.7454808950424194),
        (957, 137, 975, 159, 0.7343994379043579), (497, 79, 510, 94, 0.7314244508743286),
        (327, 141, 342, 160, 0.7313395738601685), (521, 116, 538, 138, 0.7246564626693726),
        (1030, 112, 1050, 140, 0.7192106246948242), (285, 153, 300, 172, 0.7133362293243408),
        (664, 79, 679, 96, 0.705007016658783), (345, 180, 365, 202, 0.6955623030662537),
        (374, 115, 388, 133, 0.6630188226699829), (67, 274, 86, 303, 0.6499727368354797),
        (393, 104, 407, 122, 0.6494697332382202), (726, 83, 743, 103, 0.6452885866165161),
        (643, 103, 659, 125, 0.6188916563987732), (535, 76, 548, 91, 0.5876395106315613),
        (424, 97, 437, 113, 0.5642848014831543), (574, 114, 591, 135, 0.5489290356636047),
        (178, 244, 196, 272, 0.5098875164985657), (249, 202, 266, 225, 0.4537358582019806),
        (616, 68, 631, 86, 0.4520191252231598), (535, 101, 550, 119, 0.3962017297744751),
        (548, 72, 560, 88, 0.30524948239326477), (430, 248, 450, 275, 0.30330559611320496)
    ]
    
    print(f"📊 Total faces detected: {len(face_positions)}")
    
    # Filter by confidence if desired
    min_confidence = float(input("Minimum confidence threshold (0.0-1.0) [0.3]: ") or "0.3")
    filtered_faces = [face for face in face_positions if face[4] >= min_confidence]
    
    print(f"🔍 Faces with confidence >= {min_confidence}: {len(filtered_faces)}")
    
    if not filtered_faces:
        print("❌ No faces meet confidence threshold")
        return
    
    # Choose how many faces to process
    num_faces = int(input(f"How many faces to process (1-{len(filtered_faces)}) [ALL]: ") or str(len(filtered_faces)))
    test_faces = filtered_faces[:num_faces]
    
    print(f"🎯 Will process {len(test_faces)} faces")
    
    processor = MinimalFaceProcessor()
    
    if not processor.connect():
        print("❌ Cannot connect to Arduino")
        print("Make sure minimal_face_arduino.ino is uploaded")
        return
    
    try:
        # Test basic movement first
        print("\n🧪 Testing basic movements...")
        processor.send_command("CENTER")
        processor.send_command("MOVE 200 0")  # Pan right
        processor.send_command("MOVE -200 0") # Pan left  
        processor.send_command("MOVE 0 100")  # Tilt up
        processor.send_command("MOVE 0 -100") # Tilt down
        processor.send_command("CENTER")
        
        proceed = input("\nDid you see both motors move? (y/n): ").lower()
        if proceed != 'y':
            print("❌ Check motor connections and power")
            return
        
        # Process faces
        print(f"\n🎬 Processing {len(test_faces)} faces...")
        success = processor.process_faces(test_faces)
        
        if success:
            print("\n✅ Face processing completed!")
        else:
            print("\n❌ Face processing failed")
    
    except KeyboardInterrupt:
        print("\n⏹️ Interrupted")
        processor.send_command("CENTER")
    
    finally:
        processor.disconnect()

def interactive_mode():
    """Original interactive mode with hardcoded faces"""
    print("🎯 Minimal Face Processor")
    print("Memory-optimized for Arduino Uno")
    print("=" * 50)
    
    # Your complete face positions from YOLO detection
    face_positions = [
        (1163, 138, 1183, 165, 0.8073931932449341), (1095, 127, 1118, 156, 0.8052961230278015),
        (845, 141, 869, 172, 0.8009026050567627), (712, 115, 736, 145, 0.8005936741828918),
        (476, 264, 501, 299, 0.7926194667816162), (522, 284, 546, 319, 0.785941481590271),
        (585, 323, 619, 365, 0.7856873869895935), (361, 141, 378, 163, 0.7855387926101685),
        (1230, 178, 1248, 206, 0.7812513113021851), (444, 187, 464, 214, 0.7790361046791077),
        (462, 114, 480, 137, 0.7750246524810791), (378, 171, 397, 196, 0.774412214756012),
        (590, 148, 612, 177, 0.7742810249328613), (647, 359, 680, 398, 0.7726911902427673),
        (550, 118, 569, 143, 0.7703436613082886), (764, 130, 786, 158, 0.7658398747444153),
        (909, 103, 928, 125, 0.7584222555160522), (687, 117, 707, 144, 0.7494418621063232),
        (448, 110, 461, 128, 0.7472586631774902), (824, 82, 842, 106, 0.7454808950424194),
        (957, 137, 975, 159, 0.7343994379043579), (497, 79, 510, 94, 0.7314244508743286),
        (327, 141, 342, 160, 0.7313395738601685), (521, 116, 538, 138, 0.7246564626693726),
        (1030, 112, 1050, 140, 0.7192106246948242), (285, 153, 300, 172, 0.7133362293243408),
        (664, 79, 679, 96, 0.705007016658783), (345, 180, 365, 202, 0.6955623030662537),
        (374, 115, 388, 133, 0.6630188226699829), (67, 274, 86, 303, 0.6499727368354797),
        (393, 104, 407, 122, 0.6494697332382202), (726, 83, 743, 103, 0.6452885866165161),
        (643, 103, 659, 125, 0.6188916563987732), (535, 76, 548, 91, 0.5876395106315613),
        (424, 97, 437, 113, 0.5642848014831543), (574, 114, 591, 135, 0.5489290356636047),
        (178, 244, 196, 272, 0.5098875164985657), (249, 202, 266, 225, 0.4537358582019806),
        (616, 68, 631, 86, 0.4520191252231598), (535, 101, 550, 119, 0.3962017297744751),
        (548, 72, 560, 88, 0.30524948239326477), (430, 248, 450, 275, 0.30330559611320496)
    ]
    
    print(f"📊 Total faces detected: {len(face_positions)}")
    
    # Filter by confidence if desired
    min_confidence = float(input("Minimum confidence threshold (0.0-1.0) [0.3]: ") or "0.3")
    filtered_faces = [face for face in face_positions if face[4] >= min_confidence]
    
    print(f"🔍 Faces with confidence >= {min_confidence}: {len(filtered_faces)}")
    
    if not filtered_faces:
        print("❌ No faces meet confidence threshold")
        return
    
    # Choose how many faces to process
    num_faces = int(input(f"How many faces to process (1-{len(filtered_faces)}) [ALL]: ") or str(len(filtered_faces)))
    test_faces = filtered_faces[:num_faces]
    
    print(f"🎯 Will process {len(test_faces)} faces")
    
    processor = MinimalFaceProcessor()
    
    if not processor.connect():
        print("❌ Cannot connect to Arduino")
        print("Make sure minimal_face_arduino.ino is uploaded")
        return
    
    try:
        # Test basic movement first
        print("\n🧪 Testing basic movements...")
        processor.send_command("CENTER")
        processor.send_command("MOVE 200 0")  # Pan right
        processor.send_command("MOVE -200 0") # Pan left  
        processor.send_command("MOVE 0 100")  # Tilt up
        processor.send_command("MOVE 0 -100") # Tilt down
        processor.send_command("CENTER")
        
        proceed = input("\nDid you see both motors move? (y/n): ").lower()
        if proceed != 'y':
            print("❌ Check motor connections and power")
            return
        
        # Process faces
        print(f"\n🎬 Processing {len(test_faces)} faces...")
        success = processor.process_faces(test_faces)
        
        if success:
            print("\n✅ Face processing completed!")
        else:
            print("\n❌ Face processing failed")
    
    except KeyboardInterrupt:
        print("\n⏹️ Interrupted")
        processor.send_command("CENTER")
    
    finally:
        processor.disconnect()

def main():
    parser = argparse.ArgumentParser(description='Minimal Face Processor for Arduino')
    parser.add_argument('input_file', nargs='?', help='JSON file with face detection results')
    parser.add_argument('--port', default='/dev/ttyACM0', help='Arduino serial port (default: /dev/ttyACM0)')
    parser.add_argument('--confidence', type=float, default=0.3, help='Minimum confidence threshold (default: 0.3)')
    parser.add_argument('--interactive', action='store_true', help='Run in interactive mode with hardcoded faces')
    
    args = parser.parse_args()
    
    if args.interactive or not args.input_file:
        interactive_mode()
    else:
        print(f"🤖 Processing faces from {args.input_file}")
        success = process_faces_from_json(args.input_file, args.port, args.confidence)
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
