import torch
import cv2
import numpy as np
from ultralytics import YOLO

# Load the YOLO model
model = YOLO("/home/invisa/Desktop/my_grad_streamlit_last/yolov11l-face.pt")

# Read the image
image_path = '/home/invisa/Desktop/my_grad_streamlit_last/2.png'  # Update this path if necessary
img = cv2.imread(image_path)
count = 0
if img is None:
    print(f"Error: Could not read the image from {image_path}")
else:
    # Perform face detection
    results = model(img)

    # Process results
    for result in results:
        boxes = result.boxes
        for box in boxes:
            count += 1
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            confidence = box.conf[0]
            if confidence > 0.5:
                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)

    # Save and display the result
    output_image_path = f'yolov11_face_count{count}.jpg'
    cv2.imwrite(output_image_path, img)
    print(f"faces_count {count}")
    print(f"Image with detected faces saved to {output_image_path}")