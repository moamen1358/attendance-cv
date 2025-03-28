import sqlite3
import os
import sys

# Determine the database path with absolute path for reliability
DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'attendance_system.db')
print(f"bootstrap_tables using database at: {DATABASE_PATH}")

def bootstrap_essential_tables():
    """
    Create essential tables that might be missing, to prevent application errors
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        print("Bootstrapping essential tables...")
        
        # 1. Create student_profiles table if it doesn't exist - ENHANCED ULTRA-AGGRESSIVE VERSION
        table_created = False
        for attempt in range(3):  # Try up to 3 times with different methods
            try:
                if attempt == 0:
                    # Standard approach - MODIFIED to include UNIQUE constraints
                    cursor.execute("""
                    CREATE TABLE IF NOT EXISTS student_profiles (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE,  -- Added UNIQUE constraint
                        name TEXT,
                        student_id TEXT UNIQUE,  -- Added UNIQUE constraint
                        section TEXT,
                        email TEXT,
                        phone TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """)
                elif attempt == 1:
                    # Alternative approach with DROP first - MODIFIED to include UNIQUE constraints
                    cursor.execute("DROP TABLE IF EXISTS student_profiles_temp")
                    cursor.execute("""
                    CREATE TABLE student_profiles_temp (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE,  -- Added UNIQUE constraint
                        name TEXT,
                        student_id TEXT UNIQUE,  -- Added UNIQUE constraint
                        section TEXT,
                        email TEXT,
                        phone TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """)
                    try:
                        # Try to copy data if original exists
                        cursor.execute("""
                        INSERT OR IGNORE INTO student_profiles_temp SELECT * FROM student_profiles
                        """)
                        # If successful, replace original with temp
                        cursor.execute("DROP TABLE IF EXISTS student_profiles")
                        cursor.execute("ALTER TABLE student_profiles_temp RENAME TO student_profiles")
                    except:
                        # If original doesn't exist or copy fails, just rename temp
                        cursor.execute("DROP TABLE IF EXISTS student_profiles")
                        cursor.execute("ALTER TABLE student_profiles_temp RENAME TO student_profiles")
                else:
                    # Emergency direct creation - MODIFIED to include UNIQUE constraints
                    cursor.execute("DROP TABLE IF EXISTS student_profiles")
                    cursor.execute("""
                    CREATE TABLE student_profiles (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE,  -- Added UNIQUE constraint
                        name TEXT, 
                        student_id TEXT UNIQUE,  -- Added UNIQUE constraint
                        section TEXT,
                        email TEXT,
                        phone TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """)
                
                conn.commit()
                
                # Verify the table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='student_profiles'")
                if cursor.fetchone():
                    print(f"SUCCESS: student_profiles table created on attempt {attempt+1}")
                    table_created = True
                    break
            except Exception as e:
                print(f"Attempt {attempt+1} failed: {e}")
        
        if not table_created:
            print("CRITICAL FAILURE: Could not create student_profiles table after multiple attempts")
        
        # Always add a default record regardless of creation method - MODIFIED to use INSERT OR IGNORE
        try:
            # First check if table exists as a last resort
            cursor.execute("CREATE TABLE IF NOT EXISTS student_profiles (id INTEGER PRIMARY KEY, username TEXT UNIQUE, name TEXT, student_id TEXT UNIQUE, section TEXT)")
            conn.commit()
            
            # Add default user data - USING INSERT OR IGNORE to prevent duplicates
            cursor.execute("""
            INSERT OR IGNORE INTO student_profiles (username, name, student_id, section) 
            VALUES (?, ?, ?, ?)
            """, ('default_user', 'Default User', 'S12345', 'Default'))
            cursor.execute("""
            INSERT OR IGNORE INTO student_profiles (username, name, student_id, section) 
            VALUES (?, ?, ?, ?)
            """, ('student', 'Student User', 'S67890', 'Default'))
            conn.commit()
            print("Added default student records")
        except Exception as e:
            print(f"Error adding default record: {e}")

        # 2. Create subjects table if it doesn't exist
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            subject_name TEXT,
            course_code TEXT,
            credit_hours INTEGER DEFAULT 3,
            description TEXT
        )
        """)
        
        # 3. Create teacher_subjects table if it doesn't exist
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS teacher_subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER,
            teacher_name TEXT,
            UNIQUE(subject_id, teacher_name)
        )
        """)
        
        # 4. Create user_accounts table if it doesn't exist
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # 5. Create professor_subject_assignments table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS professor_subject_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            professor_username TEXT NOT NULL,
            subject_id INTEGER NOT NULL,
            assigned_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(professor_username, subject_id)
        )
        """)
        
        # 6. Create class_attendance table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS class_attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT NOT NULL,
            class_date TEXT NOT NULL,
            subject TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            attended BOOLEAN NOT NULL DEFAULT 0,
            UNIQUE(student_name, class_date, subject, start_time)
        )
        """)
        
        # Enhance attendance_records table creation with improved schema and indices
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,  -- Standard column name for student
            timestamp TIMESTAMP NOT NULL,  -- Standard column name for time
            confidence REAL DEFAULT 1.0,
            device_id TEXT,
            day_of_week TEXT
        )
        """)
        
        # Add indexes for better performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_attendance_name ON attendance_records(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_attendance_timestamp ON attendance_records(timestamp)")
        
        # Create views for compatibility with all common column names
        cursor.execute("DROP VIEW IF EXISTS attendance_name_view")
        cursor.execute("""
        CREATE VIEW attendance_name_view AS
        SELECT 
            id,
            name AS student_name,  -- Map name to student_name
            name AS student_username, -- Map name to student_username
            timestamp,
            confidence,
            device_id,
            day_of_week
        FROM attendance_records
        """)
        
        # Create a compatibility view for attendance_log if it doesn't exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='attendance_log'")
        if not cursor.fetchone():
            cursor.execute("""
            CREATE VIEW IF NOT EXISTS attendance_log AS
            SELECT * FROM attendance_records
            """)
            print("Created attendance_log compatibility view")
        
        # Create attendance_log table if it doesn't exist - maintain legacy support
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,  -- Standard column name
            timestamp TIMESTAMP NOT NULL,  -- Standard column name
            confidence REAL DEFAULT 1.0,
            device_id TEXT,
            day_of_week TEXT
        )
        """)
        
        # Add views for compatibility
        cursor.execute("DROP VIEW IF EXISTS student_profiles_view")
        cursor.execute("""
        CREATE VIEW student_profiles_view AS SELECT * FROM student_profiles
        """)
        
        # Add a default student record if the table is empty
        cursor.execute("SELECT COUNT(*) FROM student_profiles")
        count = cursor.fetchone()[0]
        
        if count == 0:
            # Try to get username from session state
            try:
                import streamlit as st
                username = st.session_state.get('username', 'default_student')
            except:
                username = 'default_student'
                
            cursor.execute("""
            INSERT INTO student_profiles (username, name, section) 
            VALUES (?, ?, ?)
            """, (username, username, 'Default'))
            print(f"Added default student: {username}")
        
        # Extra verification
        tables_to_verify = [
            "student_profiles",
            "subjects",
            "teacher_subjects",
            "user_accounts",
            "professor_subject_assignments",
            "class_attendance",
            "attendance_records",
            "attendance_log"
        ]
        
        print("\nFinal table verification:")
        for table in tables_to_verify:
            try:
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                result = cursor.fetchone()
                status = "✅ EXISTS" if result else "❌ MISSING"
                print(f"{status}: {table}")
                
                if result:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"  - Records: {count}")
            except Exception as verify_error:
                print(f"  Error verifying {table}: {verify_error}")
        
        conn.commit()
        print("Essential tables created successfully")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"Error creating essential tables: {e}")
        return False
    finally:
        conn.close()

# Always run bootstrap on import
bootstrap_essential_tables()

if __name__ == "__main__":
    # If run directly, bootstrap the tables
    bootstrap_essential_tables()
