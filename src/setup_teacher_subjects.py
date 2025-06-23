import streamlit as st
import pandas as pd
import sqlite3

DATABASE_PATH = 'attendance_system.db'

def create_or_update_schema():
    """Use centralized database initialization instead of local table creation"""
    try:
        from db_init import initialize_database, check_database_integrity
        
        print("Using centralized database initialization...")
        success = initialize_database()
        if success:
            check_database_integrity()
            print("Database initialization completed successfully")
        else:
            print("Database initialization failed")
        
        return success
    except ImportError:
        print("Centralized database initialization not available")
        return True

# Initialize schema when the module is imported
create_or_update_schema()

import streamlit as st
import pandas as pd
import sqlite3

DATABASE_PATH = 'attendance_system.db'

def create_or_update_schema():
    """Use centralized database initialization instead of local table creation"""
    try:
        from db_init import initialize_database, check_database_integrity
        
        print("Using centralized database initialization...")
        success = initialize_database()
        if success:
            check_database_integrity()
            print("Database initialization completed successfully")
        else:
            print("Database initialization failed")
        
        return success
    except ImportError:
        print("Centralized database initialization not available")
        return True

# Initialize schema when the module is imported
create_or_update_schema()

def get_teacher_subjects(username):
    """Get list of subjects taught by a specific teacher using enhanced tables"""
    conn = sqlite3.connect('attendance_system.db')
    cursor = conn.cursor()
    
    try:
        # First, get the teacher's linked_id from users_enhanced
        cursor.execute("""
            SELECT linked_id 
            FROM users_enhanced 
            WHERE username = ? AND role = 'teacher'
        """, (username,))
        
        result = cursor.fetchone()
        if not result:
            print(f"Teacher {username} not found in users_enhanced table")
            return []
        
        teacher_id = result[0]
        
        # Get subjects from teacher_subjects_enhanced table
        cursor.execute("""
            SELECT s.subject_name, s.course_code
            FROM teacher_subjects_enhanced ts
            JOIN subjects_enhanced s ON ts.subject_id = s.subject_id
            WHERE ts.teacher_id = ? AND ts.status = 'active'
            ORDER BY s.subject_name
        """, (teacher_id,))
        
        subjects = [f"{row[0]} ({row[1]})" for row in cursor.fetchall()]
        
        if subjects:
            print(f"Found {len(subjects)} subjects for teacher {username}: {subjects}")
            return subjects
        
        print(f"No subjects found for teacher {username} (teacher_id: {teacher_id})")
        return []
        
    except Exception as e:
        print(f"Error in get_teacher_subjects for {username}: {e}")
        return []
    finally:
        conn.close()

def get_all_subjects():
    """Get all subjects from enhanced database"""
    conn = sqlite3.connect(DATABASE_PATH)
    query = "SELECT * FROM subjects_enhanced ORDER BY subject_name"
    
    try:
        df = pd.read_sql(query, conn)
    except Exception as e:
        print(f"Error getting subjects: {e}")
        df = pd.DataFrame(columns=['subject_id', 'subject_name', 'course_code'])
    
    conn.close()
    return df

def assign_subject_to_teacher(teacher_username, subject_id):
    """Assign a subject to a teacher using enhanced tables"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # Get teacher's linked_id from users_enhanced
        cursor.execute("""
            SELECT linked_id 
            FROM users_enhanced 
            WHERE username = ? AND role = 'teacher'
        """, (teacher_username,))
        
        result = cursor.fetchone()
        if not result:
            return False, f"Teacher {teacher_username} not found"
        
        teacher_id = result[0]
        
        # Check if this assignment already exists
        cursor.execute("""
            SELECT id FROM teacher_subjects_enhanced 
            WHERE teacher_id = ? AND subject_id = ? AND status = 'active'
        """, (teacher_id, subject_id))
        
        exists = cursor.fetchone()
        
        if not exists:
            # Create new assignment
            cursor.execute("""
                INSERT INTO teacher_subjects_enhanced 
                (teacher_id, subject_id, academic_year, semester, section, status)
                VALUES (?, ?, '2024-2025', 'Fall', 'A', 'active')
            """, (teacher_id, subject_id))
            conn.commit()
            return True, "Subject assigned successfully"
        else:
            return False, "This subject is already assigned to this teacher"
    
    except Exception as e:
        conn.rollback()
        return False, f"Error assigning subject: {e}"
    finally:
        conn.close()

def get_teacher_info(username):
    """Get teacher information from enhanced tables"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT full_name, email, linked_id
            FROM users_enhanced 
            WHERE username = ? AND role = 'teacher'
        """, (username,))
        
        result = cursor.fetchone()
        if result:
            return {
                'full_name': result[0],
                'email': result[1],
                'linked_id': result[2]
            }
        return None
        
    except Exception as e:
        print(f"Error getting teacher info: {e}")
        return None
    finally:
        conn.close()
