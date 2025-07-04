import streamlit as st
import cv2
import numpy as np
from datetime import datetime
import time
import sys
import os
from pathlib import Path

# Add camera_scripts to path for imports
camera_scripts_path = Path(__file__).parent.parent / "camera_scripts"
sys.path.append(str(camera_scripts_path))

# Add local insightface to path BEFORE importing
insightface_path = Path(__file__).parent.parent / "insightface" / "python-package"
sys.path.insert(0, str(insightface_path))

# Import our custom FaceAnalysis with YOLO integration
from custom_face_analysis import CustomFaceAnalysis as FaceAnalysis

MODEL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_NAME = 'antelopev2'  # Changed to antelopev2 for better embeddings
DETECTION_SIZE = (640, 640)  # Updated for yolov11l
CONFIDENCE_THRESHOLD = 0.25

# Initialize face analysis model
@st.cache_resource
def load_face_model():
    try:
        yolo_path = os.path.join(os.path.dirname(__file__), "..", "models", "yolov11l-face.pt")  # Changed to yolov11l
        
        app = FaceAnalysis(
            name=MODEL_NAME, 
            root=MODEL_ROOT, 
            yolo_model_path=yolo_path,
            providers=['CUDAExecutionProvider', 'CPUExecutionProvider'],
            gpu_mode='HYBRID'
        )
        app.prepare(ctx_id=0, det_size=DETECTION_SIZE, det_thresh=CONFIDENCE_THRESHOLD)
        return app
    except Exception as e:
        st.error(f"Failed to load face model: {e}")
        return None

def process_frame(frame, app):
    """Simple frame processing - just detect faces and draw boxes"""
    if app is None:
        return frame
    
    try:
        faces = app.get(frame)
        
        for face in faces:
            x1, y1, x2, y2 = face.bbox.astype(int)
            confidence = face.det_score
            
            # Draw green box around detected face
            color = (0, 255, 0)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, f"Face {confidence:.2f}", (x1, y1-10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        return frame
    except Exception:
        return frame

def show_simple_livestream():
    st.markdown("""
    <style>
    .main-header {
        text-align: center;
        color: #1f77b4;
        font-size: 2.5em;
        font-weight: bold;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Simple header
    st.markdown('<div class="main-header">📹 Live Camera Stream</div>', unsafe_allow_html=True)
    
    # Load face detection model
    app = load_face_model()
    
    if app is None:
        st.error("❌ Could not load face detection model")
        return
    
    st.success("✅ Face detection model loaded")
    
    # Simple controls
    col1, col2 = st.columns([3, 1])
    with col2:
        stop_stream = st.button("🛑 Stop Stream", type="secondary")
    
    # Stream display
    stream_placeholder = st.empty()
    
    # Initialize camera
    cap = cv2.VideoCapture(0)  # Use local camera
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    
    if not cap.isOpened():
        st.error("❌ Could not open camera")
        return
    
    st.info("🎥 Camera stream starting...")
    
    # Simple streaming loop
    frame_count = 0
    
    try:
        while not stop_stream:
            ret, frame = cap.read()
            if not ret:
                st.error("❌ Failed to read from camera")
                break
            
            frame_count += 1
            
            # Process frame for face detection
            processed_frame = process_frame(frame, app)
            
            # Add simple overlay
            current_time = datetime.now().strftime("%H:%M:%S")
            cv2.putText(processed_frame, f"Time: {current_time}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(processed_frame, f"Frame: {frame_count}", (10, 70), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Display frame
            stream_placeholder.image(processed_frame, channels="BGR", 
                                   caption="🎥 Live Camera Feed with Face Detection", 
                                   use_container_width=True)
            
            # Small delay for smooth streaming
            time.sleep(0.03)
            
    except KeyboardInterrupt:
        pass
    finally:
        cap.release()
        st.success(f"🏁 Stream ended. Processed {frame_count} frames.")

if __name__ == "__main__":
    show_simple_livestream()
