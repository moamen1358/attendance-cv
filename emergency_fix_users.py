"""
Emergency script to add/fix default users in the database.
Run this if you're having login issues.
"""
import sqlite3
import os
from pathlib import Path

def fix_users():
    """Fix or add default users with password '123'"""
    print("Adding emergency users...")
    
    db_path = Path('attendance_system.db')
    
    # Connect to database
    conn = sqlite3.connect(db_path)
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
            email TEXT,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Check professor_profiles table columns
        cursor.execute("PRAGMA table_info(professor_profiles)")
        prof_columns = [col[1] for col in cursor.fetchall()]
        
        # Check student_profiles table columns
        cursor.execute("PRAGMA table_info(student_profiles)")
        student_columns = [col[1] for col in cursor.fetchall()]
        
        print(f"Available professor_profiles columns: {', '.join(prof_columns)}")
        print(f"Available student_profiles columns: {', '.join(student_columns)}")
        
        # Force add default users with password "123"
        accounts = [
            ('admin', '123', 'admin'),
            ('professor', '123', 'professor'),
            ('student', '123', 'student'),
        ]
        
        for username, password, role in accounts:
            # Add or update user
            cursor.execute(
                "INSERT OR REPLACE INTO user_accounts (username, password, role) VALUES (?, ?, ?)",
                (username, password, role)
            )
            print(f"Added/updated user: {username}")
            
            # Add profile for student - use dynamic columns approach
            if role == 'student':
                # Create column string and values for the INSERT statement
                col_str = "username, name, student_id, section"
                values = (username, f"{username.capitalize()} User", username.upper(), "Default")
                
                # Add password if it exists and is required
                if 'password' in student_columns:
                    col_str += ", password"
                    values += (password,)
                
                # Add email if it exists
                if 'email' in student_columns:
                    col_str += ", email" 
                    values += (f"{username}@example.com",)
                
                # Add phone if it exists
                if 'phone' in student_columns:
                    col_str += ", phone"
                    values += (f"+1234567890",)
                
                # Execute the dynamic insert
                query = f"INSERT OR REPLACE INTO student_profiles ({col_str}) VALUES ({','.join(['?'] * len(values))})"
                cursor.execute(query, values)
                print(f"Added student profile with fields: {col_str}")
                
            # Add profile for professor - already has dynamic columns
            elif role == 'professor':
                # Create column string and values for the INSERT statement
                col_str = "username, name"
                values = (username, f"Prof. {username.capitalize()}")
                
                # Add password if it exists and is required
                if 'password' in prof_columns:
                    col_str += ", password"
                    values += (password,)
                
                # Add department if it exists
                if 'department' in prof_columns:
                    col_str += ", department"
                    values += ("Computer Science",)
                
                # Add email if it exists
                if 'email' in prof_columns:
                    col_str += ", email"
                    values += (f"{username}@example.com",)
                
                # Add phone if it exists
                if 'phone' in prof_columns:
                    col_str += ", phone"
                    values += (f"+1234567890",)
                
                # Execute the dynamic insert
                query = f"INSERT OR REPLACE INTO professor_profiles ({col_str}) VALUES ({','.join(['?'] * len(values))})"
                cursor.execute(query, values)
                print(f"Added professor profile with fields: {col_str}")
                
        conn.commit()
        print("\nDefault users added successfully.")
        print("You can now login with:")
        print("Admin: username=admin, password=123")
        print("Professor: username=professor, password=123")
        print("Student: username=student, password=123")
        
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
        import traceback
        print(traceback.format_exc())
    finally:
        conn.close()

if __name__ == "__main__":
    fix_users()
