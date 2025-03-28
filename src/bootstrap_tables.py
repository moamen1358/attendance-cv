import sqlite3
import os
from src.database_sync import sync_user_tables

def bootstrap_essential_tables():
    """Create and sync all essential database tables"""
    conn = sqlite3.connect('attendance_system.db')
    cursor = conn.cursor()
    
    try:
        # Create user_accounts table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            last_login TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create student_profiles table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS student_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            student_id TEXT UNIQUE,
            section TEXT,
            email TEXT,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (username) REFERENCES user_accounts(username)
        )
        ''')
        
        # Create professor_profiles table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS professor_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            department TEXT,
            email TEXT,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (username) REFERENCES user_accounts(username)
        )
        ''')
        
        # Make sure we have a default admin account
        cursor.execute('''
        INSERT OR IGNORE INTO user_accounts (username, password, role)
        VALUES ('admin', 'admin', 'admin')
        ''')
        
        # Commit changes
        conn.commit()
        
        # Now sync all tables to ensure consistency
        sync_user_tables()
        
        print("Essential tables bootstrapped successfully")
        return True
    
    except Exception as e:
        conn.rollback()
        print(f"Error bootstrapping tables: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    # Run bootstrap if executed directly
    bootstrap_essential_tables()
