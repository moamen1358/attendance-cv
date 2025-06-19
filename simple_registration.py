import streamlit as st
import cv2
import numpy as np
from insightface.app import FaceAnalysis
import sqlite3
from database_utils import execute_query, execute_query_df
import json
from datetime import datetime
import os
import uuid

# Constants
DATABASE_PATH = 'attendance_system.db'
MODEL_ROOT = '/home/invisa/Desktop/my_grad_streamlit/insightface_model'
MODEL_NAME = 'buffalo_sc'

DETECTION_SIZE = (640, 640)

# Initialize database
def initialize_database():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS attendance_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        timestamp DATETIME NOT NULL
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS presidents_embeds (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        facial_features TEXT NOT NULL
    )
    ''')
    conn.commit()
    conn.close()

initialize_database()

# Initialize face analysis model
try:
    app = FaceAnalysis(name=MODEL_NAME, root=MODEL_ROOT, providers=['CUDAExecutionProvider'])
    app.prepare(ctx_id=0, det_size=DETECTION_SIZE)
except Exception as e:
    st.error(f"Failed to initialize face analysis model: {str(e)}")
    st.stop()

def register_face_from_image(image, name):
    """Register face from a given image - Original simple version"""
    try:
        faces = app.get(image)
        if not faces:
            return False
        embedding = faces[0].embedding
        normalized_embedding = embedding / np.linalg.norm(embedding)
        embedding_str = json.dumps(normalized_embedding.tolist())
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Try to insert into both tables for compatibility
        try:
            # First try the modern table
            cursor.execute('''
                INSERT INTO facial_recognition_data (name, facial_features)
                VALUES (?, ?)
            ''', (name, embedding_str))
        except sqlite3.OperationalError:
            # Fall back to older table
            cursor.execute('''
                INSERT INTO presidents_embeds (name, facial_features)
                VALUES (?, ?)
            ''', (name, embedding_str))

        # Check if the name exists in the students table
        existing_name = cursor.execute('''
            SELECT name FROM students WHERE name = ?
        ''', (name,)).fetchone()
        
        # Insert into students if the name does not exist
        if existing_name is None:
            cursor.execute('''
                INSERT INTO students (name)
                VALUES (?)
            ''', (name,))
        
        # Also add to student_profiles if the table exists
        try:
            cursor.execute("SELECT name FROM student_profiles WHERE name = ?", (name,))
            if not cursor.fetchone():
                cursor.execute('''
                    INSERT INTO student_profiles (name, username, password)
                    VALUES (?, ?, ?)
                ''', (name, name.lower(), f"{name.lower()}_123"))
        except sqlite3.OperationalError:
            # student_profiles table might not exist
            pass
        
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Registration error: {str(e)}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def show_simple_registration_form():
    """Simple registration form - just name and image like the original"""
    st.header("👤 Simple Registration Form")
    st.markdown("*Original simple version - just name and photo*")
    
    name = st.text_input("Student Name", key="simple_reg_name", 
                        help="Enter the student's full name")
    
    # Initialize session state for uploaded files
    if 'uploaded_files_simple' not in st.session_state:
        st.session_state.uploaded_files_simple = []
    
    # File uploader
    uploaded_files = st.file_uploader("Upload images", type=["jpg", "jpeg", "png"], 
                                    accept_multiple_files=True, key="simple_file_uploader",
                                    help="Upload one or more clear photos of the student")
    
    # Store uploaded files in session state
    if uploaded_files:
        st.session_state.uploaded_files_simple = uploaded_files
    
    # Display preview of uploaded images
    if st.session_state.uploaded_files_simple:
        st.write("📸 Preview of uploaded images:")
        cols = st.columns(4)
        for idx, uploaded_file in enumerate(st.session_state.uploaded_files_simple):
            file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
            image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            if image is not None:
                resized_image = cv2.resize(image, (150, 150))
                cols[idx % 4].image(resized_image, channels="BGR", use_container_width=True)
            # Reset file pointer to beginning
            uploaded_file.seek(0)
    
    # Camera registration
    st.write("### 📷 Camera Registration")
    camera_image = st.camera_input("Take a picture for registration",
                                 help="Take a clear photo of the student's face")
    
    # Registration buttons
    col1, col2 = st.columns(2)
    
    with col1:
        # Registration button for camera
        if camera_image and name:
            if st.button("📷 Register from Camera", type="primary"):
                file_bytes = np.asarray(bytearray(camera_image.read()), dtype=np.uint8)
                image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
                if image is not None:
                    if register_face_from_image(image, name):
                        st.success(f"✅ Successfully registered {name} from camera!")
                        # Clear the form
                        st.session_state.uploaded_files_simple = []
                    else:
                        st.error("❌ No face detected in the image")
                else:
                    st.error("❌ Invalid image format")
    
    with col2:
        # Registration button for uploaded files
        if name and st.session_state.uploaded_files_simple:
            if st.button("📁 Register from Uploaded Images", type="primary"):
                success_count = 0
                for idx, uploaded_file in enumerate(st.session_state.uploaded_files_simple):
                    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
                    image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
                    if image is not None:
                        if register_face_from_image(image, name):
                            success_count += 1
                        # Reset file pointer for potential future use
                        uploaded_file.seek(0)
                
                if success_count > 0:
                    st.success(f"✅ Registered {success_count} images for {name}!")
                    # Clear the form
                    st.session_state.uploaded_files_simple = []
                else:
                    st.error("❌ No faces detected in any uploaded images")
    
    # Show simple instructions
    with st.expander("📋 Instructions"):
        st.markdown("""
        **How to use the simple registration:**
        1. Enter the student's name
        2. Either take a photo with your camera OR upload image files
        3. Click the appropriate registration button
        4. The student will be added to the system for attendance tracking
        
        **Photo requirements:**
        - Clear, well-lit photo of the face
        - Student should be looking at the camera
        - Only one person visible in each photo
        """)
    
    # Show recent registrations
    st.markdown("---")
    st.subheader("📋 Recent Simple Registrations")
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get recent students from the students table
        cursor.execute("SELECT id, name FROM students ORDER BY id DESC LIMIT 10")
        recent_students = cursor.fetchall()
        
        if recent_students:
            st.write("**Recently registered students:**")
            for student_id, student_name in recent_students:
                st.write(f"• {student_name} (ID: {student_id})")
        else:
            st.info("No students registered yet using the simple form.")
        
        conn.close()
    except Exception as e:
        st.error(f"Error loading recent registrations: {e}")

if __name__ == "__main__":
    st.set_page_config(
        page_title="Simple Registration Form",
        page_icon="👤",
        layout="centered"
    )
    
    show_simple_registration_form()
