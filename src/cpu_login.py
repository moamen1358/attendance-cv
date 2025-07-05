import streamlit as st
import sqlite3
import os
from datetime import datetime
import sys

# Set page config
st.set_page_config(
    page_title="Face Recognition System (CPU Mode)",
    page_icon="🖥️",
    layout="wide"
)

def main():
    st.title("🖥️ Face Recognition Attendance System")
    st.subheader("CPU Mode - Demo Version")
    
    st.info("Running in CPU-only mode for compatibility")
    
    # Simple navigation
    menu = ["Login", "CPU Demo", "About"]
    choice = st.sidebar.selectbox("Menu", menu)
    
    if choice == "Login":
        st.header("👤 User Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            if username and password:
                st.success(f"Welcome {username}! (Demo Mode)")
                st.info("CPU-only demonstration - full features require GPU")
            else:
                st.error("Please enter username and password")
    
    elif choice == "CPU Demo":
        st.header("🖥️ CPU Face Detection Demo")
        from cpu_real_time_prediction import cpu_real_time_prediction
        cpu_real_time_prediction()
    
    elif choice == "About":
        st.header("📋 About")
        st.write("""
        **Face Recognition Attendance System**
        
        Currently running in CPU-only mode due to CUDA compatibility issues.
        
        **Features in CPU Mode:**
        - Basic OpenCV face detection
        - User interface demonstration
        - Database connectivity (read-only)
        
        **For full features:**
        - GPU/CUDA support required
        - Advanced face recognition models
        - Real-time attendance tracking
        """)

if __name__ == "__main__":
    main()
