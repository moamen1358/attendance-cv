/*
  Professional Space Scanner Arduino Code
  Systematic grid-based scanning for student attendance
  
  Features:
  - Horizontal left-to-right scanning
  - Vertical step-down after each row
  - Configurable scan density and speed
  - Professional timing and movement patterns
  - Status reporting and monitoring
  
  Hardware Requirements:
  - 2x Stepper Motors (Pan/Tilt)
  - Stepper Motor Drivers (A4988/DRV8825)
  - Arduino Uno/Nano
  
  Author: Professional Scanning System
  Version: 1.0
*/

// Motor pin definitions (matching your working configuration)
#define PAN_STEP_PIN 2      // Pan motor step pin
#define PAN_DIR_PIN 3       // Pan motor direction pin
#define TILT_STEP_PIN 4     // Tilt motor step pin
#define TILT_DIR_PIN 5      // Tilt motor direction pin

// Motor specifications
const int STEPS_PER_REV = 200;      // Steps per revolution
const int MICROSTEPS = 8;           // Microstepping setting
const int TOTAL_STEPS_PER_REV = STEPS_PER_REV * MICROSTEPS; // 1600

// Movement timing parameters
const int STEP_DELAY = 600;         // Microseconds between steps (faster for smooth scanning)
const int SCAN_PAUSE = 1500;       // Pause at each scan position (ms)
const int ROW_TRANSITION_DELAY = 500; // Delay when moving to next row (ms)

// Scanning area parameters (in steps)
const int PAN_RANGE = 400;          // Total horizontal range (±200 steps from center)
const int TILT_RANGE = 200;         // Total vertical range (±100 steps from center)
const int PAN_STEP_SIZE = 50;       // Horizontal step between scan positions
const int TILT_STEP_SIZE = 40;      // Vertical step between rows

// Position tracking
int current_pan_steps = 0;
int current_tilt_steps = 0;

// Scanning state
enum ScanState {
  IDLE,
  SCANNING,
  PAUSED,
  RETURNING_HOME
};

ScanState scan_state = IDLE;
bool scan_direction_right = true;   // Current horizontal scan direction
int current_row = 0;               // Current scanning row
int total_rows = 0;                // Total rows to scan
int scan_positions_per_row = 0;    // Positions per row
int current_position_in_row = 0;   // Current position in current row

// Statistics
unsigned long scan_start_time = 0;
int total_scan_positions = 0;
int completed_positions = 0;

void setup() {
  Serial.begin(9600);
  
  // Initialize motor pins
  pinMode(PAN_STEP_PIN, OUTPUT);
  pinMode(PAN_DIR_PIN, OUTPUT);
  pinMode(TILT_STEP_PIN, OUTPUT);
  pinMode(TILT_DIR_PIN, OUTPUT);
  
  // Set initial pin states
  digitalWrite(PAN_STEP_PIN, LOW);
  digitalWrite(PAN_DIR_PIN, HIGH);
  digitalWrite(TILT_STEP_PIN, LOW);
  digitalWrite(TILT_DIR_PIN, HIGH);
  
  // Calculate scanning parameters
  scan_positions_per_row = (PAN_RANGE / PAN_STEP_SIZE) + 1;
  total_rows = (TILT_RANGE / TILT_STEP_SIZE) + 1;
  total_scan_positions = scan_positions_per_row * total_rows;
  
  delay(1000);
  
  Serial.println("=== Professional Space Scanner v1.0 ===");
  Serial.println("Commands:");
  Serial.println("  START - Begin systematic scanning");
  Serial.println("  PAUSE - Pause current scan");
  Serial.println("  RESUME - Resume paused scan");
  Serial.println("  STOP - Stop scan and return home");
  Serial.println("  HOME - Move to center position");
  Serial.println("  STATUS - Show current status");
  Serial.println("  CONFIG - Show configuration");
  Serial.println();
  
  showConfiguration();
  Serial.println("READY");
}

void loop() {
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    processCommand(command);
  }
  
  // Handle scanning state machine
  if (scan_state == SCANNING) {
    performScanStep();
  }
  
  delay(10);
}

