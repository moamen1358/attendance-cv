"""
Script to create three basic users with password '123':
- Admin
- Professor
- Student
"""
import sqlite3
import os
from datetime import datetime
from pathlib import Path

# Database path
DATABASE_PATH = Path('attendance_system.db')

def create_users():
    """Create basic users with simple passwords"""
    # Connect to database
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # Ensure tables exist
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
        
        # Create users with plain text passwords
        users = [
            ("admin", "123", "admin"),
            ("professor", "123", "professor"),
            ("student", "123", "student")
        ]
        
        for username, password, role in users:
            # Add or update user
            cursor.execute("SELECT id FROM user_accounts WHERE username = ?", (username,))
            user = cursor.fetchone()
            
            if user:
                # Update existing user
                cursor.execute(
                    "UPDATE user_accounts SET password = ? WHERE username = ?", 
                    (password, username)
                )
                print(f"Updated existing user: {username}")
            else:
                # Create new user
                cursor.execute(
                    "INSERT INTO user_accounts (username, password, role) VALUES (?, ?, ?)",
                    (username, password, role)
                )
                print(f"Created new user: {username}")
            
            # Create profile for student
            if role == "student":
                cursor.execute(
                    "INSERT OR REPLACE INTO student_profiles (username, name, student_id, section) VALUES (?, ?, ?, ?)",
                    (username, f"{username.capitalize()} User", username.upper(), "Default Section")
                )
                
            # Create profile for professor
            elif role == "professor":
                cursor.execute(
                    "INSERT OR REPLACE INTO professor_profiles (username, name, department) VALUES (?, ?, ?)",
                    (username, f"Prof. {username.capitalize()}", "Computer Science")
                )
        
        # Commit changes
        conn.commit()
        print("\nUsers created successfully:")
        print("1. Username: admin, Password: 123, Role: admin")  
        print("2. Username: professor, Password: 123, Role: professor")
        print("3. Username: student, Password: 123, Role: student")
        
    except Exception as e:
        conn.rollback()
        print(f"Error creating users: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    create_users()
