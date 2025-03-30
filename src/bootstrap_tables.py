"""
Bootstrap Tables Module

This module initializes essential database tables on application startup.
"""
import sqlite3
import os

# Database path
DATABASE_PATH = 'attendance_system.db'

def bootstrap_essential_tables():
    """
    Ensure essential database tables exist at application startup.
    
    This function creates the necessary database tables with default schemas
    if they don't already exist.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        print("Bootstrapping essential tables...")
        
        # Create user_accounts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                role TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create student_profiles table
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
        
        # Create professor_profiles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS professor_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                name TEXT,
                password TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create attendance_records table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                username TEXT,
                student_username TEXT,
                timestamp TIMESTAMP NOT NULL,
                confidence REAL DEFAULT 1.0,
                device_id TEXT,
                day_of_week TEXT
            )
        ''')
        
        # Create login_logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS login_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                login_time TIMESTAMP,
                ip_address TEXT,
                status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create class_schedules table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS class_schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                day TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                type TEXT,
                room TEXT,
                professor TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Check if we need to add default user for testing
        cursor.execute("SELECT COUNT(*) FROM user_accounts")
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("Adding default admin user for testing...")
            cursor.execute('''
                INSERT INTO user_accounts (username, password, role)
                VALUES ('admin', 'admin', 'admin')
            ''')
        
        conn.commit()
        print("Database bootstrap completed successfully")
        
    except Exception as e:
        print(f"Error during bootstrap: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    bootstrap_essential_tables()
