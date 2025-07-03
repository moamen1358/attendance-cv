/*
  Memory-Optimized Face Tracking Arduino Code
  Uses your working pin configuration without enable pins
  Minimal memory usage for Arduino Uno
*/

// Motor pin definitions (matching your working code)
#define PAN_STEP_PIN 2      // Pan motor step (your STEP_PIN1)
#define PAN_DIR_PIN 3       // Pan motor direction (your DIR_PIN1)
#define TILT_STEP_PIN 4     // Tilt motor step (your STEP_PIN2)
#define TILT_DIR_PIN 5      // Tilt motor direction (your DIR_PIN2)

// Motor specifications
const int STEPS_PER_REV = 200;
const int MICROSTEPS = 8;
const int TOTAL_STEPS_PER_REV = STEPS_PER_REV * MICROSTEPS; // 1600

// Movement parameters (matching your working timing)
const int STEP_DELAY = 800;     // Microseconds (same as your code)
const int FACE_DELAY = 2000;    // Time at each face

// Image parameters
const int IMAGE_WIDTH = 1366;
const int IMAGE_HEIGHT = 768;
const int IMAGE_CENTER_X = 683;
const int IMAGE_CENTER_Y = 384;

// Position tracking
int current_pan_steps = 0;
int current_tilt_steps = 0;

// Streaming mode
bool streaming_mode = false;
int total_faces = 0;
int faces_processed = 0;

void setup() {
  Serial.begin(9600);
  
  // Initialize pins (no enable pins needed)
  pinMode(PAN_STEP_PIN, OUTPUT);
  pinMode(PAN_DIR_PIN, OUTPUT);
  pinMode(TILT_STEP_PIN, OUTPUT);
  pinMode(TILT_DIR_PIN, OUTPUT);
  
  // Set initial states
  digitalWrite(PAN_STEP_PIN, LOW);
  digitalWrite(PAN_DIR_PIN, HIGH);
  digitalWrite(TILT_STEP_PIN, LOW);
  digitalWrite(TILT_DIR_PIN, HIGH);
  
  delay(1000);
  
  Serial.println("Face Tracker Ready - Memory Optimized");
  Serial.println("Commands: STREAM <total>, FACE <x1> <y1> <x2> <y2>, MOVE <pan> <tilt>, CENTER, PING");
  Serial.println("READY");
}

void loop() {
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    processCommand(command);
  }
  delay(10);
}

void processCommand(String cmd) {
  cmd.toUpperCase();
  Serial.print("CMD: ");
  Serial.println(cmd);
  
  if (cmd.startsWith("STREAM")) {
    int count = cmd.substring(7).toInt();
    if (count > 0) {
      streaming_mode = true;
      total_faces = count;
      faces_processed = 0;
      Serial.print("STREAMING ");
      Serial.println(count);
    }
  }
  else if (cmd.startsWith("FACE")) {
    if (streaming_mode) {
      processFace(cmd);
    } else {
      Serial.println("ERROR: Use STREAM first");
    }
  }
  else if (cmd.startsWith("MOVE")) {
    processMove(cmd);
  }
  else if (cmd == "CENTER") {
    moveToPosition(0, 0);
    Serial.println("CENTERED");
  }
  else if (cmd == "PING") {
    Serial.println("PONG");
  }
  else {
    Serial.println("ERROR: Unknown");
  }
  
  Serial.println("READY");
}

void processFace(String cmd) {
  // Parse: FACE 1163 138 1183 165
  int values[4];
  int start = 5; // Skip "FACE "
  
  for (int i = 0; i < 4; i++) {
    int space = cmd.indexOf(' ', start);
    if (space == -1 && i < 3) return;
    
    values[i] = cmd.substring(start, (i < 3) ? space : cmd.length()).toInt();
    start = space + 1;
  }
  
  // Calculate center
  int center_x = values[0] + (values[2] - values[0]) / 2;
  int center_y = values[1] + (values[3] - values[1]) / 2;
  
  // Convert to steps
  int pan_steps = pixelToPanSteps(center_x);
  int tilt_steps = pixelToTiltSteps(center_y);
  
  faces_processed++;
  
  Serial.print("FACE ");
  Serial.print(faces_processed);
  Serial.print("/");
  Serial.print(total_faces);
  Serial.print(" -> ");
  Serial.print(pan_steps);
  Serial.print(",");
  Serial.println(tilt_steps);
  
  // Move to position
  moveToPosition(pan_steps, tilt_steps);
  
  // Wait at face
  delay(FACE_DELAY);
  
  // Check if done
  if (faces_processed >= total_faces) {
    Serial.println("COMPLETE");
    moveToPosition(0, 0); // Return to center
    streaming_mode = false;
  }
}

void processMove(String cmd) {
  // Parse: MOVE 100 50
  int first_space = cmd.indexOf(' ');
  int second_space = cmd.indexOf(' ', first_space + 1);
  
  if (first_space != -1 && second_space != -1) {
    int pan = cmd.substring(first_space + 1, second_space).toInt();
    int tilt = cmd.substring(second_space + 1).toInt();
    
    moveToPosition(pan, tilt);
    Serial.println("MOVED");
  }
}

int pixelToPanSteps(int pixel_x) {
  // Convert pixel to pan steps with amplification
  int offset = pixel_x - IMAGE_CENTER_X;
  float angle = (float)offset / IMAGE_WIDTH * 60.0; // 60 degree FOV
  angle *= 2.0; // Amplification factor
  return (int)(angle * 4.44); // 4.44 steps per degree
}

int pixelToTiltSteps(int pixel_y) {
  // Convert pixel to tilt steps with amplification  
  int offset = pixel_y - IMAGE_CENTER_Y;
  float angle = -(float)offset / IMAGE_HEIGHT * 35.0; // 35 degree FOV
  angle *= 2.0; // Amplification factor
  return (int)(angle * 4.44); // 4.44 steps per degree
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
    
    // Small delay every 50 steps
    if (i % 50 == 0 && i > 0) {
      delay(2);
    }
  }
}
