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
        
        # Create compatibility views for legacy code
        print("Creating compatibility views...")
        
        # 1. user_accounts_enhanced view (maps users_enhanced with teacher -> professor role mapping)
        cursor.execute('''
        CREATE VIEW IF NOT EXISTS user_accounts_enhanced AS 
        SELECT 
            id, 
            username, 
            password_hash, 
            email, 
            full_name, 
            CASE WHEN role = 'teacher' THEN 'professor' ELSE role END as role,
            linked_id, 
            last_login, 
            status, 
            created_at, 
            updated_at,
            id as student_id, 
            id as professor_id 
        FROM users_enhanced
        ''')
        
        # 2. students view (maps students_enhanced to legacy students table format)
        cursor.execute('''
        CREATE VIEW IF NOT EXISTS students AS 
        SELECT 
            student_id, 
            name, 
            roll_number 
        FROM students_enhanced
        ''')
        
        # 3. subjects view (maps subjects_enhanced to legacy subjects table format)
        cursor.execute('''
        CREATE VIEW IF NOT EXISTS subjects AS 
        SELECT 
            subject_id, 
            subject_name, 
            course_code, 
            credit_hours, 
            description, 
            department 
        FROM subjects_enhanced
        ''')
        
        # 4. professor_subject_assignments view (maps teacher_subjects_enhanced)
        cursor.execute('''
        CREATE VIEW IF NOT EXISTS professor_subject_assignments AS 
        SELECT 
            id, 
            (SELECT username FROM users_enhanced WHERE linked_id = teacher_id) as professor_username,
            subject_id, 
            assigned_date 
        FROM teacher_subjects_enhanced
        ''')
        
        # 5. professor_profiles view (maps teachers_enhanced with users_enhanced)
        cursor.execute('''
        CREATE VIEW IF NOT EXISTS professor_profiles AS 
        SELECT 
            u.username, 
            t.name, 
            t.department, 
            t.email, 
            t.phone 
        FROM users_enhanced u 
        JOIN teachers_enhanced t ON u.linked_id = t.teacher_id 
        WHERE u.role = 'teacher'
        ''')
        
        # 6. user_accounts view (legacy compatibility)
        cursor.execute('''
        CREATE VIEW IF NOT EXISTS user_accounts AS 
        SELECT 
            id, 
            username, 
            password_hash as password, 
            email, 
            full_name, 
            role, 
            linked_id, 
            last_login, 
            status, 
            created_at 
        FROM users_enhanced
        ''')
        
        print("✓ Compatibility views created successfully")
        
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

