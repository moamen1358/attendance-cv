# # import torch
# # import cv2
# # import numpy as np
# # import serial
# # import time
# # import logging
# # from ultralytics import YOLO

# # # Configure logging
# # logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# # # Initialize serial communication with Arduino
# # def initialize_serial(port='/dev/ttyUSB0', baudrate=9600):
# #     try:
# #         ser = serial.Serial(port, baudrate)
# #         logging.info(f"Serial connection established on {port} at {baudrate} baud.")
# #         return ser
# #     except serial.SerialException as e:
# #         logging.error(f"Failed to establish serial connection: {e}")
# #         return None

# # # Calculate target angles for the servo motor
# # def calculate_target_angles(face_position, image_width, image_height):
# #     x1, y1, x2, y2 = face_position
# #     center_x = (x1 + x2) // 2
# #     center_y = (x1 + x2) // 2

# #     pan_angle = (center_x / image_width) * 180  # Assuming 180 degrees range for pan
# #     tilt_angle = (center_y / image_height) * 180  # Assuming 180 degrees range for tilt

# #     logging.info(f"Calculated angles - Pan: {pan_angle}, Tilt: {tilt_angle}")
# #     return pan_angle, tilt_angle

# # # Send angles to the servo motor
# # def send_angles_to_servo(ser, pan_angle, tilt_angle):
# #     if pan_angle is not None and tilt_angle is not None:
# #         command = f"{int(pan_angle)},{int(tilt_angle)}\n"
# #         ser.write(command.encode())
# #         logging.info(f"Sent command to servo: {command}")

# # # Load the YOLO model
# # def load_yolo_model(model_path):
# #     try:
# #         model = YOLO(model_path)
# #         logging.info(f"YOLO model loaded from {model_path}")
# #         return model
# #     except Exception as e:
# #         logging.error(f"Failed to load YOLO model: {e}")
# #         return None

# # # Detect faces in the image
# # def detect_faces(model, img):
# #     try:
# #         results = model(img)
# #         face_positions = []
# #         for result in results:
# #             boxes = result.boxes
# #             for box in boxes:
# #                 x1, y1, x2, y2 = map(int, box.xyxy[0])
# #                 confidence = box.conf[0]
# #                 if confidence > 0.5:
# #                     face_positions.append((x1, y1, x2, y2))
# #                     # Draw the bounding box
# #                     cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
# #                     # Draw a red point at the center of the bounding box
# #                     center_x = (x1 + x2) // 2
# #                     center_y = (y1 + y2) // 2
# #                     cv2.circle(img, (center_x, center_y), 3, (0, 0, 255), -1)
# #         logging.info(f"Detected {len(face_positions)} faces.")
# #         return face_positions, img
# #     except Exception as e:
# #         logging.error(f"Failed to detect faces: {e}")
# #         return [], img

# # # Main function
# # def main():
# #     # Initialize serial communication
# #     ser = initialize_serial()
# #     if ser is None:
# #         return

# #     # Load the YOLO model
# #     model_path = "/home/invisa/Desktop/grad_v2/yolov11l-face.pt"
# #     model = load_yolo_model(model_path)
# #     if model is None:
# #         return

# #     # Read the image
# #     image_path = '/home/invisa/Desktop/my_grad_streamlit/testttttttt/2.png'
# #     img = cv2.imread(image_path)
# #     if img is None:
# #         logging.error(f"Error: Could not read the image from {image_path}")
# #         return

# #     # Detect faces
# #     face_positions, img_with_boxes = detect_faces(model, img)

# #     # Save and display the result
# #     output_image_path = 'yolov5_face_wide.jpg'
# #     cv2.imwrite(output_image_path, img_with_boxes)
# #     logging.info(f"Image with detected faces saved to {output_image_path}")

# #     # Move the camera to each face one by one
# #     image_width = img.shape[1]
# #     image_height = img.shape[0]

