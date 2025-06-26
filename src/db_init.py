"""
Centralized Database Initialization Script
This script contains CREATE TABLE statements for the implemented attendance system tables.
This matches the actual database schema currently in use.
All other modules should import and call initialize_database() instead of creating tables directly.
"""

import sqlite3
import os
from datetime import datetime

# Database configuration
DATABASE_PATH = 'attendance_system.db'

def initialize_database():
    """
    Initialize all required tables for the attendance system.
    This is the ONLY place where CREATE TABLE statements should exist in active code.
    Creates only the tables that are actually implemented and in use.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        print(f"[{datetime.now()}] Initializing database tables...")
        
        # Enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # 1. Enhanced Students table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS students_enhanced (
            student_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            roll_number TEXT UNIQUE NOT NULL,
            email TEXT,
            phone TEXT,
            department TEXT,
            year INTEGER,
            section TEXT,
            enrollment_date DATE DEFAULT (date('now')),
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 2. Enhanced Subjects table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS subjects_enhanced (
            subject_id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_name TEXT NOT NULL,
            course_code TEXT UNIQUE,
            credit_hours INTEGER DEFAULT 3,
            description TEXT,
            department TEXT,
            semester INTEGER,
            year INTEGER,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 3. Enhanced Teachers table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS teachers_enhanced (
            teacher_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            employee_id TEXT UNIQUE,
            email TEXT,
            phone TEXT,
            department TEXT,
            specialization TEXT,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 4. Enhanced Teacher-Subject assignments
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS teacher_subjects_enhanced (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER,
            subject_id INTEGER,
            academic_year TEXT,
            semester TEXT,
            section TEXT,
            assigned_date DATE DEFAULT (date('now')),
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (teacher_id) REFERENCES teachers_enhanced(teacher_id),
            FOREIGN KEY (subject_id) REFERENCES subjects_enhanced(subject_id),
            UNIQUE(teacher_id, subject_id, academic_year, semester, section)
        )
        ''')
        
        # 5. Enhanced Class Schedules table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS class_schedules_enhanced (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER,
            teacher_id INTEGER,
            day_of_week TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            room_number TEXT,
            class_type TEXT DEFAULT 'lecture',
            section TEXT,
            academic_year TEXT,
            semester TEXT,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (subject_id) REFERENCES subjects_enhanced(subject_id),
            FOREIGN KEY (teacher_id) REFERENCES teachers_enhanced(teacher_id)
        )
        ''')
        
        # 6. Enhanced Attendance Records table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance_records_enhanced (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            subject_id INTEGER,
            teacher_id INTEGER,
            attendance_date DATE NOT NULL,
            attendance_time TIME DEFAULT (time('now')),
            status TEXT NOT NULL CHECK (status IN ('present', 'absent', 'late', 'excused')),
            marked_by TEXT,
            notes TEXT,
            academic_year TEXT,
            semester TEXT,
            section TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students_enhanced(student_id),
            FOREIGN KEY (subject_id) REFERENCES subjects_enhanced(subject_id),
            FOREIGN KEY (teacher_id) REFERENCES teachers_enhanced(teacher_id)
        )
        ''')
        
        # 7. Enhanced Student Profiles (for face recognition)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS student_profiles_enhanced (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            profile_name TEXT,
            encoding_data BLOB,
            image_path TEXT,
            confidence_threshold REAL DEFAULT 0.6,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students_enhanced(student_id)
        )
        ''')
        
        # 8. Enhanced User Authentication table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users_enhanced (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT,
            full_name TEXT,
            role TEXT NOT NULL CHECK (role IN ('admin', 'teacher', 'student')),
            linked_id INTEGER,
            last_login TIMESTAMP,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 9. Enhanced Attendance Sessions table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance_sessions_enhanced (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER,
            teacher_id INTEGER,
            session_date DATE NOT NULL,
            start_time TIME,
            end_time TIME,
            session_type TEXT DEFAULT 'lecture',
            location TEXT,
            notes TEXT,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (subject_id) REFERENCES subjects_enhanced(subject_id),
            FOREIGN KEY (teacher_id) REFERENCES teachers_enhanced(teacher_id)
        )
        ''')
        
        # 10. Enhanced Student Enrollments table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS student_enrollments_enhanced (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            subject_id INTEGER,
            academic_year TEXT,
            semester TEXT,
            enrollment_date DATE DEFAULT (date('now')),
            status TEXT DEFAULT 'enrolled',
            grade TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students_enhanced(student_id),
            FOREIGN KEY (subject_id) REFERENCES subjects_enhanced(subject_id),
            UNIQUE(student_id, subject_id, academic_year, semester)
        )
        ''')
        
        # 11. Departments table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS departments (
            department_id INTEGER PRIMARY KEY,
            department_code TEXT,
            department_name TEXT,
            head_name TEXT,
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create views (these exist in the actual database)
        cursor.execute('''
        CREATE VIEW IF NOT EXISTS attendance_with_names AS
            SELECT 
                ar.*,
                COALESCE(ar.name, ar.username, ar.student_username) AS student_name
            FROM attendance_records ar
        ''')
        
        cursor.execute('''
        CREATE VIEW IF NOT EXISTS student_profiles AS 
            SELECT * FROM student_profiles_enhanced
        ''')
        
        cursor.execute('''
        CREATE VIEW IF NOT EXISTS student_profiles_view AS 
            SELECT * FROM student_profiles_enhanced
        ''')
        
        # Create indexes for better performance (matching actual database indexes)
        indexes = [
            # Core attendance indexes
            "CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance_records_enhanced(attendance_date)",
            "CREATE INDEX IF NOT EXISTS idx_attendance_student ON attendance_records_enhanced(student_id)",
            "CREATE INDEX IF NOT EXISTS idx_attendance_subject ON attendance_records_enhanced(subject_id)",
            
            # Student and user indexes
            "CREATE INDEX IF NOT EXISTS idx_student_roll ON students_enhanced(roll_number)",
            "CREATE INDEX IF NOT EXISTS idx_subject_code ON subjects_enhanced(course_code)",
            "CREATE INDEX IF NOT EXISTS idx_teacher_employee ON teachers_enhanced(employee_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_username ON users_enhanced(username)"
        ]
        
        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
            except Exception as idx_error:
                print(f"Warning: Could not create index: {idx_error}")
        
        conn.commit()
        print(f"[{datetime.now()}] Database tables initialized successfully!")
        
        # Return table information for verification
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"Tables created: {[table[0] for table in tables]}")
        
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"[{datetime.now()}] Error initializing database: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()

def check_database_integrity():
    """Check if all required tables exist and have the correct structure"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Only check for tables that actually exist in the database
    required_tables = [
        'students_enhanced',
        'subjects_enhanced', 
        'teachers_enhanced',
        'teacher_subjects_enhanced',
        'class_schedules_enhanced',
        'attendance_records_enhanced',
        'student_profiles_enhanced',
        'users_enhanced',
        'attendance_sessions_enhanced',
        'student_enrollments_enhanced',
        'departments'
    ]
    
    try:
        missing_tables = []
        for table in required_tables:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
            if not cursor.fetchone():
                missing_tables.append(table)
        
        if missing_tables:
            print(f"Missing tables: {missing_tables}")
            return False
        else:
            print("All required tables exist")
            return True
            
    except Exception as e:
        print(f"Error checking database integrity: {e}")
        return False
    finally:
        conn.close()

def get_table_info(table_name):
    """Get detailed information about a specific table"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        return columns
    except Exception as e:
        print(f"Error getting table info for {table_name}: {e}")
        return []
    finally:
        conn.close()

if __name__ == "__main__":
    # Initialize database when run directly
    success = initialize_database()
    if success:
        check_database_integrity()
    else:
        print("Database initialization failed!")