# Professional Space Scanner System

A comprehensive Arduino-based camera scanning system for systematic space coverage during student attendance monitoring.

## 🎯 **System Overview**

This system provides:
- **Systematic Grid Scanning**: Left-to-right, top-to-bottom coverage
- **Professional Movement Patterns**: Smooth, precise motor control
- **Real-time Face Detection**: Integration with InsightFace
- **Attendance Logging**: Comprehensive database recording
- **Monitoring & Control**: Professional Python interface

## 📁 **Files Structure**

```
camera_scripts/
├── professional_space_scanner.ino    # Main Arduino scanning code
├── scanner_controller.py             # Python Arduino interface
├── integrated_attendance_scanner.py  # Full attendance system
├── test_scanner.py                   # Simple test script
└── README_SCANNER.md                 # This documentation
```

## 🔧 **Hardware Requirements**

### Arduino Setup
- **Arduino Uno/Nano** (minimum)
- **2x Stepper Motors** (NEMA 17 recommended)
- **2x Stepper Drivers** (A4988 or DRV8825)
- **Power Supply** (12V, 2A minimum)
- **Pan/Tilt Camera Mount**

### Wiring Diagram
```
Arduino Pin -> Component
Pin 2       -> Pan Motor Step
Pin 3       -> Pan Motor Direction  
Pin 4       -> Tilt Motor Step
Pin 5       -> Tilt Motor Direction
5V          -> Driver Logic Power
GND         -> Common Ground
```

### Camera Setup
- **USB Camera** or **RTSP Camera**
- **Mounting System** for pan/tilt motors
- **Stable Base** for vibration-free operation

## 🚀 **Quick Start Guide**

### 1. Arduino Setup
```bash
# Upload the Arduino code
# Open professional_space_scanner.ino in Arduino IDE
# Select your board and port
# Upload to Arduino
```

### 2. Python Dependencies
```bash
# Install required packages
pip install opencv-python
pip install pyserial
pip install insightface
pip install numpy
```

### 3. Basic Testing
```bash
# Test Arduino connection
python3 test_scanner.py /dev/ttyUSB0

# Follow the interactive menu to test functionality
```

### 4. Full System Operation
```bash
# Run integrated attendance scanner
python3 integrated_attendance_scanner.py
```

## 📋 **Arduino Commands**

| Command | Description | Example |
|---------|-------------|---------|
| `START` | Begin systematic scanning | `START` |
| `PAUSE` | Pause current scan | `PAUSE` |
| `RESUME` | Resume paused scan | `RESUME` |
| `STOP` | Stop scan and return home | `STOP` |
| `HOME` | Move to center position | `HOME` |
| `STATUS` | Get current status | `STATUS` |
| `CONFIG` | Show configuration | `CONFIG` |
| `PING` | Test connection | `PING` |

## ⚙️ **Configuration Parameters**

### Arduino Settings (in .ino file)
```cpp
// Scanning area (in motor steps)
const int PAN_RANGE = 400;      // ±200 steps from center
const int TILT_RANGE = 200;     // ±100 steps from center

// Step sizes for grid scanning
const int PAN_STEP_SIZE = 50;   // Horizontal spacing
const int TILT_STEP_SIZE = 40;  // Vertical spacing

// Timing parameters
const int STEP_DELAY = 600;     // Motor step delay (μs)
const int SCAN_PAUSE = 1500;    // Pause at each position (ms)
```

### Python Settings
```python
# Camera settings
CAMERA_ID = 0               # USB camera index
FRAME_WIDTH = 1280         # Camera resolution
FRAME_HEIGHT = 720

# Arduino connection
ARDUINO_PORT = '/dev/ttyUSB0'  # Serial port
BAUDRATE = 9600               # Communication speed
```

## 📊 **Scanning Pattern**

The scanner follows a systematic grid pattern:

```
1 → 2 → 3 → 4 → 5
               ↓
10← 9 ← 8 ← 7 ← 6
↓
11→ 12→ 13→ 14→ 15
                ↓
20← 19← 18← 17← 16
```