# #     for face_position in face_positions:
# #         pan_angle, tilt_angle = calculate_target_angles(face_position, image_width, image_height)
# #         send_angles_to_servo(ser, pan_angle, tilt_angle)
# #         time.sleep(2)  # Wait for 2 seconds to allow the camera to move and stabilize

# #     # Close the serial connection
# #     ser.close()
# #     logging.info("Serial connection closed.")

# # if __name__ == "__main__":
# #     main()

# # #include <Servo.h>

# # # // Define the servo objects
# # # Servo panServo;
# # # Servo tiltServo;

# # # // Define the pins for the servos
# # # const int panServoPin = 9;
# # # const int tiltServoPin = 10;

# # # void setup() {
# # #   // Initialize serial communication
# # #   Serial.begin(9600);

# # #   // Attach the servos to the specified pins
# # #   panServo.attach(panServoPin);
# # #   tiltServo.attach(tiltServoPin);

# # #   // Initialize the servos to the center position
# # #   panServo.write(90);
# # #   tiltServo.write(90);
# # # }

# # # void loop() {
# # #   // Check if data is available on the serial port
# # #   if (Serial.available() > 0) {
# # #     // Read the incoming command
# # #     String command = Serial.readStringUntil('\n');

# # #     // Find the comma separating the pan and tilt angles
# # #     int commaIndex = command.indexOf(',');

# # #     // If a comma is found, parse the angles
# # #     if (commaIndex > 0) {
# # #       // Extract the pan and tilt angles from the command
# # #       int panAngle = command.substring(0, commaIndex).toInt();
# # #       int tiltAngle = command.substring(commaIndex + 1).toInt();

# # #       // Move the servos to the specified angles
# # #       panServo.write(panAngle);
# # #       tiltServo.write(tiltAngle);

# # #       // Print the angles to the serial monitor for debugging
# # #       Serial.print("Pan angle: ");
# # #       Serial.print(panAngle);
# # #       Serial.print(", Tilt angle: ");
# # #       Serial.println(tiltAngle);
# # #     }
# # #   }
# # # }



# # # import torch
# # # import cv2
# # # import numpy as np
# # # import serial
# # # import time
# # # import logging
# # # from ultralytics import YOLO

# # # # Configure logging
# # # logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# # # # Initialize serial communication with Arduino
# # # def initialize_serial(port='/dev/ttyUSB0', baudrate=9600):
# # #     try:
# # #         ser = serial.Serial(port, baudrate)
# # #         logging.info(f"Serial connection established on {port} at {baudrate} baud.")
# # #         return ser
# # #     except serial.SerialException as e:
# # #         logging.error(f"Failed to establish serial connection: {e}")
# # #         return None

# # # # Calculate target angles for the servo motor
# # # def calculate_target_angles(face_position, image_width, image_height):
# # #     x1, y1, x2, y2 = face_position
# # #     center_x = (x1 + x2) // 2
# # #     center_y = (y1 + y2) // 2

# # #     pan_angle = (center_x / image_width) * 180  # Assuming 180 degrees range for pan
# # #     tilt_angle = (center_y / image_height) * 180  # Assuming 180 degrees range for tilt

# # #     logging.info(f"Calculated angles - Pan: {pan_angle}, Tilt: {tilt_angle}")
# # #     return pan_angle, tilt_angle

# # # # Send angles to the servo motor
# # # def send_angles_to_servo(ser, pan_angle, tilt_angle):
# # #     if pan_angle is not None and tilt_angle is not None:
# # #         command = f"{int(pan_angle)},{int(tilt_angle)}\n"
# # #         ser.write(command.encode())
# # #         logging.info(f"Sent command to servo: {command}")

# # # # Load the YOLO model
# # # def load_yolo_model(model_path):
# # #     try:
# # #         model = YOLO(model_path)
# # #         logging.info(f"YOLO model loaded from {model_path}")
# # #         return model
# # #     except Exception as e:
# # #         logging.error(f"Failed to load YOLO model: {e}")
# # #         return None

