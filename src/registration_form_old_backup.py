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

def generate_default_password(name, section):
    """Generate a password based on name and section"""
    # Format: {name}_{section_abbreviated}
    # Example: "moamen" in "Section 1" → "moamen_sec1"
    
    # Get section number (default to "0" if not available)
    section_num = "0"
    if section and "Section" in section:
        try:
            section_num = section.split()[-1]  # Extract number from "Section X"
        except:
            pass
    
    # Create password
    password = f"{name}_sec{section_num}"
    return password

def register_student(student_data, image):
    """Register a student with the enhanced database structure"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Extract student data
        name = student_data.get('name', '')
        email = student_data.get('email', '')
        phone = student_data.get('phone', '')
        department = student_data.get('department', '')
        academic_year = student_data.get('academic_year', 1)
        semester = student_data.get('semester', 1)
        
        if not name:
            st.error("Name is required.")
            return False
        
        # Generate username from name (lowercase, replace spaces with underscores)
        username = name.lower().replace(' ', '_').replace('.', '').replace('-', '_')
        
        # Generate student number
        year = 2024  # Current academic year
        dept_code = department[:2].upper() if department else 'GN'
        
        # Get next sequence number for this department
        cursor.execute("""
            SELECT COUNT(*) FROM student_profiles_enhanced 
            WHERE student_number LIKE ?
        """, (f"{dept_code}{year}%",))
        count = cursor.fetchone()[0] + 1
        student_number = f"{dept_code}{year}{count:03d}"
        
        # Generate password (firstname_lastname123)
        name_parts = name.split()
        first_name = name_parts[0].lower()
        last_name = name_parts[-1].lower() if len(name_parts) > 1 else "user"
        password = f"{first_name}_{last_name}123"
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        # Check if username already exists
        cursor.execute("SELECT username FROM student_profiles_enhanced WHERE username = ?", (username,))
        if cursor.fetchone():
            st.error(f"Username '{username}' already exists.")
            return False
        
        # Get department ID
        cursor.execute("SELECT department_id FROM departments WHERE department_code = ?", (dept_code,))
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
            st.write(f"**Department:** {department}")
            st.write(f"**Academic Year:** {academic_year}")
            st.write(f"**Current Semester:** {semester}")
            if enrolled_subjects:
                st.write(f"**Enrolled Subjects:** {', '.join(enrolled_subjects)}")
        
        return True
        
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        conn.rollback()
        return False
    except Exception as e:
        st.error(f"Registration error: {str(e)}")
        return False
    finally:
        conn.close()
        if image is not None:
            faces = app.get(image)
            if faces:
                embedding = faces[0].embedding
                normalized_embedding = embedding / np.linalg.norm(embedding)
                embedding_str = json.dumps(normalized_embedding.tolist())
                
                # Save to presidents_embeds table
                cursor.execute(
                    "INSERT INTO presidents_embeds (name, facial_features) VALUES (?, ?)",
                    (name, embedding_str)
                )
                st.info(f"✅ Added face embedding for '{name}' to presidents_embeds table")
            else:
                st.warning("No face detected in the image. Name saved to students table but no facial data.")
        else:
            st.warning("No image provided. Name saved to students table but no facial data.")
        
        # STEP 3: Try to add to student_profiles table if it exists (for compatibility)
        try:
            # Check if student_profiles table exists and get its structure
            cursor.execute("PRAGMA table_info(student_profiles)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if columns:  # Table exists
                # Check if student already exists in profiles
                existing_profile = cursor.execute("SELECT name FROM student_profiles WHERE name = ?", (name,)).fetchone()
                if not existing_profile:
                    # Determine which columns to insert based on what exists in the table
                    available_columns = []
                    values = []
                    
                    # Add basic required fields
                    if 'name' in columns:
                        available_columns.append('name')
                        values.append(name)
                        
                    if 'section' in columns and section:
                        available_columns.append('section')
                        values.append(section)
                        
                    # Add optional fields if they exist in the table schema
                    if 'student_id' in columns and 'student_id' in student_data and student_data['student_id']:
                        available_columns.append('student_id')
                        values.append(student_data['student_id'])
                        
                    if 'email' in columns and 'email' in student_data and student_data['email']:
                        available_columns.append('email')
                        values.append(student_data['email'])
                        
                    if 'phone' in columns and 'phone' in student_data and student_data['phone']:
                        available_columns.append('phone')
                        values.append(student_data['phone'])
                    
                    # Build dynamic INSERT statement based on available columns
                    if available_columns:
                        columns_str = ', '.join(available_columns)
                        placeholders = ', '.join(['?' for _ in available_columns])
                        insert_sql = f"INSERT INTO student_profiles ({columns_str}) VALUES ({placeholders})"
                        cursor.execute(insert_sql, values)
                        st.info(f"✅ Added '{name}' to student_profiles table")
                        
                        # Create user account with default password
                        try:
                            default_password = generate_default_password(name, section)
                            cursor.execute(
                                "INSERT INTO user_accounts (username, password, role) VALUES (?, ?, 'student')",
                                (name, default_password)
                            )
                            st.info(f"✅ Created user account for '{name}'")
                        except sqlite3.IntegrityError:
                            # User account might already exist
                            st.info(f"ℹ️ User account for '{name}' already exists")
        except sqlite3.OperationalError:
            # student_profiles table might not exist, which is fine
            st.info("ℹ️ student_profiles table not found, skipping profile creation")
        
        conn.commit()
        
        # Show success message
        success_message = f"""
        🎉 **Student registration completed successfully!**
        
        **What was saved:**
        ✅ Name '{name}' added to **students** table
        """
        
        if image is not None:
            faces = app.get(image)
            if faces:
                success_message += "✅ Face embedding saved to **presidents_embeds** table\n"
            else:
                success_message += "⚠️ No face detected - only name saved\n"
        else:
            success_message += "⚠️ No image provided - only name saved\n"
        
        # Add optional fields to success message if they were provided
        if section:
            success_message += f"✅ Section: {section}\n"
        if 'student_id' in student_data and student_data['student_id']:
            success_message += f"✅ Student ID: {student_data['student_id']}\n"
        if 'email' in student_data and student_data['email']:
            success_message += f"✅ Email: {student_data['email']}\n"
            
        st.success(success_message)
        return True
        
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return False
    except Exception as e:
        st.error(f"Registration error: {str(e)}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def register_face_from_image(image, name):
    """Register face from a given image - adds name to students table and face embedding to presidents_embeds table"""
    try:
        if not name:
            st.error("Name is required for registration.")
            return False
            
        faces = app.get(image)
        if not faces:
            st.error("No face detected in the image.")
            return False
            
        embedding = faces[0].embedding
        normalized_embedding = embedding / np.linalg.norm(embedding)
        embedding_str = json.dumps(normalized_embedding.tolist())
        
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # STEP 1: Add to presidents_embeds table (primary face embedding storage)
        try:
            cursor.execute('''
                INSERT INTO presidents_embeds (name, facial_features)
                VALUES (?, ?)
            ''', (name, embedding_str))
            st.info(f"✅ Face embedding for '{name}' saved to presidents_embeds table")
        except sqlite3.IntegrityError:
            st.warning(f"Face embedding for '{name}' already exists in presidents_embeds table")
        
        # STEP 2: Add to students table if not already exists
        existing_name = cursor.execute('''
            SELECT name FROM students WHERE name = ?
        ''', (name,)).fetchone()
        
        if existing_name is None:
            cursor.execute('''
                INSERT INTO students (name)
                VALUES (?)
            ''', (name,))
            st.info(f"✅ Name '{name}' added to students table")
        else:
            st.info(f"ℹ️ Name '{name}' already exists in students table")
        
        # STEP 3: Try to add to newer facial_recognition_data table if it exists (for compatibility)
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO facial_recognition_data (name, facial_features)
                VALUES (?, ?)
            ''', (name, embedding_str))
        except sqlite3.OperationalError:
            # Table doesn't exist, which is fine
            pass
        
        conn.commit()
        
        st.success(f"""
        🎉 **Registration completed for '{name}'!**
        
        **What was saved:**
        ✅ Name added to **students** table
        ✅ Face embedding saved to **presidents_embeds** table
        
        The student can now be recognized by the attendance system.
        """)
        
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
    st.header("🎓 Student Registration Form")
    st.markdown("""
    Register a new student by providing their name and photo. 
    
    **What happens when you register:**
    - ✅ Student name is added to the **students** table
    - ✅ Face embedding is saved to the **presidents_embeds** table
    - ✅ Student can then be recognized by the attendance system
    """)
    
    name = st.text_input("Student Name", key="reg_name", 
                        help="Enter the full name of the student")
    
    # Initialize session state for uploaded files
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = []
    
    # File uploader
    uploaded_files = st.file_uploader("Upload student photos", type=["jpg", "jpeg", "png"], 
                                    accept_multiple_files=True, key="file_uploader",
                                    help="Upload clear photos of the student's face")
    
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
    st.write("### 📷 Camera Registration")
    camera_image = st.camera_input("Take a picture of the student",
                                  help="Take a clear photo of the student's face")
    
    st.markdown("---")
    
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
                        st.balloons()
                        st.rerun()  # Refresh the page
                else:
                    st.error("Invalid image format. Please try again.")
    
    with col2:
        # Registration button for uploaded files
        if st.session_state.uploaded_files and name:
            if st.button("📁 Register from Uploaded Images", type="primary"):
                success_count = 0
                total_files = len(st.session_state.uploaded_files)
                
                for idx, uploaded_file in enumerate(st.session_state.uploaded_files):
                    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
                    image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
                    if image is not None:
                        # Use the first successful registration
                        if success_count == 0 and register_face_from_image(image, name):
                            success_count = 1
                            break
                        uploaded_file.seek(0)
                
                if success_count > 0:
                    st.balloons()
                    # Clear uploaded files after successful registration
                    st.session_state.uploaded_files = []
                    st.rerun()  # Refresh the page
                else:
                    st.error("No faces detected in any uploaded images")
    
    # Show requirements
    with st.expander("📋 Photo Requirements for Best Results"):
        st.markdown("""
        **For successful face recognition:**
        - 📸 Clear, well-lit photo
        - 👁️ Student looking directly at camera
        - 🚫 No sunglasses or face coverings
        - 🎯 Good focus and contrast
        - 👤 Only one person visible in photo
        - 📐 Face should be clearly visible and not too small
        """)
    
    # Show current database status
    st.markdown("---")
    st.subheader("📊 Current Registration Status")
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Count students
        cursor.execute("SELECT COUNT(*) FROM students")
        student_count = cursor.fetchone()[0]
        
        # Count face embeddings
        cursor.execute("SELECT COUNT(*) FROM presidents_embeds")
        embedding_count = cursor.fetchone()[0]
        
        # Show stats
        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("Students Registered", student_count)
        with col_b:
            st.metric("Face Embeddings Stored", embedding_count)
        
        # Show recent registrations
        cursor.execute("SELECT name FROM students ORDER BY id DESC LIMIT 5")
        recent_students = cursor.fetchall()
        
        if recent_students:
            st.write("**Recent Registrations:**")
            for student in recent_students:
                st.write(f"• {student[0]}")
        
        conn.close()
        
    except Exception as e:
        st.error(f"Error loading registration status: {e}")
    
    # Validation messages
    if not name:
        st.warning("⚠️ Please enter a student name")
    if name and not camera_image and not st.session_state.uploaded_files:
        st.warning("⚠️ Please provide a photo (camera or upload)")
    
if __name__ == "__main__":
    show_registration_form()