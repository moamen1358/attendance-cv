import sqlite3
import pandas as pd
from datetime import datetime

# Database path
DATABASE_PATH = 'attendance_system.db'

def get_db_connection():
    """Get a connection to the SQLite database"""
    return sqlite3.connect(DATABASE_PATH)

def sync_user_tables():
    """
    Synchronize data across all user-related tables to ensure consistency.
    This ensures that users in user_accounts also exist in their respective role tables.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    changes_made = 0
    
    try:
        # First check which tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [table[0] for table in cursor.fetchall()]
        
        required_tables = {
            'user_accounts': False,
            'students': False,
            'student_profiles': False,
            'professor_profiles': False,
            'teacher_subjects': False,
            'professor_subject_assignments': False
        }
        
        # Mark which tables exist
        for table in tables:
            if table in required_tables:
                required_tables[table] = True
        
        # Create missing tables if needed
        if not required_tables.get('student_profiles', False):
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS student_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                student_id TEXT UNIQUE,
                section TEXT,
                email TEXT,
                phone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            print("Created student_profiles table")
            required_tables['student_profiles'] = True
        
        if not required_tables.get('professor_profiles', False):
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS professor_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                department TEXT,
                email TEXT,
                phone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            print("Created professor_profiles table")
            required_tables['professor_profiles'] = True
        
        # Only proceed if user_accounts table exists
        if not required_tables.get('user_accounts', False):
            print("user_accounts table doesn't exist - cannot synchronize")
            return 0
        
        # 1. Sync student accounts with student_profiles
        if required_tables.get('student_profiles', False):
            # Get all student accounts
            cursor.execute("SELECT username, password FROM user_accounts WHERE role='student'")
            students = cursor.fetchall()
            
            # For each student account, ensure they exist in student_profiles
            for student in students:
                username = student[0]
                
                # Check if student exists in profiles
                cursor.execute("SELECT 1 FROM student_profiles WHERE username=?", (username,))
                if not cursor.fetchone():
                    # Add to student_profiles with placeholder data
                    cursor.execute('''
                    INSERT INTO student_profiles 
                    (username, name, student_id, section) 
                    VALUES (?, ?, ?, ?)
                    ''', (username, username, username, 'Default'))
                    changes_made += 1
                    print(f"Added {username} to student_profiles")
            
            # For each student in student_profiles, ensure they exist in user_accounts
            cursor.execute("SELECT username FROM student_profiles")
            profile_students = cursor.fetchall()
            
            for student in profile_students:
                username = student[0]
                
                # Check if student exists in user_accounts
                cursor.execute("SELECT 1 FROM user_accounts WHERE username=?", (username,))
                if not cursor.fetchone():
                    # Add to user_accounts with default password
                    cursor.execute('''
                    INSERT INTO user_accounts 
                    (username, password, role) 
                    VALUES (?, ?, 'student')
                    ''', (username, username))  # Using username as default password
                    changes_made += 1
                    print(f"Added {username} to user_accounts as student")
        
        # 2. Sync professor accounts with professor_profiles
        if required_tables.get('professor_profiles', False):
            # Get all professor accounts
            cursor.execute("SELECT username FROM user_accounts WHERE role='professor'")
            professors = cursor.fetchall()
            
            # For each professor account, ensure they exist in professor_profiles
            for professor in professors:
                username = professor[0]
                
                # Check if professor exists in profiles
                cursor.execute("SELECT 1 FROM professor_profiles WHERE username=?", (username,))
                if not cursor.fetchone():
                    # Add to professor_profiles with placeholder data
                    cursor.execute('''
                    INSERT INTO professor_profiles 
                    (username, name, department) 
                    VALUES (?, ?, ?)
                    ''', (username, username, 'Default'))
                    changes_made += 1
                    print(f"Added {username} to professor_profiles")
            
            # For each professor in professor_profiles, ensure they exist in user_accounts
            cursor.execute("SELECT username FROM professor_profiles")
            profile_professors = cursor.fetchall()
            
            for professor in profile_professors:
                username = professor[0]
                
                # Check if professor exists in user_accounts
                cursor.execute("SELECT 1 FROM user_accounts WHERE username=?", (username,))
                if not cursor.fetchone():
                    # Add to user_accounts with default password
                    cursor.execute('''
                    INSERT INTO user_accounts 
                    (username, password, role) 
                    VALUES (?, ?, 'professor')
                    ''', (username, username))  # Using username as default password
                    changes_made += 1
                    print(f"Added {username} to user_accounts as professor")
        
        # 3. Sync teacher_subjects with professor_subject_assignments
        if required_tables.get('teacher_subjects', False) and required_tables.get('professor_subject_assignments', False):
            # Get all teacher-subject assignments
            cursor.execute("SELECT teacher_name, subject_id FROM teacher_subjects")
            teacher_subjects = cursor.fetchall()
            
            # For each teacher-subject, ensure they exist in professor_subject_assignments
            for assignment in teacher_subjects:
                teacher_name = assignment[0]
                subject_id = assignment[1]
                
                # Check if assignment exists in professor_subject_assignments
                cursor.execute(
                    "SELECT 1 FROM professor_subject_assignments WHERE professor_username=? AND subject_id=?", 
                    (teacher_name, subject_id)
                )
                if not cursor.fetchone():
                    # Add to professor_subject_assignments
                    cursor.execute('''
                    INSERT OR IGNORE INTO professor_subject_assignments 
                    (professor_username, subject_id) 
                    VALUES (?, ?)
                    ''', (teacher_name, subject_id))
                    changes_made += 1
                    print(f"Added {teacher_name} - {subject_id} to professor_subject_assignments")
            
            # For each assignment in professor_subject_assignments, ensure they exist in teacher_subjects
            cursor.execute("SELECT professor_username, subject_id FROM professor_subject_assignments")
            prof_assignments = cursor.fetchall()
            
            for assignment in prof_assignments:
                username = assignment[0]
                subject_id = assignment[1]
                
                # Check if assignment exists in teacher_subjects
                cursor.execute(
                    "SELECT 1 FROM teacher_subjects WHERE teacher_name=? AND subject_id=?", 
                    (username, subject_id)
                )
                if not cursor.fetchone():
                    # Add to teacher_subjects
                    cursor.execute('''
                    INSERT OR IGNORE INTO teacher_subjects 
                    (teacher_name, subject_id) 
                    VALUES (?, ?)
                    ''', (username, subject_id))
                    changes_made += 1
                    print(f"Added {username} - {subject_id} to teacher_subjects")
        
        # Commit all changes
        conn.commit()
        print(f"Database synchronization complete. {changes_made} changes made.")
        return changes_made
        
    except Exception as e:
        print(f"Error synchronizing tables: {e}")
        conn.rollback()
        return -1
    finally:
        conn.close()

def register_user(username, password, role, profile_data=None):
    """
    Register a new user and ensure all related tables are updated
    
    Args:
        username (str): Username for the new account 
        password (str): Password for the new account
        role (str): User role (student, professor, admin)
        profile_data (dict): Optional additional profile data like name, email, etc.
    
    Returns:
        bool: True if successful, False otherwise
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Start transaction
        cursor.execute("BEGIN")
        
        # 1. Add to user_accounts
        cursor.execute(
            "INSERT INTO user_accounts (username, password, role) VALUES (?, ?, ?)",
            (username, password, role)
        )
        
        # 2. Add to role-specific tables
        if role == 'student':
            # Extract profile data with defaults
            name = profile_data.get('name', username) if profile_data else username
            student_id = profile_data.get('student_id', username) if profile_data else username
            section = profile_data.get('section', 'Default') if profile_data else 'Default'
            email = profile_data.get('email', '') if profile_data else ''
            phone = profile_data.get('phone', '') if profile_data else ''
            
            # Add to student_profiles
            cursor.execute('''
            INSERT INTO student_profiles 
            (username, name, student_id, section, email, phone) 
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (username, name, student_id, section, email, phone))
            
            # Check if students table exists and add there too if it does
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='students'")
            if cursor.fetchone():
                cursor.execute(
                    "INSERT OR IGNORE INTO students (name, id, section) VALUES (?, ?, ?)", 
                    (name, student_id, section)
                )
        
        elif role == 'professor':
            # Extract profile data with defaults
            name = profile_data.get('name', username) if profile_data else username
            department = profile_data.get('department', 'Default') if profile_data else 'Default'
            email = profile_data.get('email', '') if profile_data else ''
            phone = profile_data.get('phone', '') if profile_data else ''
            
            # Add to professor_profiles
            cursor.execute('''
            INSERT INTO professor_profiles 
            (username, name, department, email, phone) 
            VALUES (?, ?, ?, ?, ?)
            ''', (username, name, department, email, phone))
        
        # Commit transaction
        conn.commit()
        print(f"Successfully registered {username} as {role}")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"Error registering user: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    # Run synchronization if script is executed directly
    sync_user_tables()
