import streamlit as st
import cv2
import numpy as np
from insightface.app import FaceAnalysis
import sqlite3
import json
from datetime import datetime
import os
import uuid


# Constants
DATABASE_PATH = 'attendance_system.db'
MODEL_ROOT = '/home/invisa/Desktop/my_grad_streamlit/insightface_model'
# # MODEL_NAME = 'antelopev2'
MODEL_NAME = 'buffalo_sc'

# # Get model path from environment variable
# MODEL_ROOT = os.environ.get('INSIGHTFACE_MODEL_DIR', '/app/insightface_model')
# MODEL_NAME = 'antelopev2'

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
    """Register face from a given image"""
    try:
        faces = app.get(image)
        if not faces:
            return False
        embedding = faces[0].embedding
        normalized_embedding = embedding / np.linalg.norm(embedding)
        embedding_str = json.dumps(normalized_embedding.tolist())
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Insert into presidents_embeds
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
        
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Registration error: {str(e)}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def add_embedding_to_collection(name, embedding, collection):
    """Add a single embedding to an existing ChromaDB collection"""
    try:
        if collection is None:
            return False
            
        # Generate a unique ID for this embedding
        embedding_id = str(uuid.uuid4())
        
        # Add the embedding to the collection
        collection.add(
            ids=[embedding_id],
            documents=[name],
            embeddings=[embedding],
            metadatas=[{"name": name}]
        )
        
        print(f"Added new embedding for {name} to collection")
        return True
    except Exception as e:
        print(f"Error adding embedding to collection: {e}")
        return False

def show_registration_form():
    st.header("Registration Form")
    name = st.text_input("Name", key="reg_name")
    
    # Initialize session state for uploaded files
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = []
    
    # File uploader
    uploaded_files = st.file_uploader("Upload images", type=["jpg", "jpeg", "png"], 
                                    accept_multiple_files=True, key="file_uploader")
    
    # Store uploaded files in session state
    if uploaded_files:
        st.session_state.uploaded_files = uploaded_files
    
    # Display preview of uploaded images
    if st.session_state.uploaded_files:
        st.write("Preview of uploaded images:")
        cols = st.columns(4)
        for idx, uploaded_file in enumerate(st.session_state.uploaded_files):
            file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
            image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            if image is not None:
                resized_image = cv2.resize(image, (150, 150))
                cols[idx % 4].image(resized_image, channels="BGR", use_container_width=True)
            # Reset file pointer to beginning
            uploaded_file.seek(0)
    
    # Camera registration
    st.write("### Camera Registration")
    camera_image = st.camera_input("Take a picture for registration")
    
    # Registration button for camera
    if camera_image and name:
        if st.button("Register from Camera"):
            file_bytes = np.asarray(bytearray(camera_image.read()), dtype=np.uint8)
            image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            if image is not None:
                if register_face_from_image(image, name):
                    st.success(f"Successfully registered {name} from camera!")
                else:
                    st.error("No face detected in the image")
    
    # Registration button for uploaded files
    if st.button("Register from Uploaded Images") and name and st.session_state.uploaded_files:
        success_count = 0
        for idx, uploaded_file in enumerate(st.session_state.uploaded_files):
            file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
            image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            if image is not None:
                if register_face_from_image(image, name):
                    success_count += 1
                # Reset file pointer for potential future use
                uploaded_file.seek(0)
        
        if success_count > 0:
            st.success(f"Registered {success_count} images for {name}!")
        else:
            st.error("No faces detected in any uploaded images")
    
if __name__ == "__main__":
    show_registration_form()