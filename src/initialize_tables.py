import sqlite3
import os
import streamlit as st

DATABASE_PATH = 'attendance_system.db'

def initialize_student_profiles():
    """
    Ensure student_profiles table exists in the database.
    Call this function early in the application startup.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    tables_created = False
    
    try:
        # Check if student_profiles table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='student_profiles'")
        if not cursor.fetchone():
            print("Creating student_profiles table...")
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
            tables_created = True
            
            # Add a default student if none exists
            cursor.execute("SELECT COUNT(*) FROM user_accounts WHERE role='student'")
            if cursor.fetchone()[0] == 0:
                # Add a default student to user_accounts
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
        
        conn.commit()
        return tables_created
    except Exception as e:
        print(f"Error initializing student_profiles table: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    # Can be run directly to initialize tables
    if initialize_student_profiles():
        print("Student profiles table created successfully")
    else:
        print("Student profiles table already exists or there was an error")
