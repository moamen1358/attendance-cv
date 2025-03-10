import sqlite3
import pandas as pd

# Constants
DATABASE_PATH = 'attendance_system.db'

def setup_teacher_subjects_table():
    """Create the teacher_subjects table to link teachers with their subjects"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Create table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS teacher_subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        teacher_username TEXT NOT NULL,
        subject TEXT NOT NULL,
        UNIQUE(teacher_username, subject)
    )
    ''')
    
    # Add some sample data if the table is empty
    cursor.execute("SELECT COUNT(*) FROM teacher_subjects")
    count = cursor.fetchone()[0]
    
    if count == 0:
        # Get existing subjects from control_4 table
        cursor.execute("SELECT DISTINCT subject FROM control_4 WHERE subject != ''")
        subjects = [row[0] for row in cursor.fetchall()]
        
        # Get existing admin users
        cursor.execute("SELECT username FROM users WHERE role = 'admin'")
        teachers = [row[0] for row in cursor.fetchall()]
        
        if teachers and subjects:
            # Assign subjects to teachers - for now, we'll just distribute them
            # In a real system, you would have a UI for this
            assignments = []
            for i, teacher in enumerate(teachers):
                # Assign 1-3 subjects to each teacher
                for j in range(min(3, len(subjects))):
                    subject_index = (i + j) % len(subjects)
                    assignments.append((teacher, subjects[subject_index]))
            
            # Insert the assignments
            cursor.executemany(
                "INSERT OR IGNORE INTO teacher_subjects (teacher_username, subject) VALUES (?, ?)",
                assignments
            )
            print(f"Added {len(assignments)} teacher-subject assignments")
        else:
            print("No teachers or subjects found to create sample data")
    
    conn.commit()
    conn.close()
    print("Teacher subjects table setup complete")

def get_teacher_subjects(username):
    """Get the subjects assigned to a specific teacher"""
    conn = sqlite3.connect(DATABASE_PATH)
    query = "SELECT subject FROM teacher_subjects WHERE teacher_username = ?"
    df = pd.read_sql(query, conn, params=(username,))
    conn.close()
    
    if df.empty:
        return []
    return df['subject'].tolist()

def assign_subject_to_teacher(teacher_username, subject):
    """Assign a subject to a teacher"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT OR IGNORE INTO teacher_subjects (teacher_username, subject) VALUES (?, ?)",
            (teacher_username, subject)
        )
        conn.commit()
        success = True
    except:
        conn.rollback()
        success = False
    
    conn.close()
    return success

def remove_subject_from_teacher(teacher_username, subject):
    """Remove a subject assignment from a teacher"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "DELETE FROM teacher_subjects WHERE teacher_username = ? AND subject = ?",
            (teacher_username, subject)
        )
        conn.commit()
        success = True
    except:
        conn.rollback()
        success = False
    
    conn.close()
    return success

if __name__ == "__main__":
    setup_teacher_subjects_table()
