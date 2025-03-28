import sqlite3
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATABASE_PATH = 'attendance_system.db'

def fix_duplicate_student_records():
    """
    Fix duplicate records in student_profiles table and enforce unique constraints
    """
    print(f"Fixing duplicate records in database: {os.path.abspath(DATABASE_PATH)}")
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # Step 1: Check for duplicates in the student_profiles table
        print("Checking for duplicate student records...")
        cursor.execute("""
        SELECT username, student_id, name, COUNT(*) as count
        FROM student_profiles
        GROUP BY username, student_id, name
        HAVING count > 1
        """)
        
        duplicates = cursor.fetchall()
        if duplicates:
            print(f"Found {len(duplicates)} groups of duplicate records")
            
            # Step 2: Create a temporary table with the structure we want
            print("Creating temporary table with proper constraints...")
            cursor.execute("""
            CREATE TABLE student_profiles_clean (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                name TEXT,
                student_id TEXT UNIQUE,
                section TEXT,
                email TEXT,
                phone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # Step 3: Copy over unique records to the new table
            print("Copying unique records to new table...")
            cursor.execute("""
            INSERT OR IGNORE INTO student_profiles_clean (username, name, student_id, section, email, phone)
            SELECT DISTINCT username, name, student_id, section, email, phone
            FROM student_profiles
            """)
            
            # Step 4: Drop the old table and rename the new one
            print("Replacing old table with clean version...")
            cursor.execute("DROP TABLE student_profiles")
            cursor.execute("ALTER TABLE student_profiles_clean RENAME TO student_profiles")
            
            # Step 5: Add indexes for better performance
            print("Adding indexes for performance...")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_student_profiles_username ON student_profiles(username)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_student_profiles_student_id ON student_profiles(student_id)")
            
            # Check the result
            cursor.execute("SELECT COUNT(*) FROM student_profiles")
            new_count = cursor.fetchone()[0]
            print(f"Cleaned student_profiles table now has {new_count} unique records")
            
        else:
            print("No duplicates found in student_profiles table")
            
            # Still need to make sure constraints are enforced
            print("Adding unique constraints to prevent future duplicates...")
            try:
                # Create a temporary table with constraints
                cursor.execute("""
                CREATE TABLE student_profiles_temp (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    name TEXT,
                    student_id TEXT UNIQUE,
                    section TEXT,
                    email TEXT,
                    phone TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)
                
                # Copy all data
                cursor.execute("""
                INSERT OR IGNORE INTO student_profiles_temp 
                SELECT * FROM student_profiles
                """)
                
                # Replace old table
                cursor.execute("DROP TABLE student_profiles")
                cursor.execute("ALTER TABLE student_profiles_temp RENAME TO student_profiles")
                
                # Add indexes
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_student_profiles_username ON student_profiles(username)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_student_profiles_student_id ON student_profiles(student_id)")
            except sqlite3.OperationalError as e:
                print(f"Table already has constraints: {e}")
        
        # Fix attendance records to reference correct student names
        print("Checking attendance records for consistency...")
        
        # Check if attendance_records table has a student_name column
        try:
            cursor.execute("PRAGMA table_info(attendance_records)")
            columns = [col[1].lower() for col in cursor.fetchall()]
            
            # If we have both name and student_name columns, ensure they're consistent
            if 'name' in columns and 'student_name' in columns:
                cursor.execute("UPDATE attendance_records SET student_name = name WHERE student_name != name")
                print("Synchronized name and student_name columns in attendance_records")
                
            # If we have name but not student_name, add student_name column
            elif 'name' in columns and 'student_name' not in columns:
                cursor.execute("ALTER TABLE attendance_records ADD COLUMN student_name TEXT")
                cursor.execute("UPDATE attendance_records SET student_name = name")
                print("Added student_name column to attendance_records")
        except Exception as e:
            print(f"Error checking attendance_records table: {e}")
        
        # Commit all changes
        conn.commit()
        print("Database cleanup completed successfully")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"Error cleaning up database: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    fix_duplicate_student_records()
    print("\nRun this script to clean up duplicate student profiles and prevent future duplicates.")
    print("Command: python scripts/fix_duplicate_records.py")