# # # # Detect faces in the image
# # # def detect_faces(model, img):
# # #     try:
# # #         results = model(img)
# # #         face_positions = []
# # #         for result in results:
# # #             boxes = result.boxes
# # #             for box in boxes:
# # #                 x1, y1, x2, y2 = map(int, box.xyxy[0])
# # #                 confidence = box.conf[0]
# # #                 if confidence > 0.5:
# # #                     face_positions.append((x1, y1, x2, y2))
# # #                     # Draw the bounding box
# # #                     cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
# # #                     # Draw a red point at the center of the bounding box
# # #                     center_x = (x1 + x2) // 2
# # #                     center_y = (y1 + y2) // 2
# # #                     cv2.circle(img, (center_x, center_y), 3, (0, 0, 255), -1)
# # #         logging.info(f"Detected {len(face_positions)} faces.")
# # #         return face_positions, img
# # #     except Exception as e:
# # #         logging.error(f"Failed to detect faces: {e}")
# # #         return [], img

# # # # Main function
# # # def main():
# # #     # Initialize serial communication
# # #     ser = initialize_serial()
# # #     if ser is None:
# # #         return

# # #     # Load the YOLO model
# # #     model_path = "/home/invisa/Desktop/grad_v2/yolov11l-face.pt"
# # #     model = load_yolo_model(model_path)
# # #     if model is None:
# # #         return

# # #     # Define the total number of students
# # #     total_students = 30  # Update this value as necessary
# # #     detected_students = 0

# # #     # Flag to indicate whether to continue taking attendance
# # #     continue_attendance = True

# # #     while continue_attendance:
# # #         # Read the image
# # #         image_path = '/home/invisa/Desktop/my_grad_streamlit/testttttttt/2.png'
# # #         img = cv2.imread(image_path)
# # #         if img is None:
# # #             logging.error(f"Error: Could not read the image from {image_path}")
# # #             return

# # #         # Detect faces
# # #         face_positions, img_with_boxes = detect_faces(model, img)

# # #         # Update the count of detected students
# # #         detected_students += len(face_positions)

# # #         # Save and display the result
# # #         output_image_path = f'yolov5_face_wide_{detected_students}.jpg'
# # #         cv2.imwrite(output_image_path, img_with_boxes)
# # #         logging.info(f"Image with detected faces saved to {output_image_path}")

# # #         # Move the camera to each face one by one
# # #         image_width = img.shape[1]
# # #         image_height = img.shape[0]

# # #         for face_position in face_positions:
# # #             pan_angle, tilt_angle = calculate_target_angles(face_position, image_width, image_height)
# # #             send_angles_to_servo(ser, pan_angle, tilt_angle)
# # #             time.sleep(2)  # Wait for 2 seconds to allow the camera to move and stabilize

# # #         # Check if all student_profiles have been detected
# # #         if detected_students >= total_students:
# # #             continue_attendance = False
# # #             logging.info("All student_profiles have been detected. Stopping attendance process.")

# # #     # Close the serial connection
# # #     ser.close()
# # #     logging.info("Serial connection closed.")

# # # if __name__ == "__main__":
# # #     main()

# import torch
# import cv2
# import numpy as np
# import serial
# import time
# import logging
# from ultralytics import YOLO

# # Configure logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# # Default position for the servos
# DEFAULT_PAN_ANGLE = 90
# DEFAULT_TILT_ANGLE = 90

# # Safe range for the servos
# MIN_ANGLE = 0
# MAX_PAN_ANGLE = 130
# MAX_TILT_ANGLE = 180

# # Step size for smooth transitions
# STEP_SIZE = 5
# STEP_DELAY = 0.05  # Delay in seconds between steps

# # Initialize serial communication with Arduino
# def initialize_serial(port='/dev/ttyACM0', baudrate=9600):
#     try:
#         ser = serial.Serial(port, baudrate)
#         logging.info(f"Serial connection established on {port} at {baudrate} baud.")
#         return ser
#     except serial.SerialException as e:
#         logging.error(f"Failed to establish serial connection: {e}")
#         return None

