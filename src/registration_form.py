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
import hashlib  # Added for password hashing

# Constants
DATABASE_PATH = 'attendance_system.db'
MODEL_ROOT = '/home/invisa/Desktop/my_grad_streamlit/insightface_model'
MODEL_NAME = 'buffalo_sc'

DETECTION_SIZE = (640, 640)

# Initialize face analysis model
try:
    app = FaceAnalysis(name=MODEL_NAME, root=MODEL_ROOT, providers=['CUDAExecutionProvider'])
    app.prepare(ctx_id=0, det_size=DETECTION_SIZE)
except Exception as e:
    st.error(f"Failed to initialize face analysis model: {str(e)}")
    st.stop()

def get_departments():
    """Get list of available departments"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT department_code, department_name FROM departments ORDER BY department_name")
        departments = cursor.fetchall()
        conn.close()
        return departments
    except Exception:
        return [('CS', 'Computer Science'), ('AI', 'Artificial Intelligence')]

def register_student(student_data, image):
    """Register a student with the enhanced database structure"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Extract student data
        name = student_data.get('name', '').strip()
        email = student_data.get('email', '').strip()
        phone = student_data.get('phone', '').strip()
        department_code = student_data.get('department', 'CS')
        academic_year = student_data.get('academic_year', 1)
        semester = student_data.get('semester', 1)
        
        if not name:
            st.error("Name is required.")
            return False
        
        # Generate username from name (lowercase, replace spaces with underscores)
        username = name.lower().replace(' ', '_').replace('.', '').replace('-', '_')
        
        # Generate student number
        year = 2024  # Current academic year
        
        # Get next sequence number for this department
        cursor.execute("""
            SELECT COUNT(*) FROM student_profiles_enhanced 
            WHERE student_number LIKE ?
        """, (f"{department_code}{year}%",))
        count = cursor.fetchone()[0] + 1
        student_number = f"{department_code}{year}{count:03d}"
        
        # Generate password (firstname_lastname123)
        name_parts = name.split()
        first_name = name_parts[0].lower()
        last_name = name_parts[-1].lower() if len(name_parts) > 1 else "user"
        password = f"{first_name}_{last_name}123"
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        # Check if username already exists
        cursor.execute("SELECT username FROM student_profiles_enhanced WHERE username = ?", (username,))
        if cursor.fetchone():
            # If username exists, add a number suffix
            counter = 1
            original_username = username
            while True:
                username = f"{original_username}_{counter}"
                cursor.execute("SELECT username FROM student_profiles_enhanced WHERE username = ?", (username,))
                if not cursor.fetchone():
                    break
                counter += 1
        
        # Get department ID
        cursor.execute("SELECT department_id FROM departments WHERE department_code = ?", (department_code,))
        dept_result = cursor.fetchone()
        department_id = dept_result[0] if dept_result else 1  # Default to first department
        
        # STEP 1: Create student profile
        cursor.execute("""
            INSERT INTO student_profiles_enhanced 
            (username, name, student_number, email, phone, department_id, academic_year, current_semester)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (username, name, student_number, email, phone, department_id, academic_year, semester))
        
        student_id = cursor.lastrowid
        st.success(f"✅ Created student profile for '{name}'")
        
        # STEP 2: Create user account
        cursor.execute("""
            INSERT INTO user_accounts_enhanced 
            (username, password, role, student_id)
            VALUES (?, ?, 'student', ?)
        """, (username, hashed_password, student_id))
        st.success("✅ Created login account")
        
        # STEP 3: Auto-enroll in subjects for their department, year, and semester
        cursor.execute("""
            SELECT subject_id, subject_name FROM subjects_enhanced 
            WHERE department_id = ? AND academic_year = ? AND semester = ?
        """, (department_id, academic_year, semester))
        
        available_subjects = cursor.fetchall()
        enrolled_subjects = []
        
        if available_subjects:
            # Get active term
            cursor.execute("SELECT term_id FROM academic_terms WHERE is_active = 1 LIMIT 1")
            term_result = cursor.fetchone()
            term_id = term_result[0] if term_result else 1
            
            for subject_id, subject_name in available_subjects:
                cursor.execute("""
                    INSERT INTO student_enrollments 
                    (student_id, subject_id, term_id, status)
                    VALUES (?, ?, ?, 'enrolled')
                """, (student_id, subject_id, term_id))
                enrolled_subjects.append(subject_name)
            
            if enrolled_subjects:
                st.success(f"✅ Enrolled in subjects: {', '.join(enrolled_subjects)}")
        
        # STEP 4: Process facial recognition data
        if image is not None:
            faces = app.get(image)
            if faces:
                embedding = faces[0].embedding
                normalized_embedding = embedding / np.linalg.norm(embedding)
                embedding_json = json.dumps(normalized_embedding.tolist())
                
                # Save facial embedding
                cursor.execute("""
                    INSERT INTO facial_embeddings 
                    (student_id, embedding_data, confidence_threshold)
                    VALUES (?, ?, 0.6)
                """, (student_id, embedding_json))
                st.success("✅ Facial recognition data saved")
                
                # Also save to legacy table for compatibility
                cursor.execute("""
                    INSERT INTO presidents_embeds (name, facial_features) 
                    VALUES (?, ?)
                """, (name, embedding_json))
                
            else:
                st.warning("⚠️ No face detected in the image")
        
        conn.commit()
        
        # Show registration summary
        st.success("🎉 Student registration completed successfully!")
        
        with st.expander("📋 Registration Summary", expanded=True):
            st.write(f"**Name:** {name}")
            st.write(f"**Student Number:** {student_number}")
            st.write(f"**Department:** {department_code}")
            st.write(f"**Academic Year:** {academic_year}")
            st.write(f"**Current Semester:** {semester}")
            if enrolled_subjects:
                st.write(f"**Enrolled Subjects:** {', '.join(enrolled_subjects)}")
        
        return True
        
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False
    except Exception as e:
        st.error(f"Registration error: {str(e)}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def show_registration_form():
    """Display the student registration form"""
    st.header("🎓 Student Registration")
    
    # Camera/Photo section at the top with full width
    st.subheader("📸 Photo Capture")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Camera input
        camera_input = st.camera_input("Take a photo for facial recognition")
        
        if camera_input is not None:
            # Convert the uploaded file to cv2 image
            bytes_data = camera_input.read()
            image_array = np.frombuffer(bytes_data, np.uint8)
            image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            
            # Display the captured image
            st.image(image, channels="BGR", use_column_width=True, caption="Captured Photo")
        else:
            image = None
    
    with col2:
        if camera_input:
            st.success("✅ Photo captured successfully!")
        else:
            st.info("📷 Please capture your photo")
    
    st.divider()
    
    # Registration form
    st.subheader("📝 Student Information")
    
    # Get departments for dropdown
    departments = get_departments()
    department_options = {f"{code} - {name}": code for code, name in departments}
    
    with st.form("student_registration"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Full Name *", placeholder="Enter your full name")
            email = st.text_input("Email", placeholder="your.email@university.edu")
            department = st.selectbox(
                "Department *",
                options=list(department_options.keys()),
                index=0
            )
        
        with col2:
            phone = st.text_input("Phone Number", placeholder="+20 1XX XXX XXXX")
            academic_year = st.selectbox(
                "Academic Year *",
                options=[1, 2, 3, 4],
                index=0,
                format_func=lambda x: f"Year {x}"
            )
            semester = st.selectbox(
                "Current Semester *",
                options=[1, 2],
                index=0,
                format_func=lambda x: f"Semester {x}"
            )
        
        submitted = st.form_submit_button("🎯 Register Student", use_container_width=True)
        
        if submitted:
            if not name:
                st.error("⚠️ Name is required!")
            elif not camera_input:
                st.error("⚠️ Please capture a photo for facial recognition!")
            else:
                # Prepare student data
                selected_dept_code = department_options[department]
                
                student_data = {
                    'name': name,
                    'email': email,
                    'phone': phone,
                    'department': selected_dept_code,
                    'academic_year': academic_year,
                    'semester': semester
                }
                
                # Register the student
                success = register_student(student_data, image)
                
                if success:
                    st.balloons()
                    st.rerun()

def main():
    """Main function to run the registration form"""
    show_registration_form()

if __name__ == "__main__":
    main()