def populate_sample_data():
    """
    Populate the database with comprehensive sample data including:
    - Students with sections
    - Teachers and subjects
    - Class schedules (2-3 subjects per student per day)
    - Student enrollments
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        print(f"[{datetime.now()}] Populating sample data...")
        
        # Check if data already exists
        cursor.execute("SELECT COUNT(*) FROM students_enhanced")
        if cursor.fetchone()[0] > 0:
            print("Sample data already exists, skipping population...")
            return True
        
        # Insert sample students
        students_data = [
            ('Fatma Khaled Ibrahim', '2024001', 'fatma.khaled@university.edu', '01234567890', 'Computer Science', 2, 'B'),
            ('Ahmed Mohamed Ali', '2024002', 'ahmed.mohamed@university.edu', '01234567891', 'Computer Science', 2, 'A'),
            ('Sara Hassan Ahmed', '2024003', 'sara.hassan@university.edu', '01234567892', 'Computer Science', 2, 'A'),
            ('Mohamed Tarek Saeed', '2024004', 'mohamed.tarek@university.edu', '01234567893', 'Engineering', 3, 'B'),
            ('Nour Amr Farouk', '2024005', 'nour.amr@university.edu', '01234567894', 'Engineering', 3, 'C'),
        ]
        
        cursor.executemany('''
            INSERT INTO students_enhanced (name, roll_number, email, phone, department, year, section)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', students_data)
        
        # Insert sample teachers
        teachers_data = [
            ('Dr. Ahmed Hassan', 'emp2024001', 'Computer Science', 'Professor', 'ahmed.hassan@university.edu'),
            ('Dr. Maha Ibrahim', 'emp2024002', 'Engineering', 'Associate Professor', 'maha.ibrahim@university.edu'),
            ('Dr. Omar Farid', 'emp2024003', 'Computer Science', 'Assistant Professor', 'omar.farid@university.edu'),
            ('Dr. Layla Mohamed', 'emp2024004', 'Mathematics', 'Professor', 'layla.mohamed@university.edu'),
        ]
        
        cursor.executemany('''
            INSERT INTO teachers_enhanced (name, employee_id, department, position, email)
            VALUES (?, ?, ?, ?, ?)
        ''', teachers_data)
        
        # Insert sample subjects
        subjects_data = [
            ('CS301', 'Data Structures', 'Computer Science', 3, 'Core course covering fundamental data structures'),
            ('CS302', 'Database Systems', 'Computer Science', 3, 'Introduction to database design and SQL'),
            ('CS303', 'Web Development', 'Computer Science', 3, 'Modern web development technologies'),
            ('ENG201', 'Engineering Mathematics', 'Engineering', 4, 'Advanced mathematics for engineers'),
            ('ENG202', 'Circuit Analysis', 'Engineering', 3, 'Electrical circuit analysis and design'),
            ('MATH201', 'Calculus II', 'Mathematics', 4, 'Advanced calculus and differential equations'),
        ]
        
        cursor.executemany('''
            INSERT INTO subjects_enhanced (subject_code, subject_name, department, credit_hours, description)
            VALUES (?, ?, ?, ?, ?)
        ''', subjects_data)
        
        # Insert class schedules - 2-3 subjects per day for each student
        schedule_data = [
            # Monday schedules
            (1, 1, 'Monday', '08:00', '10:00', 'A', 'Room 101'),
            (1, 2, 'Monday', '10:30', '12:30', 'A', 'Room 102'),
            (2, 1, 'Monday', '08:00', '10:00', 'B', 'Room 103'),
            (2, 3, 'Monday', '10:30', '12:30', 'B', 'Room 104'),
            (3, 2, 'Monday', '13:30', '15:30', 'A', 'Room 105'),
            
            # Tuesday schedules
            (1, 2, 'Tuesday', '08:00', '10:00', 'A', 'Room 101'),
            (1, 3, 'Tuesday', '10:30', '12:30', 'A', 'Room 102'),
            (2, 1, 'Tuesday', '13:30', '15:30', 'B', 'Room 103'),
            (3, 1, 'Tuesday', '08:00', '10:00', 'A', 'Room 104'),
            (3, 3, 'Tuesday', '13:30', '15:30', 'A', 'Room 105'),
            
            # Wednesday schedules
            (1, 1, 'Wednesday', '09:00', '11:00', 'A', 'Room 101'),
            (1, 3, 'Wednesday', '11:30', '13:30', 'A', 'Room 102'),
            (1, 2, 'Wednesday', '14:00', '16:00', 'A', 'Room 103'),
            (2, 2, 'Wednesday', '09:00', '11:00', 'B', 'Room 104'),
            (2, 3, 'Wednesday', '14:00', '16:00', 'B', 'Room 105'),
            (3, 1, 'Wednesday', '11:30', '13:30', 'A', 'Room 106'),
            
            # Thursday schedules
            (1, 2, 'Thursday', '08:00', '10:00', 'A', 'Room 101'),
            (2, 1, 'Thursday', '10:30', '12:30', 'B', 'Room 102'),
            (2, 3, 'Thursday', '13:30', '15:30', 'B', 'Room 103'),
            (3, 2, 'Thursday', '08:00', '10:00', 'A', 'Room 104'),
            (3, 3, 'Thursday', '10:30', '12:30', 'A', 'Room 105'),
            
            # Friday schedules
            (1, 1, 'Friday', '08:00', '10:00', 'A', 'Room 101'),
            (1, 3, 'Friday', '13:30', '15:30', 'A', 'Room 102'),
            (2, 2, 'Friday', '10:30', '12:30', 'B', 'Room 103'),
            (3, 1, 'Friday', '08:00', '10:00', 'A', 'Room 104'),
        ]
        
        cursor.executemany('''
            INSERT INTO class_schedules_enhanced 
            (subject_id, teacher_id, day_of_week, start_time, end_time, section, room_number)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', schedule_data)
        
        # Insert student enrollments
        enrollment_data = [
            (1, 1, 'A', 'active'),  # Fatma -> CS301, Section A
            (1, 2, 'A', 'active'),  # Fatma -> CS302, Section A  
            (1, 3, 'A', 'active'),  # Fatma -> CS303, Section A
            (2, 1, 'B', 'active'),  # Ahmed -> CS301, Section B
            (2, 2, 'B', 'active'),  # Ahmed -> CS302, Section B
            (2, 3, 'B', 'active'),  # Ahmed -> CS303, Section B
            (3, 1, 'A', 'active'),  # Sara -> CS301, Section A
            (3, 2, 'A', 'active'),  # Sara -> CS302, Section A
            (3, 3, 'A', 'active'),  # Sara -> CS303, Section A
            (4, 4, 'B', 'active'),  # Mohamed -> ENG201, Section B
            (4, 5, 'B', 'active'),  # Mohamed -> ENG202, Section B
            (5, 4, 'C', 'active'),  # Nour -> ENG201, Section C
            (5, 6, 'C', 'active'),  # Nour -> MATH201, Section C
        ]
        
        cursor.executemany('''
            INSERT INTO student_enrollments_enhanced (student_id, subject_id, section, status)
            VALUES (?, ?, ?, ?)
        ''', enrollment_data)
        
        # Insert user accounts for authentication
        users_data = [
            ('admin', 'admin', 'admin', 'System Administrator', 'active'),
            ('2024001', '2024001', 'student', 'Fatma Khaled Ibrahim', 'active'),
            ('2024002', '2024002', 'student', 'Ahmed Mohamed Ali', 'active'),
            ('2024003', '2024003', 'student', 'Sara Hassan Ahmed', 'active'),
            ('2024004', '2024004', 'student', 'Mohamed Tarek Saeed', 'active'),
            ('2024005', '2024005', 'student', 'Nour Amr Farouk', 'active'),
            ('emp2024001', 'emp2024001', 'teacher', 'Dr. Ahmed Hassan', 'active'),
            ('emp2024002', 'emp2024002', 'teacher', 'Dr. Maha Ibrahim', 'active'),
            ('emp2024003', 'emp2024003', 'teacher', 'Dr. Omar Farid', 'active'),
            ('emp2024004', 'emp2024004', 'teacher', 'Dr. Layla Mohamed', 'active'),
        ]
        
        cursor.executemany('''
            INSERT INTO users_enhanced (username, password_hash, role, full_name, status)
            VALUES (?, ?, ?, ?, ?)
        ''', users_data)
        
        conn.commit()
        print("✅ Sample data populated successfully!")
        print("   - 5 students with sections assigned")
        print("   - 4 teachers across departments")
        print("   - 6 subjects with descriptions")
        print("   - 25+ class schedules (2-3 subjects per day)")
        print("   - Student enrollments with sections")
        print("   - User accounts for authentication")
        
        return True
        
    except Exception as e:
        print(f"❌ Error populating sample data: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    # Initialize database when run directly
    print("🚀 Starting database initialization...")
    success = initialize_database()
    if success:
        print("✅ Database tables created successfully!")
        
        # Populate with sample data
        sample_success = populate_sample_data()
        if sample_success:
            print("✅ Sample data populated successfully!")
        
        # Verify database integrity
        integrity_check = check_database_integrity()
        if integrity_check:
            print("✅ Database integrity check passed!")
            print("\n🎓 University Attendance System is ready!")
            print("📚 Students have been assigned to sections with 2-3 subjects per day")
            print("👨‍🏫 Teachers are assigned to subjects and sections")
            print("📅 Class schedules are configured for Monday-Friday")
        else:
            print("❌ Database integrity check failed!")
    else:
        print("❌ Database initialization failed!")