import sqlite3
from datetime import datetime
import os

def setup_student_tables():
    """Create essential student tables if they don't exist"""
    conn = sqlite3.connect('attendance_system.db')
    cursor = conn.cursor()
    
    try:
        # Create student_profiles table with all required fields
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS student_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            username TEXT,
            student_id TEXT,
            section TEXT,
            email TEXT,
            phone TEXT,
            password TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login DATETIME
        )
        """)
        
        # Check if the table was just created (no data yet)
        cursor.execute("SELECT COUNT(*) FROM student_profiles")
        count = cursor.fetchone()[0]
        
        # Print status
        if count == 0:
            print("Created empty student_profiles table")
        else:
            print(f"Student_profiles table already exists with {count} records")
        
        # Add sample student if requested
        if count == 0:
            add_sample = input("Do you want to add a sample student profile? (y/n): ").lower()
            if add_sample == 'y' or add_sample == 'yes':
                # Insert a sample student profile
                cursor.execute("""
                INSERT OR IGNORE INTO student_profiles 
                (name, username, student_id, section, email, password)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    "sample_student",
                    "sample_student",
                    "S12345",
                    "Section 1",
                    "student@example.com",
                    "sample_student_sec1"
                ))
                
                # Also create user account for this student
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL,
                    role TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_login DATETIME
                )
                """)
                
                cursor.execute("""
                INSERT OR IGNORE INTO user_accounts 
                (username, password, role)
                VALUES (?, ?, ?)
                """, (
                    "sample_student",
                    "sample_student_sec1",
                    "student"
                ))
                
                conn.commit()
                print("Added sample student profile and user account")
            
        # Sync student_profiles with user_accounts if needed
        if count == 0:
            sync_tables = input("Do you want to sync existing students from user_accounts to student_profiles? (y/n): ").lower()
            if sync_tables == 'y' or sync_tables == 'yes':
                # Check if user_accounts table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_accounts'")
                if cursor.fetchone():
                    # Find all students in user_accounts that don't have profiles
                    cursor.execute("""
                    SELECT username FROM user_accounts 
                    WHERE role = 'student' AND 
                          username NOT IN (SELECT name FROM student_profiles)
                    """)
                    
                    students_to_add = cursor.fetchall()
                    if students_to_add:
                        for student in students_to_add:
                            username = student[0]
                            # Add basic profile for each student
                            cursor.execute("""
                            INSERT INTO student_profiles (name, username, section, password)
                            VALUES (?, ?, ?, ?)
                            """, (username, username, "Unassigned", username + "_sec1"))
                        
                        conn.commit()
                        print(f"Synced {len(students_to_add)} students from user_accounts to student_profiles")
                    else:
                        print("No students need to be synced")
                else:
                    print("user_accounts table not found, skipping sync")
        
        # Create attendance_records table if it doesn't exist
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            confidence REAL,
            device_id TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        print("Created attendance_records table if it didn't exist")
        
        # Return success
        return True
        
    except Exception as e:
        print(f"Error setting up student tables: {e}")
        conn.rollback()
        return False
    
    finally:
        conn.close()

def import_students_from_csv():
    """Import student profiles from a CSV file"""
    import pandas as pd
    
    try:
        csv_path = input("Enter the path to your CSV file: ")
        if not os.path.exists(csv_path):
            print(f"File not found: {csv_path}")
            return False
            
        # Read the CSV file
        df = pd.read_csv(csv_path)
        
        # Check required columns
        required_columns = ['name', 'section']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"CSV is missing required columns: {missing_columns}")
            print(f"Available columns: {df.columns.tolist()}")
            return False
            
        # Connect to database
        conn = sqlite3.connect('attendance_system.db')
        cursor = conn.cursor()
        
        # Insert each student
        added_count = 0
        for _, row in df.iterrows():
            try:
                # Prepare student data
                student_name = row['name']
                section = row['section'] if 'section' in df.columns else "Unassigned"
                student_id = row['student_id'] if 'student_id' in df.columns else None
                email = row['email'] if 'email' in df.columns else None
                
                # Generate default password
                password = f"{student_name}_sec{section.split()[-1] if 'Section' in section else '1'}"
                
                # Insert into student_profiles
                cursor.execute("""
                INSERT OR IGNORE INTO student_profiles 
                (name, username, student_id, section, email, password)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    student_name,
                    student_name,
                    student_id,
                    section,
                    email,
                    password
                ))
                
                # Also create user account for this student
                cursor.execute("""
                INSERT OR IGNORE INTO user_accounts 
                (username, password, role)
                VALUES (?, ?, ?)
                """, (
                    student_name,
                    password,
                    "student"
                ))
                
                added_count += 1
            except Exception as e:
                print(f"Error adding student {row.get('name', 'unknown')}: {e}")
        
        conn.commit()
        print(f"Successfully imported {added_count} students from CSV")
        return True
        
    except Exception as e:
        print(f"Error importing students: {e}")
        return False

def noninteractive_setup(add_sample=False, sync_existing=True):
    """Run setup in non-interactive mode for use in scripts"""
    conn = sqlite3.connect('attendance_system.db')
    cursor = conn.cursor()
    
    try:
        # Create student_profiles table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS student_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            username TEXT,
            student_id TEXT,
            section TEXT,
            email TEXT,
            phone TEXT,
            password TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login DATETIME
        )
        """)
        
        # Check if the table was just created (no data yet)
        cursor.execute("SELECT COUNT(*) FROM student_profiles")
        count = cursor.fetchone()[0]
        
        # Add sample student if requested and table is empty
        if count == 0 and add_sample:
            # Insert a sample student profile
            cursor.execute("""
            INSERT OR IGNORE INTO student_profiles 
            (name, username, student_id, section, email, password)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (
                "sample_student",
                "sample_student",
                "S12345",
                "Section 1",
                "student@example.com",
                "sample_student_sec1"
            ))
            
            # Also create user account for this student
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                role TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME
            )
            """)
            
            cursor.execute("""
            INSERT OR IGNORE INTO user_accounts 
            (username, password, role)
            VALUES (?, ?, ?)
            """, (
                "sample_student",
                "sample_student_sec1",
                "student"
            ))
            
            print("Added sample student profile")
        
        # Sync with user_accounts if requested
        if count == 0 and sync_existing:
            # Check if user_accounts table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_accounts'")
            if cursor.fetchone():
                # Find all students in user_accounts that don't have profiles
                cursor.execute("""
                SELECT username FROM user_accounts 
                WHERE role = 'student' AND 
                      username NOT IN (SELECT name FROM student_profiles)
                """)
                
                students_to_add = cursor.fetchall()
                if students_to_add:
                    for student in students_to_add:
                        username = student[0]
                        # Add basic profile for each student
                        cursor.execute("""
                        INSERT INTO student_profiles (name, username, section, password)
                        VALUES (?, ?, ?, ?)
                        """, (username, username, "Unassigned", username + "_sec1"))
                    
                    print(f"Synced {len(students_to_add)} students from user_accounts")
        
        # Create attendance_records table if it doesn't exist
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            confidence REAL,
            device_id TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"Error in noninteractive setup: {e}")
        conn.rollback()
        return False
    
    finally:
        conn.close()

if __name__ == "__main__":
    print("Setting up student tables...")
    if setup_student_tables():
        print("Student tables setup complete!")
        
        # Ask if user wants to import students from CSV
        import_csv = input("Would you like to import students from a CSV file? (y/n): ").lower()
        if import_csv == 'y' or import_csv == 'yes':
            import_students_from_csv()
    else:
        print("Failed to setup student tables.")
