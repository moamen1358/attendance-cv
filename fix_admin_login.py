"""
Direct fix for admin login issues.
This script directly verifies and fixes the admin user in the database.
"""
import sqlite3
import os
from pathlib import Path

def fix_admin_login():
    print("Starting direct admin login fix...")
    
    # Find database file - check both in current directory and project root
    db_paths = [
        Path('attendance_system.db'),  # Current directory
        Path('/home/invisa/Desktop/my_grad_streamlit/attendance_system.db')  # Full path
    ]
    
    db_path = None
    for path in db_paths:
        if path.exists():
            db_path = path
            print(f"Found database at: {db_path}")
            break
    
    if not db_path:
        print("Database not found. Creating a new one.")
        db_path = Path('attendance_system.db')
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if user_accounts table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_accounts'")
        if not cursor.fetchone():
            print("Creating user_accounts table...")
            cursor.execute('''
            CREATE TABLE user_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL,
                last_login TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
        
        # Create or update admin user - DIRECT APPROACH
        cursor.execute("DELETE FROM user_accounts WHERE username = 'admin'")
        cursor.execute(
            "INSERT INTO user_accounts (username, password, role) VALUES ('admin', '123', 'admin')"
        )
        
        print("Admin user recreated with username='admin' and password='123'")
        
        # Verify admin user
        cursor.execute("SELECT username, password FROM user_accounts WHERE username = 'admin'")
        result = cursor.fetchone()
        if result:
            print(f"Verified admin user: username={result[0]}, password={result[1]}")
        else:
            print("WARNING: Admin user verification failed!")
        
        # Commit changes
        conn.commit()
        print("\nAdmin login fix successful!")
        print("You can now log in with:")
        print("Username: admin")
        print("Password: 123")
        
    except Exception as e:
        conn.rollback()
        print(f"Error fixing admin login: {e}")
        import traceback
        print(traceback.format_exc())
    finally:
        conn.close()

if __name__ == "__main__":
    fix_admin_login()