# # Send angles to the servo motor
# def send_angles_to_servo(ser, pan_angle, tilt_angle):
#     if pan_angle is not None and tilt_angle is not None:
#         command = f"{int(pan_angle)},{int(tilt_angle)}\n"
#         ser.write(command.encode())
#         logging.info(f"Sent command to servo: {command}")

# # Move servos smoothly to the target position
# def move_servos_smoothly(ser, current_pan, current_tilt, target_pan, target_tilt):
#     current_pan = int(current_pan)
#     current_tilt = int(current_tilt)
#     target_pan = int(target_pan)
#     target_tilt = int(target_tilt)

#     # Apply pan and tilt limits
#     if target_pan > MAX_PAN_ANGLE:
#         target_pan = MAX_PAN_ANGLE
#     if target_tilt > MAX_TILT_ANGLE:
#         target_tilt = MAX_TILT_ANGLE

#     pan_steps = range(current_pan, target_pan, STEP_SIZE if target_pan > current_pan else -STEP_SIZE)
#     tilt_steps = range(current_tilt, target_tilt, STEP_SIZE if target_tilt > current_tilt else -STEP_SIZE)

#     for pan_angle, tilt_angle in zip(pan_steps, tilt_steps):
#         send_angles_to_servo(ser, pan_angle, tilt_angle)
#         time.sleep(STEP_DELAY)

#     # Ensure final position is reached
#     send_angles_to_servo(ser, target_pan, target_tilt)

# # Calculate target angles for the servo motor
# def calculate_target_angles(face_position, image_width, image_height):
#     x1, y1, x2, y2 = face_position
#     center_x = (x1 + x2) // 2
#     center_y = (y1 + y2) // 2

#     pan_angle = (center_x / image_width) * MAX_PAN_ANGLE  # Assuming 130 degrees range for pan
#     tilt_angle = (center_y / image_height) * MAX_TILT_ANGLE  # Assuming 180 degrees range for tilt

#     logging.info(f"Calculated angles - Pan: {pan_angle}, Tilt: {tilt_angle}")
#     return pan_angle, tilt_angle

# # Load the YOLO model
# def load_yolo_model(model_path):
#     try:
#         model = YOLO(model_path)
#         logging.info(f"YOLO model loaded from {model_path}")
#         return model
#     except Exception as e:
#         logging.error(f"Failed to load YOLO model: {e}")
#         return None

# # Detect faces in the image
# def detect_faces(model, img):
#     try:
#         results = model(img)
#         face_positions = []
#         for result in results:
#             boxes = result.boxes
#             for box in boxes:
#                 x1, y1, x2, y2 = map(int, box.xyxy[0])
#                 confidence = box.conf[0]
#                 if confidence > 0.5:
#                     face_positions.append((x1, y1, x2, y2))
#                     # Draw the bounding box
#                     cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
#                     # Draw a red point at the center of the bounding box
#                     center_x = (x1 + x2) // 2
#                     center_y = (y1 + y2) // 2
#                     cv2.circle(img, (center_x, center_y), 3, (0, 0, 255), -1)
#         logging.info(f"Detected {len(face_positions)} faces.")
#         return face_positions, img
#     except Exception as e:
#         logging.error(f"Failed to detect faces: {e}")
#         return [], img

# # Sort face positions to move in a row, student by student
# def sort_face_positions(face_positions):
#     # Sort by y coordinate (top to bottom), then by x coordinate (left to right)
#     return sorted(face_positions, key=lambda pos: (pos[1], pos[0]))

# # Main function
# def main():
#     # Initialize serial communication
#     ser = initialize_serial()
#     if ser is None:
#         return

#     # Load the YOLO model
#     model_path = "/home/invisa/Desktop/grad_v2/yolov11l-face.pt"
#     model = load_yolo_model(model_path)
#     if model is None:
#         return

#     # Define the total number of students
#     total_students = 30  # Update this value as necessary
#     detected_students = 0

