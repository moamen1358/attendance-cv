"""
Emergency script to fix login issues.

This script:
1. Verifies the database structure
2. Ensures user_accounts table exists with proper columns
3. Creates default users with password "123"
"""
import sqlite3
from pathlib import Path
import os
import sys

def fix_login_issues():
    """Fix login issues by ensuring database and users exist"""
    print("Emergency Login Fix - Starting...")
    
    # Database path
    db_path = Path('attendance_system.db')
    
    # Connect to database or create it
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. Ensure user_accounts table exists with basic structure
        print("Checking user_accounts table...")
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
        
        # 2. Check if basic profiles exist
        print("Ensuring profile tables exist...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS student_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            name TEXT,
            student_id TEXT,
            section TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS professor_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            name TEXT,
            department TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 3. Create default users if they don't exist
        print("Creating default users...")
        default_users = [
            ('admin', '123', 'admin'),
            ('professor', '123', 'professor'),
            ('student', '123', 'student')
        ]
        
        for username, password, role in default_users:
            # Check if user exists
            cursor.execute("SELECT id FROM user_accounts WHERE username = ?", (username,))
            if cursor.fetchone() is None:
                # Create user
                cursor.execute(
                    "INSERT INTO user_accounts (username, password, role) VALUES (?, ?, ?)",
                    (username, password, role)
                )
                print(f"Created user: {username}")
                
                # Create profile if student or professor
                if role == 'student':
                    cursor.execute(
                        "INSERT OR IGNORE INTO student_profiles (username, name, student_id, section) VALUES (?, ?, ?, ?)",
                        (username, f"{username.title()} User", username.upper(), "Default")
                    )
                elif role == 'professor':
                    cursor.execute(
                        "INSERT OR IGNORE INTO professor_profiles (username, name, department) VALUES (?, ?, ?)",
                        (username, f"Prof. {username.title()}", "Computer Science")
                    )
            else:
                # Update password to ensure it's '123'
                cursor.execute("UPDATE user_accounts SET password = ? WHERE username = ?", (password, username))
                print(f"Reset password for user: {username}")
        
        # 4. Commit changes
        conn.commit()
        
        print("\nLogin fix complete!")
        print("You can now log in with these credentials:")
        print("- Admin: username='admin', password='123'")
        print("- Professor: username='professor', password='123'")
        print("- Student: username='student', password='123'")
        
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"Error fixing login: {e}")
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    fix_login_issues()