**Features:**
- **Bi-directional scanning** (left-right, right-left alternating)
- **Configurable grid density** via step sizes
- **Smooth transitions** between rows
- **Complete area coverage** guaranteed

## 🔍 **Face Detection Integration**

### Real-time Processing
- **InsightFace** for accurate detection
- **Confidence scoring** for quality assurance
- **Bounding box visualization**
- **Multi-face handling**

### Database Recording
- **SQLite database** for attendance records
- **Session management** with timestamps
- **Position tracking** for each detection
- **Comprehensive reporting**

## 📈 **Monitoring & Logging**

### Console Output
```
=== SCANNER STATUS ===
State: SCANNING
Position: Pan=150, Tilt=-50
Progress: 25/81 (30%)
Current Row: 3/9
Elapsed: 45s
=====================
```

### Log Files
- `scanner.log` - System operations
- `attendance_scanner.log` - Face detection events
- `scan_data_YYYYMMDD_HHMMSS.json` - Session data

### Database Tables
```sql
-- Session tracking
attendance_sessions (id, session_start, session_end, total_faces_detected, scan_positions, status)

-- Face detection records  
face_detections (id, session_id, detection_time, pan_position, tilt_position, face_count, confidence)
```

## 🛠️ **Troubleshooting**

### Common Issues

**Arduino not responding:**
```bash
# Check connection
ls /dev/ttyUSB*
# or
ls /dev/ttyACM*

# Test with test script
python3 test_scanner.py /dev/ttyUSB0
```

**Motors not moving:**
- Check wiring connections
- Verify power supply (12V, 2A+)
- Test with multimeter
- Check driver enable pins

**Face detection errors:**
```bash
# Install missing dependencies
pip install onnxruntime
pip install opencv-python

# Check camera access
ls /dev/video*
```

**Permission errors:**
```bash
# Add user to dialout group
sudo usermod -a -G dialout $USER
# Logout and login again
```

### Performance Optimization

**Scanning Speed:**
- Reduce `STEP_DELAY` for faster movement
- Adjust `SCAN_PAUSE` for detection time
- Optimize `PAN_STEP_SIZE` and `TILT_STEP_SIZE`

**Detection Accuracy:**
- Increase camera resolution
- Improve lighting conditions
- Adjust detection thresholds
- Use higher quality camera

## 📋 **Usage Examples**

### 1. Basic Arduino Test
```python
from scanner_controller import SpaceScanner

scanner = SpaceScanner('/dev/ttyUSB0')
if scanner.connect():
    scanner.start_scanning()
    # Monitor progress
    status = scanner.get_status()
    print(status)
```

### 2. Manual Control
```python
scanner = SpaceScanner()
scanner.connect()
scanner.go_home()           # Center position
scanner.start_scanning()    # Begin systematic scan
scanner.pause_scanning()    # Pause
scanner.resume_scanning()   # Resume  
scanner.stop_scanning()     # Stop and return home
```

### 3. Integrated Attendance
```python
from integrated_attendance_scanner import AttendanceScanner

scanner = AttendanceScanner(camera_id=0)
scanner.initialize_systems()
scanner.start_attendance_session()
# System runs automatically
# Press Ctrl+C to stop
```

## 🎯 **Professional Features**

### Movement Quality
- **Smooth acceleration/deceleration**
- **Precise positioning** (±1 step accuracy)
- **Vibration-free operation**
- **Professional timing patterns**

### System Reliability
- **Comprehensive error handling**
- **Automatic recovery** from failures
- **Position validation** and correction
- **Professional logging** and monitoring

### Integration Ready
- **Modular design** for easy integration
- **Standard interfaces** (Serial, USB)
- **Professional documentation**
- **Extensive configuration options**

## 📞 **Support**

For technical support or questions:
- Check the troubleshooting section
- Review log files for error details
- Test individual components separately
- Verify hardware connections

---

**System Status**: ✅ Production Ready
**Version**: 1.0
**Last Updated**: July 2025
