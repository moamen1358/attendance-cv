"""
Reset users script.

This script removes all existing user data and creates
three new users: one student, one professor, and one admin.
"""
import sqlite3
import os
from pathlib import Path
import sys

# Ensure we can import from the project
sys.path.insert(0, str(Path(__file__).parent))

# Database path
DATABASE_PATH = Path('attendance_system.db')

def ensure_table_schema():
    """Ensure the tables have the correct schema"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # First create user_accounts table if it doesn't exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_accounts'")
        if not cursor.fetchone():
            print("Creating user_accounts table...")
            cursor.execute("""
            CREATE TABLE user_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL,
                last_login TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
        # Check if professor_profiles table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='professor_profiles'")
        if not cursor.fetchone():
            # Create professor_profiles table
            print("Creating professor_profiles table...")
            cursor.execute("""
            CREATE TABLE professor_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                password TEXT NOT NULL,
                department TEXT,
                email TEXT,
                phone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
        else:
            # Check columns to detect actual schema
            cursor.execute("PRAGMA table_info(professor_profiles)")
            columns = [col[1].lower() for col in cursor.fetchall()]
            print(f"Professor profiles columns: {columns}")
            
            if 'department' not in columns:
                print("Adding department column to professor_profiles table...")
                cursor.execute("ALTER TABLE professor_profiles ADD COLUMN department TEXT")
            
            if 'email' not in columns:
                print("Adding email column to professor_profiles table...")
                cursor.execute("ALTER TABLE professor_profiles ADD COLUMN email TEXT")

        # Check if student_profiles table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='student_profiles'")
        if not cursor.fetchone():
            # Create student_profiles table
            print("Creating student_profiles table...")
            cursor.execute("""
            CREATE TABLE student_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                password TEXT NOT NULL,
                student_id TEXT,
                section TEXT,
                email TEXT,
                phone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
        
        conn.commit()
        print("Schema validated successfully")
        return True
    except Exception as e:
        conn.rollback()
        print(f"Error ensuring schema: {e}")
        return False
    finally:
        conn.close()

def reset_users():
    """Reset users in the database"""
    print(f"Connecting to database: {DATABASE_PATH.absolute()}")
    
    # First ensure the schema is correct
    if not ensure_table_schema():
        print("Failed to validate schema, aborting user reset")
        return
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        print("Starting transaction...")
        conn.execute("BEGIN TRANSACTION")
        
        # Delete all existing user data
        print("Removing existing user data...")
        cursor.execute("DELETE FROM user_accounts")
        try:
            cursor.execute("DELETE FROM student_profiles")
        except sqlite3.OperationalError:
            print("Note: student_profiles table doesn't exist yet")
        
        try:
            cursor.execute("DELETE FROM professor_profiles")
        except sqlite3.OperationalError:
            print("Note: professor_profiles table doesn't exist yet")
        
        # Create the admin user - EXACT password here is critical!
        print("Creating admin user...")
        cursor.execute("""
        INSERT INTO user_accounts (username, password, role)
        VALUES ('admin', 'admin', 'admin')
        """)
        
        # Create the professor user - EXACT password here is critical!
        print("Creating professor user...")
        cursor.execute("""
        INSERT INTO user_accounts (username, password, role)
        VALUES ('professor', 'professor', 'professor')
        """)
        
        # Create the student user - EXACT password here is critical!
        print("Creating student user...")
        cursor.execute("""
        INSERT INTO user_accounts (username, password, role)
        VALUES ('student', 'student', 'student')
        """)
        
        # Check the required columns for professor_profiles
        cursor.execute("PRAGMA table_info(professor_profiles)")
        columns = [column_info[1] for column_info in cursor.fetchall()]
        needs_password = 'password' in columns
        
        # Add professor profile with correct columns including password if required
        try:
            if needs_password:
                cursor.execute("""
                INSERT INTO professor_profiles (username, name, password, department, email)
                VALUES ('professor', 'John Smith', 'professor', 'Computer Science', 'prof@example.edu')
                """)
            else:
                cursor.execute("""
                INSERT INTO professor_profiles (username, name, department, email)
                VALUES ('professor', 'John Smith', 'Computer Science', 'prof@example.edu')
                """)
            print("Added professor profile")
        except sqlite3.OperationalError as e:
            print(f"Note: Couldn't add professor profile: {e}")
        
        # Check the required columns for student_profiles
        cursor.execute("PRAGMA table_info(student_profiles)")
        columns = [column_info[1] for column_info in cursor.fetchall()]
        needs_password = 'password' in columns
        
        # Add student profile with correct columns including password if required
        try:
            if needs_password:
                cursor.execute("""
                INSERT INTO student_profiles (username, name, password, student_id, section)
                VALUES ('student', 'Jane Doe', 'student', 'S12345', 'A')
                """)
            else:
                cursor.execute("""
                INSERT INTO student_profiles (username, name, student_id, section)
                VALUES ('student', 'Jane Doe', 'S12345', 'A')
                """)
            print("Added student profile")
        except sqlite3.OperationalError as e:
            print(f"Note: Couldn't add student profile: {e}")
        
        # Commit the transaction
        conn.commit()
        print("\n✅ Users reset successfully!")
        print("\nNew user credentials:")
        print("--------------------")
        print("Admin:     username: admin     password: admin")
        print("Professor: username: professor password: professor")
        print("Student:   username: student   password: student")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error resetting users: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    reset_users()
