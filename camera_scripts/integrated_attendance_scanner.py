#!/usr/bin/env python3
"""
Integrated Attendance Scanner
Combines systematic space scanning with real-time face detection

Features:
- Automatic scanning while detecting faces
- Real-time attendance recording
- Professional movement patterns
- Comprehensive logging and reporting

Author: Professional Attendance System
Version: 1.0
"""

import cv2
import numpy as np
import serial
import time
import threading
import json
import sqlite3
from datetime import datetime
import logging
import insightface
from insightface.app import FaceAnalysis

class AttendanceScanner:
    def __init__(self, camera_id=0, arduino_port='/dev/ttyUSB0'):
        """Initialize the integrated attendance scanner"""
        self.camera_id = camera_id
        self.arduino_port = arduino_port
        self.cap = None
        self.arduino = None
        self.face_app = None
        
        # Scanning state
        self.scanning = False
        self.auto_scan = False
        self.detected_faces = []
        self.attendance_records = []
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('attendance_scanner.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for attendance"""
        self.db_conn = sqlite3.connect('attendance_scanner.db', check_same_thread=False)
        cursor = self.db_conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_start DATETIME,
            session_end DATETIME,
            total_faces_detected INTEGER,
            scan_positions INTEGER,
            status TEXT
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS face_detections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            detection_time DATETIME,
            pan_position INTEGER,
            tilt_position INTEGER,
            face_count INTEGER,
            confidence REAL,
            FOREIGN KEY (session_id) REFERENCES attendance_sessions (id)
        )
        ''')
        
        self.db_conn.commit()
        self.logger.info("Database initialized")
    
    def initialize_systems(self):
        """Initialize camera, Arduino, and face detection"""
        success = True
        
        # Initialize camera
        try:
            self.cap = cv2.VideoCapture(self.camera_id)
            if not self.cap.isOpened():
                self.logger.error("Failed to open camera")
                success = False
            else:
                # Set camera properties for better quality
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                self.cap.set(cv2.CAP_PROP_FPS, 30)
                self.logger.info("Camera initialized")
        except Exception as e:
            self.logger.error(f"Camera initialization error: {e}")
            success = False
        
        # Initialize Arduino
        try:
            self.arduino = serial.Serial(self.arduino_port, 9600, timeout=1)
            time.sleep(2)  # Wait for Arduino reset
            
            # Test connection
            self.arduino.write(b"PING\n")
            time.sleep(0.5)
            response = self.arduino.readline().decode().strip()
            
            if "PONG" in response:
                self.logger.info("Arduino connected successfully")
            else:
                self.logger.error("Arduino connection failed")
                success = False
                
        except Exception as e:
            self.logger.error(f"Arduino initialization error: {e}")
            success = False
        
        # Initialize face detection
        try:
            self.face_app = FaceAnalysis()
            self.face_app.prepare(ctx_id=0, det_size=(640, 640))
            self.logger.info("Face detection initialized")
        except Exception as e:
            self.logger.error(f"Face detection initialization error: {e}")
            success = False
        
        return success
    
    def start_attendance_session(self):
        """Start a new attendance scanning session"""
        if not all([self.cap, self.arduino, self.face_app]):
            self.logger.error("Systems not properly initialized")
            return False
        
        # Create new session in database
        cursor = self.db_conn.cursor()
        cursor.execute('''
        INSERT INTO attendance_sessions (session_start, status)
        VALUES (?, ?)
        ''', (datetime.now(), 'ACTIVE'))
        
        self.session_id = cursor.lastrowid
        self.db_conn.commit()
        
        self.scanning = True
        self.detected_faces = []
        self.attendance_records = []
        
        # Start scanning thread
        self.scan_thread = threading.Thread(target=self._scanning_loop)
        self.scan_thread.daemon = True
        self.scan_thread.start()
        
        # Start face detection thread
        self.detection_thread = threading.Thread(target=self._detection_loop)
        self.detection_thread.daemon = True
        self.detection_thread.start()
        
        self.logger.info(f"Attendance session {self.session_id} started")
        return True
    
    def stop_attendance_session(self):
        """Stop the current attendance session"""
        self.scanning = False
        
        # Send stop command to Arduino
        if self.arduino:
            self.arduino.write(b"STOP\n")
        
        # Update database
        cursor = self.db_conn.cursor()
        cursor.execute('''
        UPDATE attendance_sessions 
        SET session_end = ?, total_faces_detected = ?, status = ?
        WHERE id = ?
        ''', (datetime.now(), len(self.detected_faces), 'COMPLETED', self.session_id))
        
        self.db_conn.commit()
        
        self.logger.info(f"Attendance session {self.session_id} completed")
        self._generate_session_report()
    
    def _scanning_loop(self):
        """Main scanning loop - systematic space coverage"""
        try:
            # Start systematic scanning
            self.arduino.write(b"START\n")
            time.sleep(1)
            
            scan_position = 0
            
            while self.scanning:
                if self.arduino.in_waiting:
                    line = self.arduino.readline().decode().strip()
                    
                    if line.startswith("SCAN ["):
                        scan_position += 1
                        self.logger.info(f"Scanner: {line}")
                        
                        # Parse position info for database
                        try:
                            # Extract pan/tilt position from Arduino response
                            # This would need to be implemented based on your Arduino response format
                            pan_pos, tilt_pos = self._parse_position_from_arduino()
                            
                            # Record scan position
                            self._record_scan_position(scan_position, pan_pos, tilt_pos)
                            
                        except Exception as e:
                            self.logger.error(f"Position parsing error: {e}")
                    
                    elif "ALL ROWS COMPLETE" in line:
                        self.logger.info("Systematic scan completed")
                        break
                
                time.sleep(0.1)
                
        except Exception as e:
            self.logger.error(f"Scanning loop error: {e}")
    
    def _detection_loop(self):
        """Face detection loop - runs continuously during scanning"""
        try:
            frame_count = 0
            
            while self.scanning:
                ret, frame = self.cap.read()
                if not ret:
                    continue
                
                frame_count += 1
                
                # Process every 5th frame to reduce CPU load
                if frame_count % 5 == 0:
                    faces = self.face_app.get(frame)
                    
                    if faces:
                        self.logger.info(f"Detected {len(faces)} faces")
                        
                        # Record face detection
                        self._record_face_detection(len(faces), faces)
                        
                        # Draw faces on frame
                        for face in faces:
                            bbox = face.bbox.astype(int)
                            cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 255, 0), 2)
                            
                            # Add confidence score
                            confidence = face.det_score
                            cv2.putText(frame, f'{confidence:.2f}', 
                                      (bbox[0], bbox[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                
                # Add scanning status overlay
                self._add_status_overlay(frame)
                
                # Display frame
                cv2.imshow('Attendance Scanner', frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                
        except Exception as e:
            self.logger.error(f"Detection loop error: {e}")
        
        finally:
            cv2.destroyAllWindows()
    
    def _parse_position_from_arduino(self):
        """Parse current pan/tilt position from Arduino"""
        # Send status command to get current position
        self.arduino.write(b"STATUS\n")
        time.sleep(0.1)
        
        response = ""
        while self.arduino.in_waiting:
            response += self.arduino.readline().decode()
        
        # Parse position from response (implementation depends on Arduino response format)
        pan_pos = 0  # Default values
        tilt_pos = 0
        
        # Add parsing logic based on your Arduino status response format
        # Example: "Position: Pan=100, Tilt=50"
        
        return pan_pos, tilt_pos
    
    def _record_scan_position(self, position, pan_pos, tilt_pos):
        """Record scan position in database"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
            INSERT INTO face_detections (session_id, detection_time, pan_position, tilt_position, face_count, confidence)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (self.session_id, datetime.now(), pan_pos, tilt_pos, 0, 0.0))
            
            self.db_conn.commit()
        except Exception as e:
            self.logger.error(f"Database recording error: {e}")
    
    def _record_face_detection(self, face_count, faces):
        """Record face detection in database"""
        try:
            # Get current position (would need to implement position tracking)
            pan_pos, tilt_pos = self._parse_position_from_arduino()
            
            # Calculate average confidence
            avg_confidence = sum(face.det_score for face in faces) / len(faces) if faces else 0.0
            
            cursor = self.db_conn.cursor()
            cursor.execute('''
            INSERT INTO face_detections (session_id, detection_time, pan_position, tilt_position, face_count, confidence)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (self.session_id, datetime.now(), pan_pos, tilt_pos, face_count, avg_confidence))
            
            self.db_conn.commit()
            
            # Add to in-memory records
            self.detected_faces.append({
                'timestamp': datetime.now().isoformat(),
                'face_count': face_count,
                'confidence': avg_confidence,
                'position': {'pan': pan_pos, 'tilt': tilt_pos}
            })
            
        except Exception as e:
            self.logger.error(f"Face recording error: {e}")
    
    def _add_status_overlay(self, frame):
        """Add status information overlay to frame"""
        h, w = frame.shape[:2]
        
        # Status background
        cv2.rectangle(frame, (10, 10), (400, 120), (0, 0, 0), -1)
        
        # Status text
        status_text = [
            f"Session ID: {getattr(self, 'session_id', 'N/A')}",
            f"Faces Detected: {len(self.detected_faces)}",
            f"Scanning: {'ACTIVE' if self.scanning else 'STOPPED'}",
            f"Time: {datetime.now().strftime('%H:%M:%S')}"
        ]
        
        for i, text in enumerate(status_text):
            cv2.putText(frame, text, (15, 30 + i*20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    
    def _generate_session_report(self):
        """Generate comprehensive session report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"attendance_report_{self.session_id}_{timestamp}.json"
        
        report = {
            'session_id': self.session_id,
            'start_time': 'TBD',  # Would get from database
            'end_time': datetime.now().isoformat(),
            'total_faces_detected': len(self.detected_faces),
            'unique_positions_scanned': 'TBD',  # Calculate from database
            'face_detections': self.detected_faces,
            'summary': {
                'peak_detection_time': 'TBD',
                'average_confidence': sum(f.get('confidence', 0) for f in self.detected_faces) / len(self.detected_faces) if self.detected_faces else 0,
                'scan_coverage': '100%'  # Assuming full systematic scan
            }
        }
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info(f"Session report saved to {report_file}")
    
    def cleanup(self):
        """Cleanup resources"""
        self.scanning = False
        
        if self.cap:
            self.cap.release()
        
        if self.arduino:
            self.arduino.close()
        
        if self.db_conn:
            self.db_conn.close()
        
        cv2.destroyAllWindows()
        self.logger.info("Systems cleaned up")

def main():
    """Main function for integrated attendance scanner"""
    print("=== Integrated Attendance Scanner ===")
    
    scanner = AttendanceScanner()
    
    if not scanner.initialize_systems():
        print("Failed to initialize systems")
        return
    
    try:
        print("Starting attendance session...")
        if scanner.start_attendance_session():
            print("Session started successfully. Press 'q' in camera window or Ctrl+C to stop.")
            
            # Keep main thread alive
            while scanner.scanning:
                time.sleep(1)
        else:
            print("Failed to start session")
    
    except KeyboardInterrupt:
        print("\nStopping session...")
    
    finally:
        scanner.stop_attendance_session()
        scanner.cleanup()
        print("Session completed")

if __name__ == "__main__":
    main()