#     # Move to the default position smoothly
#     current_pan_angle = DEFAULT_PAN_ANGLE
#     current_tilt_angle = DEFAULT_TILT_ANGLE
#     move_servos_smoothly(ser, current_pan_angle, current_tilt_angle, DEFAULT_PAN_ANGLE, DEFAULT_TILT_ANGLE)
#     logging.info(f"Moved to default position: Pan: {DEFAULT_PAN_ANGLE}, Tilt: {DEFAULT_TILT_ANGLE}")

#     # Flag to indicate whether to continue taking attendance
#     continue_attendance = True

#     while continue_attendance:
#         # Read the image
#         image_path = '/home/invisa/Desktop/my_grad_streamlit/testttttttt/2.png'
#         img = cv2.imread(image_path)
#         if img is None:
#             logging.error(f"Error: Could not read the image from {image_path}")
#             return

#         # Detect faces
#         face_positions, img_with_boxes = detect_faces(model, img)

#         # Sort face positions to move in a row, student by student
#         face_positions = sort_face_positions(face_positions)

#         # Update the count of detected students
#         detected_students += len(face_positions)

#         # Save and display the result
#         output_image_path = f'yolov5_face_wide_{detected_students}.jpg'
#         cv2.imwrite(output_image_path, img_with_boxes)
#         logging.info(f"Image with detected faces saved to {output_image_path}")

#         # Move the camera to each face one by one
#         image_width = img.shape[1]
#         image_height = img.shape[0]

#         for face_position in face_positions:
#             pan_angle, tilt_angle = calculate_target_angles(face_position, image_width, image_height)
#             move_servos_smoothly(ser, current_pan_angle, current_tilt_angle, int(pan_angle), int(tilt_angle))
#             current_pan_angle, current_tilt_angle = int(pan_angle), int(tilt_angle)  # Update current position
#             time.sleep(2)  # Wait for 2 seconds to allow the camera to move and stabilize

#         # Check if all student_profiles have been detected
#         if detected_students >= total_students:
#             continue_attendance = False
#             logging.info("All student_profiles have been detected. Stopping attendance process.")

#     # Close the serial connection
#     ser.close()
#     logging.info("Serial connection closed.")

# if __name__ == "__main__":
#     main()

import torch
import cv2
import numpy as np
import serial
import time
import logging
from ultralytics import YOLO

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Default position for the servos
DEFAULT_PAN_ANGLE = 90
DEFAULT_TILT_ANGLE = 90

# Safe range for the servos
MIN_ANGLE = 0
MAX_PAN_ANGLE = 130
MAX_TILT_ANGLE = 180

# Step size for smooth transitions
STEP_SIZE = 5
STEP_DELAY = 0.05  # Delay in seconds between steps

def initialize_serial(port='/dev/ttyACM0', baudrate=9600):
    try:
        ser = serial.Serial(port, baudrate)
        logging.info(f"Serial connection established on {port} at {baudrate} baud.")
        return ser
    except serial.SerialException as e:
        logging.error(f"Failed to establish serial connection: {e}")
        return None

def send_angles_to_servo(ser, pan_angle, tilt_angle):
    if pan_angle is not None and tilt_angle is not None:
        command = f"{int(pan_angle)},{int(tilt_angle)}\n"
        ser.write(command.encode())
        logging.info(f"Sent command to servo: {command}")

def move_servos_smoothly(ser, current_pan, current_tilt, target_pan, target_tilt):
    current_pan = int(current_pan)
    current_tilt = int(current_tilt)
    target_pan = int(target_pan)
    target_tilt = int(target_tilt)

    # Apply pan and tilt limits
    target_pan = max(MIN_ANGLE, min(target_pan, MAX_PAN_ANGLE))
    target_tilt = max(MIN_ANGLE, min(target_tilt, MAX_TILT_ANGLE))

    while current_pan != target_pan or current_tilt != target_tilt:
        # Calculate next step for pan
        if current_pan < target_pan:
            new_pan = min(current_pan + STEP_SIZE, target_pan)
        elif current_pan > target_pan:
            new_pan = max(current_pan - STEP_SIZE, target_pan)
        else:
            new_pan = current_pan

        # Calculate next step for tilt
        if current_tilt < target_tilt:
            new_tilt = min(current_tilt + STEP_SIZE, target_tilt)
        elif current_tilt > target_tilt:
            new_tilt = max(current_tilt - STEP_SIZE, target_tilt)
        else:
            new_tilt = current_tilt

        # Send the new angles
        send_angles_to_servo(ser, new_pan, new_tilt)
        time.sleep(STEP_DELAY)

        # Update current angles
        current_pan = new_pan
        current_tilt = new_tilt

    # Ensure final position is exactly the target
    send_angles_to_servo(ser, target_pan, target_tilt)

