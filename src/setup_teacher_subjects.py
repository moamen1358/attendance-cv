import streamlit as st
import pandas as pd
import sqlite3
from database_utils import execute_query, execute_query_df

DATABASE_PATH = 'attendance_system.db'

def create_or_update_schema():
    """Use centralized database initialization instead of local table creation"""
    from db_init import initialize_database, check_database_integrity
    
    print("Using centralized database initialization...")
    success = initialize_database()
    if success:
        check_database_integrity()
        print("Database initialization completed successfully")
    else:
        print("Database initialization failed")
    
    return success

# Initialize schema when the module is imported
create_or_update_schema()

def get_teacher_subjects(username):
    """Get list of subjects taught by a specific teacher"""
    conn = sqlite3.connect('attendance_system.db')
    cursor = conn.cursor()
    
    try:
        # Check if the professor_subject_assignments table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='professor_subject_assignments'
        """)
        
        if cursor.fetchone():
            # First try to get subjects from professor_subject_assignments table
            cursor.execute("""
                SELECT s.subject_name
                FROM professor_subject_assignments psa
                JOIN subjects s ON psa.subject_id = s.subject_id
                WHERE psa.professor_username = ?
                ORDER BY s.subject_name
            """, (username,))
            
            subjects = [row[0] for row in cursor.fetchall()]
            
            if subjects:
                return subjects
        
        # If no subjects found in primary table, try the teacher_subjects table
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='teacher_subjects'
        """)
        
        if cursor.fetchone():
            # Try to get subjects from teacher_subjects table
            cursor.execute("""
                SELECT s.subject_name
                FROM teacher_subjects ts
                JOIN subjects s ON ts.subject_id = s.subject_id
                WHERE ts.teacher_name = ?
                ORDER BY s.subject_name
            """, (username,))
            
            subjects = [row[0] for row in cursor.fetchall()]
            
            if subjects:
                return subjects
        
        # If we get here, no subjects found in either table
        return []
        
    except Exception as e:
        print(f"Error in get_teacher_subjects: {e}")
        return []
    finally:
        conn.close()

def get_all_subjects():
    """Get all subjects from database"""
    conn = sqlite3.connect(DATABASE_PATH)
    query = "SELECT * FROM subjects ORDER BY subject_name"
    
    try:
        df = pd.read_sql(query, conn)
    except:
        df = pd.DataFrame(columns=['subject_id', 'subject_name', 'course_code'])
    
    conn.close()
    return df

def assign_subject_to_teacher(teacher_username, subject_id):
    """Assign a subject to a teacher"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if this assignment already exists
        teacher_column = 'teacher_name'
        
        # Check column name first
        execute_query("PRAGMA table_info(teacher_subjects)")
        columns = [col[1] for col in cursor.fetchall()]
        if teacher_column not in columns:
            if 'teacher_username' in columns:
                teacher_column = 'teacher_username'
            elif 'username' in columns:
                teacher_column = 'username'
            elif 'teacher' in columns:
                teacher_column = 'teacher'
        
        # Check for existing assignment
        cursor.execute(f"SELECT id FROM teacher_subjects WHERE {teacher_column} = ? AND subject_id = ?",
                     (teacher_username, subject_id))
        exists = cursor.fetchone()
        
        if not exists:
            # Create new assignment
            cursor.execute(f"INSERT INTO teacher_subjects (subject_id, {teacher_column}) VALUES (?, ?)",
                         (subject_id, teacher_username))
            conn.commit()
            return True, "Subject assigned successfully"
        else:
            return False, "This subject is already assigned to this teacher"
    
    except Exception as e:
        conn.rollback()
        return False, f"Error assigning subject: {e}"
    finally:
        conn.close()