void processCommand(String cmd) {
  cmd.toUpperCase();
  Serial.print(">>> ");
  Serial.println(cmd);
  
  if (cmd == "START") {
    startScanning();
  }
  else if (cmd == "PAUSE") {
    pauseScanning();
  }
  else if (cmd == "RESUME") {
    resumeScanning();
  }
  else if (cmd == "STOP") {
    stopScanning();
  }
  else if (cmd == "HOME") {
    moveToCenter();
  }
  else if (cmd == "STATUS") {
    showStatus();
  }
  else if (cmd == "CONFIG") {
    showConfiguration();
  }
  else if (cmd == "PING") {
    Serial.println("PONG");
  }
  else {
    Serial.println("ERROR: Unknown command");
  }
  
  Serial.println("READY");
}

void startScanning() {
  if (scan_state == SCANNING) {
    Serial.println("ALREADY SCANNING");
    return;
  }
  
  Serial.println("STARTING SYSTEMATIC SCAN");
  Serial.print("Total positions: ");
  Serial.println(total_scan_positions);
  
  // Reset scanning state
  scan_state = SCANNING;
  current_row = 0;
  current_position_in_row = 0;
  completed_positions = 0;
  scan_direction_right = true;
  scan_start_time = millis();
  
  // Move to starting position (top-left)
  moveToScanPosition(-PAN_RANGE/2, -TILT_RANGE/2);
  
  Serial.println("SCAN STARTED");
}

void pauseScanning() {
  if (scan_state == SCANNING) {
    scan_state = PAUSED;
    Serial.println("SCAN PAUSED");
  } else {
    Serial.println("NOT SCANNING");
  }
}

void resumeScanning() {
  if (scan_state == PAUSED) {
    scan_state = SCANNING;
    Serial.println("SCAN RESUMED");
  } else {
    Serial.println("NOT PAUSED");
  }
}

void stopScanning() {
  if (scan_state == SCANNING || scan_state == PAUSED) {
    scan_state = RETURNING_HOME;
    Serial.println("STOPPING SCAN");
    moveToCenter();
    scan_state = IDLE;
    
    unsigned long elapsed = (millis() - scan_start_time) / 1000;
    Serial.print("SCAN COMPLETED - Time: ");
    Serial.print(elapsed);
    Serial.print("s, Positions: ");
    Serial.print(completed_positions);
    Serial.print("/");
    Serial.println(total_scan_positions);
  } else {
    Serial.println("NOT SCANNING");
  }
}

void performScanStep() {
  // Calculate current scan position
  int pan_pos, tilt_pos;
  
  if (scan_direction_right) {
    // Moving left to right
    pan_pos = -PAN_RANGE/2 + (current_position_in_row * PAN_STEP_SIZE);
  } else {
    // Moving right to left
    pan_pos = PAN_RANGE/2 - (current_position_in_row * PAN_STEP_SIZE);
  }
  
  tilt_pos = -TILT_RANGE/2 + (current_row * TILT_STEP_SIZE);
  
  // Move to scan position
  moveToScanPosition(pan_pos, tilt_pos);
  
  // Report position
  Serial.print("SCAN [");
  Serial.print(current_row + 1);
  Serial.print("/");
  Serial.print(total_rows);
  Serial.print("][");
  Serial.print(current_position_in_row + 1);
  Serial.print("/");
  Serial.print(scan_positions_per_row);
  Serial.print("] ");
  Serial.print(completed_positions + 1);
  Serial.print("/");
  Serial.println(total_scan_positions);
  
  // Pause for scanning
  delay(SCAN_PAUSE);
  
  // Update position counters
  completed_positions++;
  current_position_in_row++;
  
  // Check if row is complete
  if (current_position_in_row >= scan_positions_per_row) {
    // Move to next row
    current_row++;
    current_position_in_row = 0;
    scan_direction_right = !scan_direction_right; // Reverse direction for next row
    
    Serial.println("ROW COMPLETE - Moving to next row");
    delay(ROW_TRANSITION_DELAY);
    
    // Check if all rows are complete
    if (current_row >= total_rows) {
      Serial.println("ALL ROWS COMPLETE");
      stopScanning();
      return;
    }
  }
}

