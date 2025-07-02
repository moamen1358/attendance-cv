#!/usr/bin/env python3
import cv2
import sys
import os

# Add the insightface package to path
sys.path.insert(0, '/home/invisa/Desktop/my_grad_streamlit_last /insightface/python-package')

from insightface.app import FaceAnalysis

def main():
    print("Face Detection Comparison Test")
    print("=" * 40)
    
    # Load image
    image_path = "2.png"
    if not os.path.exists(image_path):
        print(f"Error: Image {image_path} not found")
        return
    
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error: Could not read image {image_path}")
        return
    
    print(f"Image loaded: {img.shape[1]}x{img.shape[0]} pixels")
    print()
    
    # Test 1: With YOLO
    print("1. Testing with YOLO detection:")
    try:
        app_yolo = FaceAnalysis(use_yolo=True, yolo_model_path="yolov11l-face.pt")
        app_yolo.prepare(ctx_id=0, det_size=(640, 640), det_thresh=0.5)
        faces_yolo = app_yolo.get(img)
        print(f"   Faces detected with YOLO: {len(faces_yolo)}")
    except Exception as e:
        print(f"   Error with YOLO: {e}")
    
    # Test 2: Without YOLO (default InsightFace)
    print("2. Testing without YOLO (default InsightFace):")
    try:
        app_default = FaceAnalysis(use_yolo=False)
        app_default.prepare(ctx_id=0, det_size=(640, 640), det_thresh=0.5)
        faces_default = app_default.get(img)
        print(f"   Faces detected without YOLO: {len(faces_default)}")
    except Exception as e:
        print(f"   Error without YOLO: {e}")
    
    print("=" * 40)
    print("Test completed!")

if __name__ == "__main__":
    main()
