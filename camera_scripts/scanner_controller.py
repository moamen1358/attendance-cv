#!/usr/bin/env python3
"""
Professional Space Scanner Controller
Coordinates Arduino scanner with face detection system

Features:
- Real-time scanner communication
- Integration with face detection
- Automatic scanning modes
- Progress monitoring
- Professional logging

Author: Professional Scanning System
Version: 1.0
"""

import serial
import time
import threading
import json
from datetime import datetime
import logging

class SpaceScanner:
    def __init__(self, port='/dev/ttyUSB0', baudrate=9600):
        """Initialize the space scanner controller"""
        self.port = port
        self.baudrate = baudrate
        self.arduino = None
        self.connected = False
        self.scanning = False
        self.scan_data = []
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('scanner.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def connect(self):
        """Connect to Arduino scanner"""
        try:
            self.arduino = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(2)  # Wait for Arduino reset
            
            # Test connection
            response = self.send_command("PING")
            if "PONG" in response:
                self.connected = True
                self.logger.info("Successfully connected to scanner")
                
                # Get configuration
                config = self.send_command("CONFIG")
                self.logger.info("Scanner configuration received")
                
                return True
            else:
                self.logger.error("Failed to receive PONG response")
                return False
                
        except Exception as e:
            self.logger.error(f"Connection error: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from Arduino"""
        if self.arduino:
            self.arduino.close()
            self.connected = False
            self.logger.info("Disconnected from scanner")
    
    def send_command(self, command):
        """Send command to Arduino and get response"""
        if not self.connected:
            return "ERROR: Not connected"
        
        try:
            # Send command
            self.arduino.write(f"{command}\n".encode())
            self.logger.debug(f"Sent: {command}")
            
            # Read response
            response = ""
            start_time = time.time()
            
            while time.time() - start_time < 5:  # 5 second timeout
                if self.arduino.in_waiting:
                    line = self.arduino.readline().decode().strip()
                    response += line + "\n"
                    
                    if line == "READY":
                        break
                time.sleep(0.01)
            
            self.logger.debug(f"Received: {response}")
            return response
            
        except Exception as e:
            self.logger.error(f"Command error: {e}")
            return f"ERROR: {e}"
    
    def start_scanning(self):
        """Start systematic scanning"""
        if not self.connected:
            return False
        
        self.logger.info("Starting systematic scanning")
        response = self.send_command("START")
        
        if "SCAN STARTED" in response:
            self.scanning = True
            self.scan_data = []
            
            # Start monitoring thread
            monitor_thread = threading.Thread(target=self._monitor_scanning)
            monitor_thread.daemon = True
            monitor_thread.start()
            
            return True
        else:
            self.logger.error("Failed to start scanning")
            return False
    
    def pause_scanning(self):
        """Pause current scanning"""
        response = self.send_command("PAUSE")
        self.logger.info("Scanning paused")
        return "SCAN PAUSED" in response
    
    def resume_scanning(self):
        """Resume paused scanning"""
        response = self.send_command("RESUME")
        self.logger.info("Scanning resumed")
        return "SCAN RESUMED" in response
    
    def stop_scanning(self):
        """Stop scanning and return home"""
        response = self.send_command("STOP")
        self.scanning = False
        self.logger.info("Scanning stopped")
        return "SCAN COMPLETED" in response
    
    def go_home(self):
        """Move scanner to center position"""
        response = self.send_command("HOME")
        return "CENTERED" in response
    
    def get_status(self):
        """Get current scanner status"""
        response = self.send_command("STATUS")
        return self._parse_status(response)
    
    def _monitor_scanning(self):
        """Monitor scanning progress in background"""
        while self.scanning and self.connected:
            try:
                if self.arduino.in_waiting:
                    line = self.arduino.readline().decode().strip()
                    
                    if line.startswith("SCAN ["):
                        # Parse scan position data
                        scan_info = self._parse_scan_line(line)
                        if scan_info:
                            self.scan_data.append(scan_info)
                            self.logger.info(f"Scan position: {scan_info}")
                    
                    elif "ALL ROWS COMPLETE" in line:
                        self.scanning = False
                        self.logger.info("Scanning completed successfully")
                        self._save_scan_data()
                        break
                
                time.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"Monitoring error: {e}")
                break
    
    def _parse_scan_line(self, line):
        """Parse scan position line from Arduino"""
        try:
            # Example: "SCAN [1/5][3/9] 21/45"
            parts = line.split('] ')
            if len(parts) >= 2:
                row_info = parts[0].replace('SCAN [', '')
                col_info = parts[1].replace('[', '').replace(']', '')
                total_info = parts[2] if len(parts) > 2 else ""
                
                row_current, row_total = map(int, row_info.split('/'))
                col_current, col_total = map(int, col_info.split('/'))
                
                if total_info:
                    pos_current, pos_total = map(int, total_info.split('/'))
                else:
                    pos_current = pos_total = 0
                
                return {
                    'timestamp': datetime.now().isoformat(),
                    'row': {'current': row_current, 'total': row_total},
                    'column': {'current': col_current, 'total': col_total},
                    'position': {'current': pos_current, 'total': pos_total},
                    'progress_percent': (pos_current / pos_total * 100) if pos_total > 0 else 0
                }
        except Exception as e:
            self.logger.error(f"Parse error: {e}")
        
        return None
    
    def _parse_status(self, response):
        """Parse status response from Arduino"""
        status = {}
        lines = response.split('\n')
        
        for line in lines:
            if 'State:' in line:
                status['state'] = line.split('State: ')[1].strip()
            elif 'Position:' in line:
                pos_data = line.split('Position: ')[1]
                if 'Pan=' in pos_data and 'Tilt=' in pos_data:
                    pan = pos_data.split('Pan=')[1].split(',')[0]
                    tilt = pos_data.split('Tilt=')[1]
                    status['position'] = {'pan': int(pan), 'tilt': int(tilt)}
            elif 'Progress:' in line:
                progress_data = line.split('Progress: ')[1]
                if '/' in progress_data:
                    current, total = progress_data.split(' (')[0].split('/')
                    percent = progress_data.split('(')[1].split('%')[0]
                    status['progress'] = {
                        'current': int(current),
                        'total': int(total),
                        'percent': float(percent)
                    }
        
        return status
    
    def _save_scan_data(self):
        """Save scan data to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"scan_data_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.scan_data, f, indent=2)
        
        self.logger.info(f"Scan data saved to {filename}")

def main():
    """Main function for testing the scanner"""
    print("=== Professional Space Scanner Controller ===")
    
    # Initialize scanner
    scanner = SpaceScanner()
    
    if not scanner.connect():
        print("Failed to connect to scanner")
        return
    
    try:
        while True:
            print("\nCommands:")
            print("1. Start scanning")
            print("2. Pause scanning")
            print("3. Resume scanning")
            print("4. Stop scanning")
            print("5. Go home")
            print("6. Get status")
            print("7. Exit")
            
            choice = input("Enter choice (1-7): ").strip()
            
            if choice == '1':
                if scanner.start_scanning():
                    print("Scanning started successfully")
                else:
                    print("Failed to start scanning")
            
            elif choice == '2':
                if scanner.pause_scanning():
                    print("Scanning paused")
                else:
                    print("Failed to pause scanning")
            
            elif choice == '3':
                if scanner.resume_scanning():
                    print("Scanning resumed")
                else:
                    print("Failed to resume scanning")
            
            elif choice == '4':
                if scanner.stop_scanning():
                    print("Scanning stopped")
                else:
                    print("Failed to stop scanning")
            
            elif choice == '5':
                if scanner.go_home():
                    print("Moved to center position")
                else:
                    print("Failed to move home")
            
            elif choice == '6':
                status = scanner.get_status()
                print(f"Status: {json.dumps(status, indent=2)}")
            
            elif choice == '7':
                print("Exiting...")
                break
            
            else:
                print("Invalid choice")
    
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    
    finally:
        scanner.disconnect()
        print("Disconnected")

if __name__ == "__main__":
    main()
