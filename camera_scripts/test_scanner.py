#!/usr/bin/env python3
"""
Arduino Scanner Test Script
Simple script to test the professional space scanner

Usage: python3 test_scanner.py [port]
"""

import serial
import time
import sys

def test_scanner(port='/dev/ttyUSB0'):
    """Test the Arduino scanner functionality"""
    print(f"Testing Arduino Scanner on {port}")
    print("=" * 50)
    
    try:
        # Connect to Arduino
        arduino = serial.Serial(port, 9600, timeout=2)
        time.sleep(2)  # Wait for Arduino reset
        
        print("✓ Connected to Arduino")
        
        # Test PING command
        arduino.write(b"PING\n")
        time.sleep(0.5)
        response = read_response(arduino)
        
        if "PONG" in response:
            print("✓ PING test passed")
        else:
            print("✗ PING test failed")
            return False
        
        # Get configuration
        print("\n--- Getting Configuration ---")
        arduino.write(b"CONFIG\n")
        time.sleep(0.5)
        config = read_response(arduino)
        print(config)
        
        # Get initial status
        print("\n--- Getting Status ---")
        arduino.write(b"STATUS\n")
        time.sleep(0.5)
        status = read_response(arduino)
        print(status)
        
        # Test HOME command
        print("\n--- Testing HOME command ---")
        arduino.write(b"HOME\n")
        time.sleep(3)
        home_response = read_response(arduino)
        print(home_response)
        
        # Interactive menu
        while True:
            print("\n" + "=" * 50)
            print("Scanner Test Menu:")
            print("1. Start scanning")
            print("2. Pause scanning")
            print("3. Resume scanning")
            print("4. Stop scanning")
            print("5. Go home")
            print("6. Get status")
            print("7. Monitor scanning (real-time)")
            print("8. Exit")
            
            choice = input("Enter choice (1-8): ").strip()
            
            if choice == '1':
                print("Starting scanning...")
                arduino.write(b"START\n")
                time.sleep(1)
                response = read_response(arduino)
                print(response)
                
            elif choice == '2':
                print("Pausing scanning...")
                arduino.write(b"PAUSE\n")
                time.sleep(0.5)
                response = read_response(arduino)
                print(response)
                
            elif choice == '3':
                print("Resuming scanning...")
                arduino.write(b"RESUME\n")
                time.sleep(0.5)
                response = read_response(arduino)
                print(response)
                
            elif choice == '4':
                print("Stopping scanning...")
                arduino.write(b"STOP\n")
                time.sleep(2)
                response = read_response(arduino)
                print(response)
                
            elif choice == '5':
                print("Moving to home position...")
                arduino.write(b"HOME\n")
                time.sleep(3)
                response = read_response(arduino)
                print(response)
                
            elif choice == '6':
                print("Getting status...")
                arduino.write(b"STATUS\n")
                time.sleep(0.5)
                response = read_response(arduino)
                print(response)
                
            elif choice == '7':
                print("Monitoring scanning... (Press Ctrl+C to stop)")
                monitor_scanning(arduino)
                
            elif choice == '8':
                print("Exiting...")
                break
                
            else:
                print("Invalid choice")
        
        arduino.close()
        print("Disconnected from Arduino")
        
    except serial.SerialException as e:
        print(f"Serial error: {e}")
        print("Make sure Arduino is connected and port is correct")
        return False
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False
    
    return True

def read_response(arduino, timeout=5):
    """Read response from Arduino until READY"""
    response = ""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        if arduino.in_waiting:
            line = arduino.readline().decode().strip()
            response += line + "\n"
            
            if line == "READY":
                break
        time.sleep(0.01)
    
    return response.strip()

def monitor_scanning(arduino):
    """Monitor scanning progress in real-time"""
    try:
        while True:
            if arduino.in_waiting:
                line = arduino.readline().decode().strip()
                if line:
                    timestamp = time.strftime("%H:%M:%S")
                    print(f"[{timestamp}] {line}")
                    
                    if "ALL ROWS COMPLETE" in line:
                        print("Scanning completed!")
                        break
            
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\nMonitoring stopped")

def main():
    """Main function"""
    port = '/dev/ttyUSB0'
    
    if len(sys.argv) > 1:
        port = sys.argv[1]
    
    print("Arduino Scanner Test Script")
    print(f"Using port: {port}")
    print("Make sure your Arduino is running the professional_space_scanner.ino code")
    print()
    
    input("Press Enter to continue...")
    
    test_scanner(port)

if __name__ == "__main__":
    main()