def calculate_target_angles(face_position, image_width, image_height):
    x1, y1, x2, y2 = face_position
    center_x = (x1 + x2) // 2
    center_y = (y1 + y2) // 2

    pan_angle = (center_x / image_width) * MAX_PAN_ANGLE
    tilt_angle = (center_y / image_height) * MAX_TILT_ANGLE

    logging.info(f"Calculated angles - Pan: {pan_angle}, Tilt: {tilt_angle}")
    return pan_angle, tilt_angle

def load_yolo_model(model_path):
    try:
        model = YOLO(model_path)
        logging.info(f"YOLO model loaded from {model_path}")
        return model
    except Exception as e:
        logging.error(f"Failed to load YOLO model: {e}")
        return None

def detect_faces(model, img):
    try:
        results = model(img)
        face_positions = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                confidence = box.conf[0]
                if confidence > 0.5:
                    face_positions.append((x1, y1, x2, y2))
                    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    center_x = (x1 + x2) // 2
                    center_y = (y1 + y2) // 2
                    cv2.circle(img, (center_x, center_y), 3, (0, 0, 255), -1)
        logging.info(f"Detected {len(face_positions)} faces.")
        return face_positions, img
    except Exception as e:
        logging.error(f"Failed to detect faces: {e}")
        return [], img

def sort_face_positions(face_positions):
    return sorted(face_positions, key=lambda pos: (pos[1], pos[0]))

def main():
    ser = initialize_serial()
    if ser is None:
        return

    model_path = "/home/invisa/Desktop/grad_v2/yolov11l-face.pt"
    model = load_yolo_model(model_path)
    if model is None:
        return

    total_students = 30
    detected_students = 0

    current_pan_angle = DEFAULT_PAN_ANGLE
    current_tilt_angle = DEFAULT_TILT_ANGLE
    move_servos_smoothly(ser, current_pan_angle, current_tilt_angle, DEFAULT_PAN_ANGLE, DEFAULT_TILT_ANGLE)
    logging.info(f"Moved to default position: Pan: {DEFAULT_PAN_ANGLE}, Tilt: {DEFAULT_TILT_ANGLE}")

    continue_attendance = True

    while continue_attendance:
        image_path = '/home/invisa/Desktop/my_grad_streamlit/testttttttt/2.png'
        img = cv2.imread(image_path)
        if img is None:
            logging.error(f"Error: Could not read the image from {image_path}")
            return

        face_positions, img_with_boxes = detect_faces(model, img)
        face_positions = sort_face_positions(face_positions)
        detected_students += len(face_positions)

        output_image_path = f'yolov5_face_wide_{detected_students}.jpg'
        cv2.imwrite(output_image_path, img_with_boxes)
        logging.info(f"Image with detected faces saved to {output_image_path}")

        image_width = img.shape[1]
        image_height = img.shape[0]

        for face_position in face_positions:
            pan_angle, tilt_angle = calculate_target_angles(face_position, image_width, image_height)
            move_servos_smoothly(ser, current_pan_angle, current_tilt_angle, pan_angle, tilt_angle)
            current_pan_angle, current_tilt_angle = pan_angle, tilt_angle
            time.sleep(2)

        if detected_students >= total_students:
            continue_attendance = False
            logging.info("All student_profiles detected. Stopping attendance process.")

    ser.close()
    logging.info("Serial connection closed.")

if __name__ == "__main__":
    main()