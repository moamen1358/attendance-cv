import streamlit as st
import pandas as pd
import sqlite3
from database_utils import execute_query, execute_query_df

DATABASE_PATH = 'attendance_system.db'

def create_or_update_schema():
    """Create or update the teacher_subjects table schema to ensure consistency"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if table exists and what columns it has
        execute_query("PRAGMA table_info(teacher_subjects)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if not columns:
            # Table doesn't exist - create it
            cursor.execute('''
            CREATE TABLE teacher_subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id INTEGER,
                teacher_name TEXT,
                FOREIGN KEY (subject_id) REFERENCES subjects(subject_id)
            )
            ''')
            conn.commit()
            print("Created teacher_subjects table")
        elif 'teacher_name' not in column_names:
            # Table exists but needs migration - check for possible columns
            teacher_column = None
            for possible_col in ['teacher', 'teacher_username', 'username', 'professor']:
                if possible_col in column_names:
                    teacher_column = possible_col
                    break
            
            # Create updated table
            cursor.execute('''
            CREATE TABLE teacher_subjects_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id INTEGER,
                teacher_name TEXT,
                FOREIGN KEY (subject_id) REFERENCES subjects(subject_id)
            )
            ''')
            
            # Migrate data if we found a matching column
            if teacher_column and 'subject_id' in column_names:
                cursor.execute(f'''
                INSERT INTO teacher_subjects_new (subject_id, teacher_name)
                SELECT subject_id, {teacher_column} FROM teacher_subjects
                ''')
            
            # Replace tables
            cursor.execute("DROP TABLE teacher_subjects")
            cursor.execute("ALTER TABLE teacher_subjects_new RENAME TO teacher_subjects")
            conn.commit()
            print(f"Migrated teacher_subjects table (old field: {teacher_column})")
        
    except Exception as e:
        conn.rollback()
        print(f"Error in teacher_subjects schema update: {e}")
    finally:
        conn.close()

# Initialize schema when the module is imported
create_or_update_schema()

def get_teacher_subjects(username):
    """Get subjects taught by a specific teacher"""
    conn = sqlite3.connect(DATABASE_PATH)
    
    try:
        # First check the column name for teacher
        cursor = conn.cursor()
        execute_query("PRAGMA table_info(teacher_subjects)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Determine the teacher column name
        teacher_column = 'teacher_name'
        if teacher_column not in columns:
            if 'teacher_username' in columns:
                teacher_column = 'teacher_username'
            elif 'username' in columns:
                teacher_column = 'username'
            elif 'teacher' in columns:
                teacher_column = 'teacher'
            else:
                # If we can't find a suitable column, return empty DataFrame
                return pd.DataFrame(columns=['subject_id', 'subject_name'])
        
        # Get subjects using JOIN with subjects table
        query = f"""
        SELECT s.subject_id, s.subject_name
        FROM subjects s
        JOIN teacher_subjects ts ON s.subject_id = ts.subject_id
        WHERE ts.{teacher_column} = ?
        ORDER BY s.subject_name
        """
        df = pd.read_sql(query, conn, params=(username,))
        return df
    
    except Exception as e:
        st.error(f"Error retrieving teacher subjects: {e}")
        # Return empty DataFrame with expected structure
        return pd.DataFrame(columns=['subject_id', 'subject_name'])
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
