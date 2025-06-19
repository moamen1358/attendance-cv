import sqlite3
from database_utils import execute_query, execute_query_df
import streamlit as st

def sync_professor_tables():
    """
    Synchronize the professor_subject_assignments and teacher_subjects tables
    to ensure compatibility between different parts of the application.
    """
    conn = sqlite3.connect('attendance_system.db')
    cursor = conn.cursor()
    
    try:
        # First, check if the tables exist and recreate if necessary
        cursor.execute("DROP TABLE IF EXISTS teacher_subjects")
        
        # Create teacher_subjects with the proper schema
        cursor.execute('''
        CREATE TABLE teacher_subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER,
            teacher_name TEXT,
            FOREIGN KEY (subject_id) REFERENCES subjects(subject_id)
        )
        ''')
        
        # Ensure professor_subject_assignments exists
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS professor_subject_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            professor_username TEXT,
            subject_id TEXT,
            assigned_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(professor_username, subject_id)
        )
        ''')
        
        # Copy data from professor_subject_assignments to teacher_subjects
        assignments = execute_query_df("""
            SELECT 
                pa.professor_username, 
                pa.subject_id
            FROM 
                professor_subject_assignments pa
        """)
        
        if not assignments.empty:
            # Insert from professor_subject_assignments into teacher_subjects
            for _, row in assignments.iterrows():
                try:
                    cursor.execute(
                        "INSERT INTO teacher_subjects (subject_id, teacher_name) VALUES (?, ?)",
                        (row['subject_id'], row['professor_username'])
                    )
                except Exception as e:
                    print(f"Error inserting assignment: {e}")
            
            print(f"Synchronized {len(assignments)} assignments to teacher_subjects table")
        
        conn.commit()
        return True, "Tables synchronized successfully"
    
    except Exception as e:
        conn.rollback()
        return False, f"Error synchronizing tables: {e}"
    
    finally:
        conn.close()

def fix_teacher_subjects_table():
    """
    Fix the teacher_subjects table by ensuring it has the correct structure
    """
    conn = sqlite3.connect('attendance_system.db')
    cursor = conn.cursor()
    
    try:
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='teacher_subjects'")
        if cursor.fetchone() is None:
            # Table doesn't exist, create it
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
        else:
            # Table exists, check its columns
            cursor.execute("PRAGMA table_info(teacher_subjects)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'teacher_name' not in columns:
                # Drop and recreate the table
                cursor.execute("DROP TABLE teacher_subjects")
                cursor.execute('''
                CREATE TABLE teacher_subjects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subject_id INTEGER,
                    teacher_name TEXT,
                    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id)
                )
                ''')
                conn.commit()
                print("Recreated teacher_subjects table with proper schema")
                
        return True, "Teacher subjects table fixed"
        
    except Exception as e:
        conn.rollback()
        return False, f"Error fixing teacher_subjects table: {e}"
        
    finally:
        conn.close()

if __name__ == "__main__":
    # Run both fixes when executed directly
    fix_teacher_subjects_table()
    sync_professor_tables()
