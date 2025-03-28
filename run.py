import streamlit as st
import os
import sys
import sqlite3

# Make sure the application directory is in the path
app_dir = os.path.dirname(os.path.abspath(__file__))
if app_dir not in sys.path:
    sys.path.append(app_dir)

def initialize_database():
    """Ensure all required tables exist"""
    db_path = 'attendance_system.db'
    print(f"Initializing database at: {os.path.abspath(db_path)}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Create student_profiles table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS student_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            student_id TEXT UNIQUE,
            password TEXT NOT NULL,
            section TEXT,
            email TEXT,
            phone TEXT,
            last_login TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # See if we need to add a default student account
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_accounts'")
        if cursor.fetchone():
            cursor.execute("SELECT COUNT(*) FROM user_accounts WHERE role='student'")
            if cursor.fetchone()[0] == 0:
                # Add default student to user_accounts
                cursor.execute('''
                INSERT INTO user_accounts (username, password, role)
                VALUES ('student', 'student123', 'student')
                ''')
                
                # Add corresponding profile
                cursor.execute('''
                INSERT INTO student_profiles (username, name, student_id, password, section)
                VALUES ('student', 'Default Student', 'STU001', 'student123', 'A')
                ''')
                
                print("Added default student account")
        
        # Commit changes
        conn.commit()
        print("Database initialization complete")
        
    except Exception as e:
        print(f"Error initializing database: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    # Initialize database first
    initialize_database()
    
    # Then import and run the main file (not app.py directly)
    os.system(f"{sys.executable} -m streamlit run {os.path.join(app_dir, 'src', 'main.py')}")
