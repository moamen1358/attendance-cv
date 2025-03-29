"""
Simple script to add a new user to the system.
"""
import sqlite3
from pathlib import Path
from src.core.security import hash_password

def add_user(username, password, role="student"):
    """Add a new user to the database"""
    # Get database path
    db_path = Path('attendance_system.db')
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # First check if user exists
        cursor.execute("SELECT username FROM user_accounts WHERE username = ?", (username,))
        if cursor.fetchone():
            print(f"User '{username}' already exists!")
            return False
            
        # Hash the password
        password_hash, salt = hash_password(password)
        
        # Insert new user - store both plain password and hash for maximum compatibility
        cursor.execute(
            "INSERT INTO user_accounts (username, password, password_hash, salt, role) VALUES (?, ?, ?, ?, ?)",
            (username, password, password_hash, salt, role)
        )
        
        # For a student, also create a student profile
        if role == "student":
            cursor.execute(
                "INSERT OR IGNORE INTO student_profiles (username, name, student_id, section) VALUES (?, ?, ?, ?)",
                (username, username, username, 'Default')
            )
        
        # For a professor, create a professor profile
        elif role == "professor":
            cursor.execute(
                "INSERT OR IGNORE INTO professor_profiles (username, name, department) VALUES (?, ?, ?)",
                (username, username, 'General')
            )
            
        conn.commit()
        print(f"Successfully added {role} '{username}' with password '{password}'")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"Error adding user: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    # Add the new user
    add_user("moamen", "123", "student")
    
    # Also add a professor with the same simple password for testing
    add_user("prof_moamen", "123", "professor")
    
    print("\nUsers created successfully. You can now log in with:")
    print("Username: moamen")
    print("Password: 123")
    print("\nOr as professor:")
    print("Username: prof_moamen")
    print("Password: 123")
