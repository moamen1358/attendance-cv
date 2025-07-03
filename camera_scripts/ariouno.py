/*
Enhanced Arduino Camera Control for Face Tracking - PAN ONLY
Receives face coordinates and moves camera left/right to track faces
TILT MOVEMENT DISABLED - Only horizontal tracking
Compatible with smart_camera_tracker.py
*/

#define STEP_PIN1 2
#define DIR_PIN1 3
// Motor 2 pins disabled - no tilt movement
// #define STEP_PIN2 4
// #define DIR_PIN2 5

// Camera positioning parameters
int currentX = 683;  // Start at image center (1366/2)
// int currentY = 384;  // Y disabled - no tilt movement

// Motor configuration
const int stepsPerPixel = 1;     // Steps per pixel movement
const int maxStepDelay = 800;    // Microseconds between steps
const int minStepDelay = 400;    // Minimum delay for smooth movement

// Image dimensions (should match camera resolution)
const int imageWidth = 1366;   // Actual image width from your test
const int imageHeight = 768;   // Actual image height from your test

void setup() {
  // Initialize motor pins - ONLY MOTOR 1 (PAN)
  pinMode(STEP_PIN1, OUTPUT);
  pinMode(DIR_PIN1, OUTPUT);
  // Motor 2 pins disabled
  // pinMode(STEP_PIN2, OUTPUT);
  // pinMode(DIR_PIN2, OUTPUT);
  
  // Initialize serial communication
  Serial.begin(9600);
  Serial.println("Arduino Camera Tracker Ready - PAN ONLY MODE");
  Serial.println("Tilt movement DISABLED - Only left/right tracking");
  Serial.println("Waiting for face coordinates...");
  
  // Set initial position to center
  currentX = imageWidth / 2;
  // currentY = imageHeight / 2;  // Y disabled
}

void loop() {
  if (Serial.available() > 0) {
    String serialInput = Serial.readStringUntil('\n');
    serialInput.trim();
    
    if (serialInput.length() > 0) {
      Serial.println("Received: " + serialInput);
      processFaceCoordinates(serialInput);
    }
  }
}

void processFaceCoordinates(String input) {
  // Parse input: "centerX centerY width height"
  int spaceCount = 0;
  for (int i = 0; i < input.length(); i++) {
    if (input.charAt(i) == ' ') spaceCount++;
  }
  
  if (spaceCount < 1) {
    Serial.println("Error: Invalid input format");
    return;
  }
  
  // Extract coordinates
  int centerX = getValue(input, ' ', 0);
  int centerY = getValue(input, ' ', 1);
  int faceWidth = getValue(input, ' ', 2);
  int faceHeight = getValue(input, ' ', 3);
  
  Serial.println("Face detected at X: " + String(centerX) + " (Y ignored: " + String(centerY) + ")");
  Serial.println("Face size: " + String(faceWidth) + "x" + String(faceHeight) + " (width used for tracking)");
  
  // Move camera to track the face - ONLY HORIZONTAL
  moveToFacePosition(centerX, 0);  // Y parameter ignored
}

int getValue(String data, char separator, int index) {
  int found = 0;
  int strIndex[] = {0, -1};
  int maxIndex = data.length() - 1;

  for (int i = 0; i <= maxIndex && found <= index; i++) {
    if (data.charAt(i) == separator || i == maxIndex) {
      if (found == index - 1) strIndex[0] = strIndex[1] + 1;
      if (found == index) strIndex[1] = (i == maxIndex) ? i+1 : i;
      found++;
    }
  }
  
  if (found > index) {
    return data.substring(strIndex[0], strIndex[1]).toInt();
  }
  return 0;
}

void moveToFacePosition(int targetX, int targetY) {
  Serial.println("Moving from X:" + String(currentX) + 
                " to X:" + String(targetX) + " (Y movement DISABLED)");
  
  // Calculate movement needed - ONLY HORIZONTAL
  int deltaX = targetX - currentX;
  // int deltaY = targetY - currentY;  // Y disabled
  
  // Convert to steps - ONLY X AXIS
  int stepsX = abs(deltaX) * stepsPerPixel;
  // int stepsY = abs(deltaY) * stepsPerPixel;  // Y disabled
  
  // Set motor direction - ONLY MOTOR 1 (PAN)
  digitalWrite(DIR_PIN1, deltaX >= 0 ? HIGH : LOW);
  // Motor 2 direction disabled
  // digitalWrite(DIR_PIN2, deltaY >= 0 ? LOW : HIGH);
  
  Serial.println("Steps needed - X: " + String(stepsX) + " (Y: DISABLED)");
  
  // Perform smooth movement - ONLY HORIZONTAL
  smoothMoveHorizontal(stepsX);
  
  // Update current position - ONLY X
  currentX = targetX;
  // currentY = targetY;  // Y disabled
  
  Serial.println("Movement completed. New position X: " + String(currentX) + " (Y: DISABLED)");
}

void smoothMoveHorizontal(int stepsX) {
  // Smooth horizontal movement only
  for (int i = 0; i < stepsX; i++) {
    // Pulse motor 1 (horizontal)
    digitalWrite(STEP_PIN1, HIGH);
    
    // Calculate dynamic delay for smooth acceleration/deceleration
    int stepDelay = calculateStepDelay(i, stepsX);
    delayMicroseconds(stepDelay);
    
    digitalWrite(STEP_PIN1, LOW);
    delayMicroseconds(stepDelay);
  }
}

int calculateStepDelay(int currentStep, int totalSteps) {
  // Create smooth acceleration/deceleration curve
  float progress = (float)currentStep / totalSteps;
  float speedMultiplier;
  
  if (progress < 0.3) {
    // Acceleration phase
    speedMultiplier = progress / 0.3;
  } else if (progress > 0.7) {
    // Deceleration phase
    speedMultiplier = (1.0 - progress) / 0.3;
  } else {
    // Constant speed phase
    speedMultiplier = 1.0;
  }
  
  speedMultiplier = max(speedMultiplier, 0.3); // Minimum speed
  
  int delay = maxStepDelay - (int)((maxStepDelay - minStepDelay) * speedMultiplier);
  return delay;
}

void centerCamera() {
  // Move camera to center position - ONLY HORIZONTAL
  Serial.println("Centering camera horizontally...");
  moveToFacePosition(imageWidth / 2, 0);  // Y value ignored
}

void emergencyStop() {
  // Stop all motor movement immediately - ONLY MOTOR 1
  digitalWrite(STEP_PIN1, LOW);
  // digitalWrite(STEP_PIN2, LOW);  // Motor 2 disabled
  Serial.println("Emergency stop activated - horizontal movement stopped");
}