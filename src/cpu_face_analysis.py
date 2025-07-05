import cv2
import numpy as np
from pathlib import Path
import sys
import os

# Simple CPU-only face analysis without InsightFace dependencies
class CPUFaceAnalysis:
    def __init__(self, name=None, root='~/.insightface', **kwargs):
        self.models = {}
        print("🖥️  CPU-only Face Analysis initialized")
        print("⚠️  Using OpenCV DNN backend (limited functionality)")
        
        # Load OpenCV's DNN face detector as fallback
        try:
            # Try to use a simple Haar cascade for face detection
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.face_cascade = cv2.CascadeClassifier(cascade_path)
            print("✅ OpenCV Haar Cascade loaded for basic face detection")
        except:
            print("❌ Could not load OpenCV face detector")
            self.face_cascade = None
    
    def get(self, img, max_num=0):
        """Simple face detection using OpenCV"""
        faces = []
        if self.face_cascade is not None:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            detected_faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
            
            for (x, y, w, h) in detected_faces:
                # Create a simple face object
                face = type('Face', (), {})()
                face.bbox = np.array([x, y, x+w, y+h])
                face.kps = None
                face.det_score = 0.9  # Fixed confidence
                face.embedding = np.random.normal(0, 1, 512)  # Random embedding for demo
                faces.append(face)
                
                if max_num > 0 and len(faces) >= max_num:
                    break
        
        return faces
