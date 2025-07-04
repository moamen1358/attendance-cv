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
MODEL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Project root directory
MODEL_NAME = 'buffalo_sc'

DETECTION_SIZE = (640, 640)

# Initialize face analysis model
try:
    app = FaceAnalysis(name=MODEL_NAME, root=MODEL_ROOT, providers=['CUDAExecutionProvider', 'CPUExecutionProvider'], gpu_mode='HYBRID')
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
            SELECT COUNT(*) FROM students_enhanced 
            WHERE roll_number LIKE ?
        """, (f"{department_code}{year}%",))
        count = cursor.fetchone()[0] + 1
        roll_number = f"{department_code}{year}{count:03d}"
        
        # Use the username as the password (simpler and more consistent)
        password = username  # Password is the same as username
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        print(f"Setting password same as username: {username}. Hash: {hashed_password[:10]}...")
        
        # Check if username already exists in users_enhanced table
        cursor.execute("SELECT username FROM users_enhanced WHERE username = ?", (username,))
        if cursor.fetchone():
            # If username exists, add a number suffix
            counter = 1
            original_username = username
            while True:
                username = f"{original_username}_{counter}"
                cursor.execute("SELECT username FROM users_enhanced WHERE username = ?", (username,))
                if not cursor.fetchone():
                    break
                counter += 1
        
        # Check if student name already exists in students_enhanced
        cursor.execute("SELECT name FROM students_enhanced WHERE name = ?", (name,))
        if cursor.fetchone():
            # If name exists, add a number suffix to make it unique
            counter = 1
            original_name = name
            while True:
                name = f"{original_name}_{counter}"
                cursor.execute("SELECT name FROM students_enhanced WHERE name = ?", (name,))
                if not cursor.fetchone():
                    break
                counter += 1
        
        # Get department ID (we'll use the department_code directly since students_enhanced uses department TEXT)
        department_name = department_code  # Use code directly
        
        # STEP 1: Create student record
        cursor.execute("""
            INSERT INTO students_enhanced 
            (name, roll_number, email, phone, department, year, section, enrollment_date, status)
            VALUES (?, ?, ?, ?, ?, ?, 'A', ?, 'active')
        """, (name, roll_number, email, phone, department_name, academic_year, datetime.now().date()))
        
        student_id = cursor.lastrowid
        st.success(f"✅ Created student record for '{name}'")
        
        # STEP 2: Create user account in users_enhanced table
        cursor.execute("""
            INSERT INTO users_enhanced 
            (username, password_hash, role, email, full_name, linked_id, status)
            VALUES (?, ?, 'student', ?, ?, ?, 'active')
        """, (username, hashed_password, email, name, student_id))
        st.success("✅ Created login account")
        
        # STEP 3: Auto-enroll in subjects for their department and year
        cursor.execute("""
            SELECT subject_id, subject_name FROM subjects_enhanced 
            WHERE department = ? AND year = ? AND semester = ?
        """, (department_name, academic_year, semester))
        
        available_subjects = cursor.fetchall()
        enrolled_subjects = []
        
        if available_subjects:
            # Get active term
            cursor.execute("SELECT term_id FROM academic_terms WHERE is_active = 1 LIMIT 1")
            term_result = cursor.fetchone()
            term_id = term_result[0] if term_result else 1
            
            for subject_id, subject_name in available_subjects:
                cursor.execute("""
                    INSERT INTO student_enrollments_enhanced 
                    (student_id, subject_id, academic_year, semester, status)
                    VALUES (?, ?, ?, ?, 'enrolled')
                """, (student_id, subject_id, str(academic_year), str(semester)))
                enrolled_subjects.append(subject_name)
            
            if enrolled_subjects:
                st.success(f"✅ Enrolled in subjects: {', '.join(enrolled_subjects)}")
        
        # STEP 4: Process facial recognition data
        if image is not None:
            st.info("🔍 Processing facial recognition data...")
            
            # Debug: Show image info
            st.write(f"📊 Image shape: {image.shape}")
            
            # Preprocess image for better face detection
            # Convert BGR to RGB for InsightFace
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Resize image if too large (max 1024px on longest side)
            height, width = rgb_image.shape[:2]
            max_size = 1024
            if max(height, width) > max_size:
                scale = max_size / max(height, width)
                new_width = int(width * scale)
                new_height = int(height * scale)
                rgb_image = cv2.resize(rgb_image, (new_width, new_height))
                st.info(f"📏 Resized image from {width}x{height} to {new_width}x{new_height}")
            
            # Try face detection
            try:
                faces = app.get(rgb_image)
                st.write(f"🔍 Detected {len(faces)} face(s)")
                
                if faces:
                    # Show detection confidence
                    for i, face in enumerate(faces):
                        if hasattr(face, 'det_score'):
                            st.write(f"Face {i+1} confidence: {face.det_score:.3f}")
                    
                    # Use the best face (first one, as InsightFace sorts by confidence)
                    best_face = faces[0]
                    embedding = best_face.embedding
                    normalized_embedding = embedding / np.linalg.norm(embedding)
                    embedding_json = json.dumps(normalized_embedding.tolist())
                    
                    # Show embedding info
                    st.write(f"📊 Embedding size: {len(embedding)} dimensions")
                    st.write(f"📊 Embedding norm: {np.linalg.norm(embedding):.3f}")
                    
                    # Draw bounding box on image for visual feedback
                    display_image = image.copy()
                    if hasattr(best_face, 'bbox'):
                        bbox = best_face.bbox.astype(int)
                        # Convert RGB bbox back to BGR image coordinates if needed
                        scale_x = image.shape[1] / rgb_image.shape[1]
                        scale_y = image.shape[0] / rgb_image.shape[0]
                        bbox = (bbox * [scale_x, scale_y, scale_x, scale_y]).astype(int)
                        
                        cv2.rectangle(display_image, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 255, 0), 2)
                        cv2.putText(display_image, f"Face: {best_face.det_score:.2f}", 
                                  (bbox[0], bbox[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                        
                        st.image(display_image, channels="BGR", use_container_width=True, 
                                caption="✅ Face Detected Successfully")
                    
                    # Save facial embedding to student_profiles_enhanced
                    cursor.execute("""
                        INSERT INTO student_profiles_enhanced 
                        (student_id, profile_name, encoding_data, confidence_threshold, status)
                        VALUES (?, ?, ?, 0.6, 'active')
                    """, (student_id, name, embedding_json))
                    st.success("✅ Facial recognition data saved successfully!")
                    
                else:
                    st.error("⚠️ No face detected in the image. Please try:")
                    st.write("• Ensure your face is clearly visible and well-lit")
                    st.write("• Look directly at the camera")
                    st.write("• Remove any obstructions (glasses, masks, etc.)")
                    st.write("• Try taking the photo again")
                    
                    # Still show the image for debugging
                    st.image(image, channels="BGR", use_container_width=True, 
                            caption="❌ No Face Detected")
                    
            except Exception as e:
                st.error(f"❌ Face detection error: {str(e)}")
                st.write("This might be due to:")
                st.write("• Image format issues")
                st.write("• Model loading problems")
                st.write("• GPU/CUDA issues")
                st.write("Please try again or contact support.")
                
        else:
            st.warning("⚠️ No image provided for facial recognition")
        
        conn.commit()
        
        # Show registration summary
        st.success("🎉 Student registration completed successfully!")
        
        with st.expander("📋 Registration Summary", expanded=True):
            st.write(f"**Name:** {name}")
            st.write(f"**Roll Number:** {roll_number}")
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
    
    # Camera input - full width
    camera_input = st.camera_input("")
    
    if camera_input is not None:
        # Convert the uploaded file to cv2 image
        bytes_data = camera_input.read()
        image_array = np.frombuffer(bytes_data, np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        
        # Test face detection immediately when photo is taken
        st.write("🔍 **Testing face detection...**")
        rgb_test_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        try:
            test_faces = app.get(rgb_test_image)
            if test_faces:
                st.success(f"✅ Face detected successfully! (Confidence: {test_faces[0].det_score:.2f})")
                
                # Show image with detection box
                display_img = image.copy()
                if hasattr(test_faces[0], 'bbox'):
                    bbox = test_faces[0].bbox.astype(int)
                    cv2.rectangle(display_img, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 255, 0), 3)
                    cv2.putText(display_img, "FACE DETECTED", (bbox[0], bbox[1]-10), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                st.image(display_img, channels="BGR", use_container_width=True, 
                        caption="✅ Ready for Registration")
            else:
                st.error("❌ No face detected! Please retake the photo.")
                st.image(image, channels="BGR", use_container_width=True, 
                        caption="❌ Face Not Detected - Please Retake")
        except Exception as e:
            st.error(f"Face detection test failed: {e}")
            st.image(image, channels="BGR", use_container_width=True, caption="Photo Captured")
    else:
        image = None
    
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
