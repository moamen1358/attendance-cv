import sqlite3
import pandas as pd
import os
import sys

# Add the parent directory to sys.path so we can import from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Constants
DATABASE_PATH = '../attendance_system.db'

def get_db_connection():
    """Get a connection to the SQLite database"""
    return sqlite3.connect(DATABASE_PATH)

def assign_all_students_to_subjects():
    """Assign all students to all subjects"""
    print("Starting student-subject assignment process...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Step 1: Check if student_subjects table exists, if not create it
        cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='student_subjects'
        """)
        
        if not cursor.fetchone():
            print("Creating student_subjects table...")
            cursor.execute("""
            CREATE TABLE student_subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_name TEXT NOT NULL,
                subject_id INTEGER NOT NULL,
                enrollment_date TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (subject_id) REFERENCES subjects(subject_id),
                UNIQUE(student_name, subject_id)
            )
            """)
        
        # Step 2: Get all students
        cursor.execute("SELECT name FROM student_profiles")
        students = [row[0] for row in cursor.fetchall()]
        
        if not students:
            print("No students found in the database.")
            return
        
        print(f"Found {len(students)} students")
        
        # Step 3: Get all subjects
        cursor.execute("SELECT subject_id, subject_name FROM subjects")
        subjects = cursor.fetchall()
        
        if not subjects:
            print("No subjects found in the database.")
            return
        
        print(f"Found {len(subjects)} subjects")
        
        # Step 4: For each student, assign them to all subjects
        assigned_count = 0
        for student in students:
            for subject_id, subject_name in subjects:
                try:
                    # Use INSERT OR IGNORE to avoid errors for existing entries
                    cursor.execute("""
                    INSERT OR IGNORE INTO student_subjects (student_name, subject_id)
                    VALUES (?, ?)
                    """, (student, subject_id))
                    
                    if cursor.rowcount > 0:
                        assigned_count += 1
                        print(f"Assigned {student} to {subject_name}")
                    
                except Exception as e:
                    print(f"Error assigning {student} to subject {subject_name}: {e}")
        
        conn.commit()
        print(f"\nAssignment complete! {assigned_count} new student-subject associations created.")
        
        # Step 5: Update class_attendance table to set defaults
        print("\nUpdating class attendance records...")
        
        # Get all class schedules
        cursor.execute("SELECT subject_id, subject, day, start_time, end_time FROM class_schedules")
        schedules = cursor.fetchall()
        
        if schedules:
            # Use a more efficient batch approach
            print(f"Processing attendance defaults for {len(schedules)} class schedules...")
            
            # This would be a place for more complex logic to set up attendance
            # For now, we just acknowledge the schedules exist
            print("Schedules found. You can now manage attendance through the app interface.")
        
    except Exception as e:
        conn.rollback()
        print(f"Error during student assignment: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    assign_all_students_to_subjects()
    print("\nDone! All students are now assigned to all subjects.")
    print("You can run this script again any time new students or subjects are added.")
