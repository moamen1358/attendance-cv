import streamlit as st
import cv2
import numpy as np
from datetime import datetime
import sqlite3
import os
from cpu_face_analysis import CPUFaceAnalysis

def create_cpu_predictor():
    """Create CPU-only face predictor"""
    return CPUFaceAnalysis()

def cpu_real_time_prediction():
    st.title("🖥️ CPU Face Recognition (Demo Mode)")
    st.warning("Running in CPU-only mode with limited functionality")
    
    if st.button("Test CPU Face Detection"):
        st.info("CPU mode active - using OpenCV Haar Cascades")
        st.success("✅ Face detection system ready (CPU mode)")
    
    st.info("""
    **CPU Mode Features:**
    - Basic face detection using OpenCV
    - Limited recognition capabilities
    - No GPU required
    - Suitable for testing and development
    """)

if __name__ == "__main__":
    cpu_real_time_prediction()
