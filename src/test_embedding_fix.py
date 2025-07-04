import os
import sys
import numpy as np
from pathlib import Path

# Add camera_scripts to path for imports
camera_scripts_path = Path("..") / "camera_scripts"
sys.path.append(str(camera_scripts_path))

# Add local insightface to path BEFORE importing
insightface_path = Path("..") / "insightface" / "python-package"
sys.path.insert(0, str(insightface_path))

# Import our custom FaceAnalysis with YOLO integration
from custom_face_analysis import CustomFaceAnalysis as FaceAnalysis

MODEL_ROOT = os.path.join("..", "models")
MODEL_NAME = 'buffalo_l'
DETECTION_SIZE = (640, 640)

try:
    yolo_path = os.path.join("..", "models", "yolov11l-face.pt")
    print(f'Testing YOLO path: {yolo_path}')
    print(f'YOLO exists: {os.path.exists(yolo_path)}')
    
    app = FaceAnalysis(name=MODEL_NAME, root=MODEL_ROOT, yolo_model_path=yolo_path)
    app.prepare(ctx_id=-1, det_size=DETECTION_SIZE)
    
    print('✅ FaceAnalysis initialized successfully!')
    print(f'Available models: {list(app.models.keys())}')
    
    # Test with a dummy image that has face-like properties
    test_img = np.zeros((480, 640, 3), dtype=np.uint8)
    # Create a face-like pattern
    test_img[100:300, 200:400] = [180, 150, 120]  # Skin tone rectangle
    test_img[130:150, 230:250] = [50, 50, 50]     # Left eye
    test_img[130:150, 350:370] = [50, 50, 50]     # Right eye
    test_img[160:180, 280:320] = [100, 80, 70]    # Nose
    test_img[200:220, 260:340] = [120, 80, 80]    # Mouth
    
    faces = app.get(test_img)
    print(f'Detected {len(faces)} faces')
    
    for i, face in enumerate(faces):
        print(f'Face {i+1}:')
        print(f'  - Bbox: {face.bbox}')
        print(f'  - Score: {face.det_score}')
        print(f'  - Has embedding: {face.embedding is not None}')
        if face.embedding is not None:
            print(f'  - Embedding shape: {face.embedding.shape}')
            print(f'  - Embedding dtype: {face.embedding.dtype}')
            print(f'  - Embedding min/max: {face.embedding.min():.3f}/{face.embedding.max():.3f}')
        else:
            print(f'  - ❌ No embedding generated!')
            
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