void moveToCenter() {
  Serial.println("MOVING TO CENTER");
  moveToPosition(0, 0);
  Serial.println("CENTERED");
}

void moveToScanPosition(int target_pan, int target_tilt) {
  // Smooth movement to scan position
  moveToPosition(target_pan, target_tilt);
}

void moveToPosition(int target_pan, int target_tilt) {
  // Move pan motor
  int pan_move = target_pan - current_pan_steps;
  if (pan_move != 0) {
    digitalWrite(PAN_DIR_PIN, pan_move > 0 ? HIGH : LOW);
    stepMotor(PAN_STEP_PIN, abs(pan_move));
    current_pan_steps = target_pan;
  }
  
  // Move tilt motor
  int tilt_move = target_tilt - current_tilt_steps;
  if (tilt_move != 0) {
    digitalWrite(TILT_DIR_PIN, tilt_move > 0 ? HIGH : LOW);
    stepMotor(TILT_STEP_PIN, abs(tilt_move));
    current_tilt_steps = target_tilt;
  }
}

void stepMotor(int step_pin, int steps) {
  for (int i = 0; i < steps; i++) {
    digitalWrite(step_pin, HIGH);
    delayMicroseconds(STEP_DELAY);
    digitalWrite(step_pin, LOW);
    delayMicroseconds(STEP_DELAY);
    
    // Small delay every 100 steps for smooth operation
    if (i % 100 == 0 && i > 0) {
      delay(1);
    }
  }
}

void showStatus() {
  Serial.println("=== SCANNER STATUS ===");
  Serial.print("State: ");
  switch(scan_state) {
    case IDLE: Serial.println("IDLE"); break;
    case SCANNING: Serial.println("SCANNING"); break;
    case PAUSED: Serial.println("PAUSED"); break;
    case RETURNING_HOME: Serial.println("RETURNING HOME"); break;
  }
  
  Serial.print("Position: Pan=");
  Serial.print(current_pan_steps);
  Serial.print(", Tilt=");
  Serial.println(current_tilt_steps);
  
  if (scan_state == SCANNING || scan_state == PAUSED) {
    Serial.print("Progress: ");
    Serial.print(completed_positions);
    Serial.print("/");
    Serial.print(total_scan_positions);
    Serial.print(" (");
    Serial.print((completed_positions * 100) / total_scan_positions);
    Serial.println("%)");
    
    Serial.print("Current Row: ");
    Serial.print(current_row + 1);
    Serial.print("/");
    Serial.println(total_rows);
    
    unsigned long elapsed = (millis() - scan_start_time) / 1000;
    Serial.print("Elapsed: ");
    Serial.print(elapsed);
    Serial.println("s");
  }
  Serial.println("=====================");
}

void showConfiguration() {
  Serial.println("=== SCANNER CONFIG ===");
  Serial.print("Pan Range: ±");
  Serial.print(PAN_RANGE/2);
  Serial.print(" steps (");
  Serial.print(PAN_RANGE/2 / 4.44, 1);
  Serial.println(" degrees)");
  
  Serial.print("Tilt Range: ±");
  Serial.print(TILT_RANGE/2);
  Serial.print(" steps (");
  Serial.print(TILT_RANGE/2 / 4.44, 1);
  Serial.println(" degrees)");
  
  Serial.print("Scan Grid: ");
  Serial.print(scan_positions_per_row);
  Serial.print(" x ");
  Serial.print(total_rows);
  Serial.print(" = ");
  Serial.print(total_scan_positions);
  Serial.println(" positions");
  
  Serial.print("Step Size: Pan=");
  Serial.print(PAN_STEP_SIZE);
  Serial.print(", Tilt=");
  Serial.println(TILT_STEP_SIZE);
  
  Serial.print("Timing: Scan=");
  Serial.print(SCAN_PAUSE);
  Serial.print("ms, Step=");
  Serial.print(STEP_DELAY);
  Serial.println("μs");
  Serial.println("======================");
}
