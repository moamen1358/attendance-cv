#!/usr/bin/env python3
"""
Database Restructure Script with Sample Data

This script creates a proper relational database structure for the academic attendance system
and populates it with sample data using Egyptian names.
"""

import sqlite3
import json
from datetime import datetime, date, timedelta
import hashlib
import random

DATABASE_PATH = 'attendance_system.db'

def hash_password(password):
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_connection():
    """Create database connection"""
    return sqlite3.connect(DATABASE_PATH)

def clear_all_data():
    """Clear all existing data from tables"""
    conn = create_connection()
    cursor = conn.cursor()
    
    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = cursor.fetchall()
    
    # Disable foreign key constraints temporarily
    cursor.execute("PRAGMA foreign_keys = OFF")
    
    # Clear all tables
    for table in tables:
        table_name = table[0]
        try:
            cursor.execute(f"DELETE FROM {table_name}")
            print(f"✅ Cleared data from {table_name}")
        except Exception as e:
            print(f"⚠️ Could not clear {table_name}: {e}")
    
    # Re-enable foreign key constraints
    cursor.execute("PRAGMA foreign_keys = ON")
    
    conn.commit()
    conn.close()

def create_enhanced_tables():
    """Create enhanced tables with proper relationships"""
    conn = create_connection()
    cursor = conn.cursor()
    
    # Enable foreign key constraints
    cursor.execute("PRAGMA foreign_keys = ON")
    
    # 1. Academic Terms
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS academic_terms (
            term_id INTEGER PRIMARY KEY AUTOINCREMENT,
            term_name TEXT NOT NULL UNIQUE,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            is_active BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 2. Departments
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS departments (
            department_id INTEGER PRIMARY KEY AUTOINCREMENT,
            department_code TEXT NOT NULL UNIQUE,
            department_name TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 3. Enhanced Subjects
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subjects_enhanced (
            subject_id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_code TEXT NOT NULL UNIQUE,
            subject_name TEXT NOT NULL,
            description TEXT,
            credits INTEGER DEFAULT 3,
            department_id INTEGER,
            academic_year INTEGER CHECK (academic_year IN (1, 2, 3, 4)),
            semester INTEGER CHECK (semester IN (1, 2)),
            is_required BOOLEAN DEFAULT 1,
            prerequisites TEXT, -- JSON array of prerequisite subject_ids
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (department_id) REFERENCES departments(department_id)
        )
    """)
    
    # 4. Enhanced Student Profiles
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS student_profiles_enhanced (
            student_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            student_number TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE,
            phone TEXT,
            department_id INTEGER,
            academic_year INTEGER CHECK (academic_year IN (1, 2, 3, 4)),
            current_semester INTEGER CHECK (current_semester IN (1, 2)),
            enrollment_date DATE DEFAULT (DATE('now')),
            status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'graduated', 'suspended')),
            gpa REAL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (department_id) REFERENCES departments(department_id)
        )
    """)
    
    # 5. Student Subject Enrollments
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS student_enrollments (
            enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            term_id INTEGER NOT NULL,
            enrollment_date DATE DEFAULT (DATE('now')),
            status TEXT DEFAULT 'enrolled' CHECK (status IN ('enrolled', 'dropped', 'completed')),
            grade TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES student_profiles_enhanced(student_id),
            FOREIGN KEY (subject_id) REFERENCES subjects_enhanced(subject_id),
            FOREIGN KEY (term_id) REFERENCES academic_terms(term_id),
            UNIQUE(student_id, subject_id, term_id)
        )
    """)
    
    # 6. Enhanced User Accounts
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_accounts_enhanced (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('student', 'professor', 'admin')),
            student_id INTEGER,
            professor_id INTEGER,
            is_active BOOLEAN DEFAULT 1,
            last_login TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES student_profiles_enhanced(student_id),
            FOREIGN KEY (professor_id) REFERENCES professor_profiles(id)
        )
    """)
    
    # 7. Class Schedules Enhanced
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS class_schedules_enhanced (
            schedule_id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER NOT NULL,
            professor_id INTEGER,
            term_id INTEGER NOT NULL,
            section TEXT DEFAULT 'A',
            day_of_week INTEGER CHECK (day_of_week BETWEEN 0 AND 6), -- 0=Sunday, 6=Saturday
            start_time TIME NOT NULL,
            end_time TIME NOT NULL,
            room TEXT,
            session_type TEXT DEFAULT 'lecture' CHECK (session_type IN ('lecture', 'lab', 'tutorial')),
            max_students INTEGER DEFAULT 50,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (subject_id) REFERENCES subjects_enhanced(subject_id),
            FOREIGN KEY (professor_id) REFERENCES professor_profiles(id),
            FOREIGN KEY (term_id) REFERENCES academic_terms(term_id)
        )
    """)
    
    # 8. Attendance Records Enhanced
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance_records_enhanced (
            attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            schedule_id INTEGER,
            attendance_date DATE NOT NULL,
            check_in_time TIMESTAMP,
            status TEXT DEFAULT 'present' CHECK (status IN ('present', 'absent', 'late', 'excused')),
            method TEXT DEFAULT 'facial_recognition' CHECK (method IN ('manual', 'facial_recognition', 'qr_code')),
            confidence_score REAL DEFAULT 1.0,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES student_profiles_enhanced(student_id),
            FOREIGN KEY (subject_id) REFERENCES subjects_enhanced(subject_id),
            FOREIGN KEY (schedule_id) REFERENCES class_schedules_enhanced(schedule_id)
        )
    """)
    
    # 9. Facial Recognition Data
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS facial_embeddings (
            embedding_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            embedding_data TEXT NOT NULL, -- JSON array of facial embedding
            confidence_threshold REAL DEFAULT 0.6,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES student_profiles_enhanced(student_id)
        )
    """)
    
    conn.commit()
    conn.close()
    print("✅ Enhanced database tables created successfully")

def insert_sample_data():
    """Insert sample data with Egyptian names"""
    conn = create_connection()
    cursor = conn.cursor()
    
    # 1. Academic Terms
    terms = [
        ('Fall 2024', '2024-09-01', '2025-01-15', True),
        ('Spring 2025', '2025-02-01', '2025-06-15', False),
        ('Summer 2025', '2025-07-01', '2025-08-30', False)
    ]
    
    for term_name, start_date, end_date, is_active in terms:
        cursor.execute("""
            INSERT OR REPLACE INTO academic_terms (term_name, start_date, end_date, is_active)
            VALUES (?, ?, ?, ?)
        """, (term_name, start_date, end_date, is_active))
    
    # 2. Departments
    departments = [
        ('CS', 'Computer Science', 'Department of Computer Science and Information Technology'),
        ('EE', 'Electrical Engineering', 'Department of Electrical and Electronics Engineering'),
        ('ME', 'Mechanical Engineering', 'Department of Mechanical Engineering'),
        ('CE', 'Civil Engineering', 'Department of Civil Engineering'),
        ('IS', 'Information Systems', 'Department of Information Systems'),
        ('AI', 'Artificial Intelligence', 'Department of Artificial Intelligence and Data Science')
    ]
    
    for dept_code, dept_name, description in departments:
        cursor.execute("""
            INSERT OR REPLACE INTO departments (department_code, department_name, description)
            VALUES (?, ?, ?)
        """, (dept_code, dept_name, description))
    
    # 3. Subjects by Department and Year
    subjects_data = [
        # Computer Science - Year 1
        ('CS101', 'Introduction to Programming', 'Basic programming concepts using Python', 3, 'CS', 1, 1),
        ('CS102', 'Computer Fundamentals', 'Basic computer architecture and systems', 3, 'CS', 1, 1),
        ('MATH101', 'Calculus I', 'Differential and integral calculus', 4, 'CS', 1, 1),
        ('ENG101', 'English Communication', 'Academic English and technical writing', 2, 'CS', 1, 1),
        
        ('CS103', 'Data Structures', 'Arrays, linked lists, stacks, queues', 3, 'CS', 1, 2),
        ('CS104', 'Object-Oriented Programming', 'OOP concepts and implementation', 3, 'CS', 1, 2),
        ('MATH102', 'Calculus II', 'Advanced calculus and applications', 4, 'CS', 1, 2),
        ('PHYS101', 'Physics I', 'Mechanics and thermodynamics', 3, 'CS', 1, 2),
        
        # Computer Science - Year 2
        ('CS201', 'Algorithms and Complexity', 'Algorithm design and analysis', 3, 'CS', 2, 1),
        ('CS202', 'Database Systems', 'Database design and SQL', 3, 'CS', 2, 1),
        ('CS203', 'Computer Networks', 'Network protocols and architecture', 3, 'CS', 2, 1),
        ('MATH201', 'Discrete Mathematics', 'Logic, sets, and graph theory', 3, 'CS', 2, 1),
        
        ('CS204', 'Software Engineering', 'Software development lifecycle', 3, 'CS', 2, 2),
        ('CS205', 'Operating Systems', 'OS concepts and implementation', 3, 'CS', 2, 2),
        ('CS206', 'Web Development', 'HTML, CSS, JavaScript, and frameworks', 3, 'CS', 2, 2),
        ('STAT201', 'Statistics', 'Probability and statistical analysis', 3, 'CS', 2, 2),
        
        # Computer Science - Year 3
        ('CS301', 'Machine Learning', 'ML algorithms and applications', 3, 'CS', 3, 1),
        ('CS302', 'Computer Graphics', '2D and 3D graphics programming', 3, 'CS', 3, 1),
        ('CS303', 'Cybersecurity', 'Information security principles', 3, 'CS', 3, 1),
        ('CS304', 'Mobile App Development', 'iOS and Android development', 3, 'CS', 3, 1),
        
        # AI Department
        ('AI101', 'Introduction to AI', 'Basic AI concepts and history', 3, 'AI', 1, 1),
        ('AI201', 'Neural Networks', 'Deep learning and neural networks', 3, 'AI', 2, 1),
        ('AI301', 'Natural Language Processing', 'Text processing and understanding', 3, 'AI', 3, 1),
        ('AI302', 'Computer Vision', 'Image processing and recognition', 3, 'AI', 3, 1),
    ]
    
    # Get department IDs
    dept_map = {}
    cursor.execute("SELECT department_id, department_code FROM departments")
    for dept_id, dept_code in cursor.fetchall():
        dept_map[dept_code] = dept_id
    
    for subject_code, subject_name, description, credits, dept_code, academic_year, semester in subjects_data:
        cursor.execute("""
            INSERT OR REPLACE INTO subjects_enhanced 
            (subject_code, subject_name, description, credits, department_id, academic_year, semester)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (subject_code, subject_name, description, credits, dept_map[dept_code], academic_year, semester))
    
    # 4. Sample Students with Egyptian Names
    egyptian_students = [
        # Computer Science Students
        ('mohamed_ali', 'Mohamed Ali Hassan', 'CS2024001', 'mohamed.ali@university.edu', '01123456789', 'CS', 1, 1),
        ('fatma_ahmed', 'Fatma Ahmed Mohamed', 'CS2024002', 'fatma.ahmed@university.edu', '01123456790', 'CS', 1, 1),
        ('omar_hassan', 'Omar Hassan Ibrahim', 'CS2024003', 'omar.hassan@university.edu', '01123456791', 'CS', 1, 1),
        ('sara_mohamed', 'Sara Mohamed Abdel Rahman', 'CS2024004', 'sara.mohamed@university.edu', '01123456792', 'CS', 1, 1),
        ('ahmed_ibrahim', 'Ahmed Ibrahim Mahmoud', 'CS2024005', 'ahmed.ibrahim@university.edu', '01123456793', 'CS', 1, 1),
        
        ('yasmin_khaled', 'Yasmin Khaled Farouk', 'CS2023001', 'yasmin.khaled@university.edu', '01123456794', 'CS', 2, 1),
        ('kareem_mostafa', 'Kareem Mostafa Salah', 'CS2023002', 'kareem.mostafa@university.edu', '01123456795', 'CS', 2, 1),
        ('dina_saeed', 'Dina Saeed Abdel Aziz', 'CS2023003', 'dina.saeed@university.edu', '01123456796', 'CS', 2, 1),
        ('youssef_nabil', 'Youssef Nabil Farid', 'CS2023004', 'youssef.nabil@university.edu', '01123456797', 'CS', 2, 1),
        ('nour_ahmed', 'Nour Ahmed Taha', 'CS2023005', 'nour.ahmed@university.edu', '01123456798', 'CS', 2, 1),
        
        ('hassan_omar', 'Hassan Omar Abdel Hamid', 'CS2022001', 'hassan.omar@university.edu', '01123456799', 'CS', 3, 1),
        ('menna_ali', 'Menna Ali Mostafa', 'CS2022002', 'menna.ali@university.edu', '01123456800', 'CS', 3, 1),
        ('moamen_ghareeb', 'Moamen Ghareeb Mohamed', 'CS2022003', 'moamen.ghareeb@university.edu', '01123456801', 'CS', 3, 1),
        
        # AI Department Students
        ('mahmoud_yasser', 'Mahmoud Yasser Fahmy', 'AI2024001', 'mahmoud.yasser@university.edu', '01123456802', 'AI', 1, 1),
        ('heba_mohamed', 'Heba Mohamed Zaki', 'AI2024002', 'heba.mohamed@university.edu', '01123456803', 'AI', 1, 1),
        ('tamer_farouk', 'Tamer Farouk Abdel Latif', 'AI2023001', 'tamer.farouk@university.edu', '01123456804', 'AI', 2, 1),
        ('salma_hassan', 'Salma Hassan Mahmoud', 'AI2022001', 'salma.hassan@university.edu', '01123456805', 'AI', 3, 1),
    ]
    
    for username, name, student_number, email, phone, dept_code, academic_year, semester in egyptian_students:
        cursor.execute("""
            INSERT OR REPLACE INTO student_profiles_enhanced 
            (username, name, student_number, email, phone, department_id, academic_year, current_semester)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (username, name, student_number, email, phone, dept_map[dept_code], academic_year, semester))
    
    # 5. Create User Accounts for Students
    cursor.execute("SELECT student_id, username, name FROM student_profiles_enhanced")
    students = cursor.fetchall()
    
    for student_id, username, name in students:
        # Generate password: firstname_lastname123
        name_parts = name.split()
        first_name = name_parts[0].lower()
        last_name = name_parts[-1].lower() if len(name_parts) > 1 else "user"
        password = f"{first_name}_{last_name}123"
        hashed_password = hash_password(password)
        
        cursor.execute("""
            INSERT OR REPLACE INTO user_accounts_enhanced 
            (username, password, role, student_id)
            VALUES (?, ?, 'student', ?)
        """, (username, hashed_password, student_id))
    
    # 6. Auto-enroll students in appropriate subjects
    cursor.execute("SELECT student_id, department_id, academic_year, current_semester FROM student_profiles_enhanced")
    students = cursor.fetchall()
    
    cursor.execute("SELECT term_id FROM academic_terms WHERE is_active = 1")
    active_term_id = cursor.fetchone()[0]
    
    for student_id, dept_id, academic_year, current_semester in students:
        # Get subjects for this student's department, year, and semester
        cursor.execute("""
            SELECT subject_id FROM subjects_enhanced 
            WHERE department_id = ? AND academic_year = ? AND semester = ?
        """, (dept_id, academic_year, current_semester))
        
        subjects = cursor.fetchall()
        
        for (subject_id,) in subjects:
            cursor.execute("""
                INSERT OR REPLACE INTO student_enrollments 
                (student_id, subject_id, term_id, status)
                VALUES (?, ?, ?, 'enrolled')
            """, (student_id, subject_id, active_term_id))
    
    # 7. Create Class Schedules
    schedule_data = [
        # CS101 - Introduction to Programming
        (1, None, 1, 'A', 0, '09:00', '10:30', 'Lab-1', 'lecture'),  # Sunday
        (1, None, 1, 'A', 2, '09:00', '10:30', 'Lab-1', 'lab'),      # Tuesday
        
        # CS102 - Computer Fundamentals  
        (2, None, 1, 'A', 1, '11:00', '12:30', 'Room-101', 'lecture'), # Monday
        (2, None, 1, 'A', 3, '11:00', '12:30', 'Room-101', 'tutorial'), # Wednesday
        
        # CS201 - Algorithms
        (9, None, 1, 'A', 0, '13:00', '14:30', 'Room-201', 'lecture'), # Sunday
        (9, None, 1, 'A', 2, '13:00', '14:30', 'Lab-2', 'lab'),        # Tuesday
        
        # AI101 - Introduction to AI
        (25, None, 1, 'A', 1, '09:00', '10:30', 'AI-Lab', 'lecture'),  # Monday
        (25, None, 1, 'A', 4, '09:00', '10:30', 'AI-Lab', 'lab'),      # Thursday
    ]
    
    for subject_id, professor_id, term_id, section, day_of_week, start_time, end_time, room, session_type in schedule_data:
        cursor.execute("""
            INSERT OR REPLACE INTO class_schedules_enhanced 
            (subject_id, professor_id, term_id, section, day_of_week, start_time, end_time, room, session_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (subject_id, professor_id, term_id, section, day_of_week, start_time, end_time, room, session_type))
    
    # 8. Generate Sample Attendance Records
    cursor.execute("""
        SELECT se.student_id, se.subject_id, sp.username, sp.name 
        FROM student_enrollments se
        JOIN student_profiles_enhanced sp ON se.student_id = sp.student_id
        WHERE se.status = 'enrolled'
    """)
    enrollments = cursor.fetchall()
    
    # Generate attendance for last 30 days
    start_date = datetime.now().date() - timedelta(days=30)
    
    for student_id, subject_id, username, name in enrollments:
        for i in range(30):
            attendance_date = start_date + timedelta(days=i)
            
            # Skip weekends (Friday=4, Saturday=5 in Python's weekday())
            if attendance_date.weekday() in [4, 5]:
                continue
            
            # Random attendance (90% chance of being present)
            status = 'present' if random.random() < 0.9 else 'absent'
            
            if status == 'present':
                # Random check-in time between 9:00 and 14:00
                hour = random.randint(9, 14)
                minute = random.randint(0, 59)
                check_in_time = datetime.combine(attendance_date, datetime.min.time().replace(hour=hour, minute=minute))
                confidence = round(random.uniform(0.7, 0.99), 2)
            else:
                check_in_time = None
                confidence = 0.0
            
            cursor.execute("""
                INSERT OR REPLACE INTO attendance_records_enhanced 
                (student_id, subject_id, attendance_date, check_in_time, status, confidence_score)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (student_id, subject_id, attendance_date, check_in_time, status, confidence))
    
    # 9. Generate Sample Facial Embeddings (dummy data)
    cursor.execute("SELECT student_id FROM student_profiles_enhanced")
    students = cursor.fetchall()
    
    for (student_id,) in students:
        # Generate dummy facial embedding (128-dimensional vector)
        dummy_embedding = [round(random.uniform(-1, 1), 4) for _ in range(128)]
        embedding_json = json.dumps(dummy_embedding)
        
        cursor.execute("""
            INSERT OR REPLACE INTO facial_embeddings 
            (student_id, embedding_data, confidence_threshold)
            VALUES (?, ?, 0.6)
        """, (student_id, embedding_json))
    
    conn.commit()
    conn.close()
    print("✅ Sample data inserted successfully")

def create_views_and_indexes():
    """Create helpful views and indexes"""
    conn = create_connection()
    cursor = conn.cursor()
    
    # View: Student Dashboard
    cursor.execute("""
        CREATE VIEW IF NOT EXISTS v_student_dashboard AS
        SELECT 
            sp.student_id,
            sp.username,
            sp.name,
            sp.student_number,
            sp.email,
            d.department_name,
            sp.academic_year,
            sp.current_semester,
            sp.gpa,
            COUNT(DISTINCT se.subject_id) as enrolled_subjects,
            AVG(CASE WHEN ar.status = 'present' THEN 1.0 ELSE 0.0 END) * 100 as overall_attendance_percentage
        FROM student_profiles_enhanced sp
        JOIN departments d ON sp.department_id = d.department_id
        LEFT JOIN student_enrollments se ON sp.student_id = se.student_id AND se.status = 'enrolled'
        LEFT JOIN attendance_records_enhanced ar ON sp.student_id = ar.student_id
        GROUP BY sp.student_id
    """)
    
    # View: Subject Enrollment Summary
    cursor.execute("""
        CREATE VIEW IF NOT EXISTS v_subject_enrollment AS
        SELECT 
            s.subject_id,
            s.subject_code,
            s.subject_name,
            s.credits,
            d.department_name,
            s.academic_year,
            s.semester,
            COUNT(se.student_id) as enrolled_count,
            AVG(CASE WHEN ar.status = 'present' THEN 1.0 ELSE 0.0 END) * 100 as avg_attendance_rate
        FROM subjects_enhanced s
        JOIN departments d ON s.department_id = d.department_id
        LEFT JOIN student_enrollments se ON s.subject_id = se.subject_id AND se.status = 'enrolled'
        LEFT JOIN attendance_records_enhanced ar ON s.subject_id = ar.subject_id
        GROUP BY s.subject_id
    """)
    
    # View: Student Attendance Summary
    cursor.execute("""
        CREATE VIEW IF NOT EXISTS v_student_attendance_summary AS
        SELECT 
            sp.student_id,
            sp.username,
            sp.name,
            s.subject_code,
            s.subject_name,
            COUNT(ar.attendance_id) as total_sessions,
            SUM(CASE WHEN ar.status = 'present' THEN 1 ELSE 0 END) as present_sessions,
            SUM(CASE WHEN ar.status = 'absent' THEN 1 ELSE 0 END) as absent_sessions,
            ROUND(
                (SUM(CASE WHEN ar.status = 'present' THEN 1.0 ELSE 0.0 END) / COUNT(ar.attendance_id)) * 100, 2
            ) as attendance_percentage
        FROM student_profiles_enhanced sp
        JOIN student_enrollments se ON sp.student_id = se.student_id
        JOIN subjects_enhanced s ON se.subject_id = s.subject_id
        LEFT JOIN attendance_records_enhanced ar ON sp.student_id = ar.student_id AND s.subject_id = ar.subject_id
        WHERE se.status = 'enrolled'
        GROUP BY sp.student_id, s.subject_id
    """)
    
    # Create useful indexes
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_student_dept_year ON student_profiles_enhanced(department_id, academic_year)",
        "CREATE INDEX IF NOT EXISTS idx_subject_dept_year ON subjects_enhanced(department_id, academic_year, semester)",
        "CREATE INDEX IF NOT EXISTS idx_enrollment_student_subject ON student_enrollments(student_id, subject_id)",
        "CREATE INDEX IF NOT EXISTS idx_attendance_student_date ON attendance_records_enhanced(student_id, attendance_date)",
        "CREATE INDEX IF NOT EXISTS idx_attendance_subject_date ON attendance_records_enhanced(subject_id, attendance_date)",
        "CREATE INDEX IF NOT EXISTS idx_schedule_subject_day ON class_schedules_enhanced(subject_id, day_of_week)",
    ]
    
    for index_sql in indexes:
        cursor.execute(index_sql)
    
    conn.commit()
    conn.close()
    print("✅ Views and indexes created successfully")

def migration_compatibility():
    """Create compatibility views for existing code"""
    conn = create_connection()
    cursor = conn.cursor()
    
    # Compatibility view for attendance_records
    cursor.execute("""
        CREATE VIEW IF NOT EXISTS attendance_records_compat AS
        SELECT 
            ar.attendance_id as id,
            sp.username as student_username,
            sp.name,
            ar.subject_id,
            ar.check_in_time as timestamp,
            ar.status,
            ar.attendance_date as class_date,
            sp.name as student_name,
            sp.username,
            ar.confidence_score as confidence,
            'facial_recognition' as device_id,
            CAST(strftime('%w', ar.attendance_date) AS INTEGER) as day_of_week
        FROM attendance_records_enhanced ar
        JOIN student_profiles_enhanced sp ON ar.student_id = sp.student_id
    """)
    
    # Compatibility view for student_profiles
    cursor.execute("""
        CREATE VIEW IF NOT EXISTS student_profiles_compat AS
        SELECT 
            student_id as id,
            username,
            name,
            student_number as student_id,
            email,
            phone,
            CASE 
                WHEN current_semester = 1 THEN 'Section A'
                WHEN current_semester = 2 THEN 'Section B'
                ELSE 'Section A'
            END as section,
            created_at,
            academic_year,
            current_semester
        FROM student_profiles_enhanced
    """)
    
    # Compatibility view for subjects
    cursor.execute("""
        CREATE VIEW IF NOT EXISTS subjects_compat AS
        SELECT 
            subject_id as id,
            subject_name as name,
            description,
            subject_code as course_code,
            credits as credit_hours,
            created_at
        FROM subjects_enhanced
    """)
    
    conn.commit()
    conn.close()
    print("✅ Compatibility views created successfully")

def main():
    """Main execution function"""
    print("🚀 Starting Database Restructure with Sample Data...")
    print("⚠️ WARNING: This will clear all existing data!")
    
    # Uncomment the next line if you want to proceed without confirmation
    # response = 'y'
    response = input("Do you want to continue? (y/N): ").lower().strip()
    
    if response != 'y':
        print("❌ Operation cancelled")
        return
    
    try:
        # Step 1: Clear existing data
        print("\n📝 Step 1: Clearing existing data...")
        clear_all_data()
        
        # Step 2: Create enhanced tables
        print("\n📝 Step 2: Creating enhanced database structure...")
        create_enhanced_tables()
        
        # Step 3: Insert sample data
        print("\n📝 Step 3: Inserting sample data with Egyptian names...")
        insert_sample_data()
        
        # Step 4: Create views and indexes
        print("\n📝 Step 4: Creating views and indexes...")
        create_views_and_indexes()
        
        # Step 5: Create compatibility layer
        print("\n📝 Step 5: Creating compatibility layer...")
        migration_compatibility()
        
        print("\n🎉 Database restructure completed successfully!")
        print("\n📊 Summary:")
        
        # Print summary
        conn = create_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM student_profiles_enhanced")
        student_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM subjects_enhanced")
        subject_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM student_enrollments")
        enrollment_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM attendance_records_enhanced")
        attendance_count = cursor.fetchone()[0]
        
        print(f"✅ Students created: {student_count}")
        print(f"✅ Subjects created: {subject_count}")
        print(f"✅ Enrollments created: {enrollment_count}")
        print(f"✅ Attendance records created: {attendance_count}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error during database restructure: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
