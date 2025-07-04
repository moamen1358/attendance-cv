import torch
import cv2
import numpy as np
from ultralytics import YOLO
from typing import List, Tuple
import argparse
import sys
import json

def detect_face_positions(image_path: str, confidence_threshold: float = 0.5) -> List[Tuple[int, int, int, int, float]]:
    """
    Detect faces in an image and return their positions.
    
    Args:
        image_path (str): Path to the input image
        confidence_threshold (float): Minimum confidence threshold for face detection
    
    Returns:
        List[Tuple[int, int, int, int, float]]: List of tuples containing (x1, y1, x2, y2, confidence)
    """
    # Check for GPU availability and set device
    import torch
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"🔧 YOLO using device: {device}")
    
    if torch.cuda.is_available():
        print(f"🚀 GPU detected: {torch.cuda.get_device_name(0)}")
        print(f"🚀 GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
    
    # Load the YOLO model
    model = YOLO("/home/invisa/Desktop/my_grad_streamlit_last /models/yolov11l-face.pt")
    
    # Explicitly move model to GPU if available
    if device == "cuda":
        model.model.to('cuda')
        print(f"🚀 YOLO model moved to GPU")
        # Verify the model is on GPU
        print(f"✅ Model device: {next(model.model.parameters()).device}")
    else:
        print(f"⚠️ YOLO using CPU - GPU not available")
    
    # Read the image
    img = cv2.imread(image_path)
    face_positions = []
    
    if img is None:
        print(f"Error: Could not read the image from {image_path}")
        return face_positions
    
    # Perform face detection
    results = model(img)
    
    # Process results
    for result in results:
        boxes = result.boxes
        if boxes is not None:
            for box in boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                confidence = float(box.conf[0])
                
                # Only include faces above confidence threshold
                if confidence >= confidence_threshold:
                    face_positions.append((x1, y1, x2, y2, confidence))
                    print(f"Detected face: ({x1}, {y1}, {x2}, {y2}) confidence: {confidence:.2f}")
    
    return face_positions

def save_annotated_image(image_path: str, face_positions: List[Tuple[int, int, int, int, float]], output_path: str = None) -> str:
    """
    Save an image with detected faces annotated.
    
    Args:
        image_path (str): Path to the input image
        face_positions (List): List of face positions from detect_face_positions()
        output_path (str): Path for output image (optional)
    
    Returns:
        str: Path to the saved annotated image
    """
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error: Could not read the image from {image_path}")
        return ""
    
    # Draw rectangles around detected faces
    for i, (x1, y1, x2, y2, confidence) in enumerate(face_positions):
        # Draw rectangle
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        # Add confidence text
        cv2.putText(img, f"{confidence:.2f}", (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    
    # Save the annotated image
    if output_path is None:
        output_path = f'face_detection_result_{len(face_positions)}_faces.jpg'
    
    cv2.imwrite(output_path, img)
    print(f"Annotated image saved to {output_path}")
    return output_path

# Main execution
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='YOLO Face Detection')
    parser.add_argument('image_path', nargs='?', default='/home/invisa/Desktop/my_grad_streamlit_last /images/2.png',
                       help='Path to the input image')
    parser.add_argument('--confidence', type=float, default=0.3,
                       help='Confidence threshold for face detection (default: 0.3)')
    parser.add_argument('--output', help='Output path for annotated image')
    parser.add_argument('--json-output', help='Save face positions as JSON to this file')
    
    args = parser.parse_args()
    
    print("🎯 Detecting face positions...")
    face_positions = detect_face_positions(args.image_path, confidence_threshold=args.confidence)
    
    print(f"\n📊 Results:")
    print(f"Total faces detected: {len(face_positions)}")
    
    if face_positions:
        print(f"\n📋 Face positions list:")
        for i, (x1, y1, x2, y2, conf) in enumerate(face_positions, 1):
            width = x2 - x1
            height = y2 - y1
            center_x = x1 + width // 2
            center_y = y1 + height // 2
            print(f"Face {i}: Position({x1}, {y1}, {x2}, {y2}) Center({center_x}, {center_y}) Size({width}x{height}) Conf({conf:.2f})")
        
        # Save annotated image
        output_path = args.output if args.output else f'face_detection_result_{len(face_positions)}_faces.jpg'
        annotated_path = save_annotated_image(args.image_path, face_positions, output_path)
        print(f"\n✅ Processing complete! Check {annotated_path}")
        
        # Save JSON output if requested
        if args.json_output:
            face_data = {
                'total_faces': len(face_positions),
                'faces': [
                    {
                        'id': i,
                        'bbox': [x1, y1, x2, y2],
                        'center': [x1 + (x2-x1)//2, y1 + (y2-y1)//2],
                        'confidence': conf
                    }
                    for i, (x1, y1, x2, y2, conf) in enumerate(face_positions, 1)
                ]
            }
            with open(args.json_output, 'w') as f:
                json.dump(face_data, f, indent=2)
            print(f"📄 Face data saved to {args.json_output}")
    else:
        print("❌ No faces detected!")
    
    # Return appropriate exit code
    sys.exit(0 if face_positions else 1)