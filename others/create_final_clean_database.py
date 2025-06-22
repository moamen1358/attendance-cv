#!/usr/bin/env python3
"""
Quick Database Creation with Sample Data
"""

import sqlite3
import hashlib
from datetime import datetime, date
import json
import random

DATABASE_PATH = 'attendance_system.db'

def create_clean_database():
    """Create a clean database with sample data"""
    
    # Remove existing database
    import os
    if os.path.exists(DATABASE_PATH):
        os.remove(DATABASE_PATH)
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    print("🏗️ Creating clean database structure...")
    
    # 1. Departments
    cursor.execute('''
        CREATE TABLE departments (
            department_id INTEGER PRIMARY KEY AUTOINCREMENT,
            department_code TEXT UNIQUE NOT NULL,
            department_name TEXT NOT NULL,
            department_head TEXT,
            contact_email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 2. Academic Terms
    cursor.execute('''
        CREATE TABLE academic_terms (
            term_id INTEGER PRIMARY KEY AUTOINCREMENT,
            term_name TEXT NOT NULL,
            start_date DATE,
            end_date DATE,
            is_active BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 3. Student Profiles Enhanced
    cursor.execute('''
        CREATE TABLE student_profiles_enhanced (
            student_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            student_number TEXT UNIQUE,
            email TEXT,
            phone TEXT,
            department_id INTEGER,
            academic_year INTEGER DEFAULT 1,
            current_semester INTEGER DEFAULT 1,
            enrollment_date DATE DEFAULT (DATE('now')),
            status TEXT DEFAULT 'active',
            gpa REAL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (department_id) REFERENCES departments(department_id)
        )
    ''')
    
    # 4. User Accounts Enhanced
    cursor.execute('''
        CREATE TABLE user_accounts_enhanced (
            account_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'student',
            student_id INTEGER,
            professor_id INTEGER,
            is_active BOOLEAN DEFAULT 1,
            last_login TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES student_profiles_enhanced(student_id)
        )
    ''')
    
    # 5. Subjects Enhanced
    cursor.execute('''
        CREATE TABLE subjects_enhanced (
            subject_id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_name TEXT NOT NULL,
            course_code TEXT UNIQUE,
            credit_hours INTEGER DEFAULT 3,
            department_id INTEGER,
            academic_year INTEGER,
            semester INTEGER,
            description TEXT,
            prerequisites TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (department_id) REFERENCES departments(department_id)
        )
    ''')
    
    # 6. Student Enrollments
    cursor.execute('''
        CREATE TABLE student_enrollments (
            enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            subject_id INTEGER,
            term_id INTEGER,
            status TEXT DEFAULT 'enrolled',
            grade TEXT,
            enrollment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES student_profiles_enhanced(student_id),
            FOREIGN KEY (subject_id) REFERENCES subjects_enhanced(subject_id),
            FOREIGN KEY (term_id) REFERENCES academic_terms(term_id)
        )
    ''')
    
    # 7. Class Schedules Enhanced
    cursor.execute('''
        CREATE TABLE class_schedules_enhanced (
            schedule_id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER,
            day_of_week TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            room TEXT,
            professor_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (subject_id) REFERENCES subjects_enhanced(subject_id)
        )
    ''')
    
    # 8. Attendance Records Enhanced
    cursor.execute('''
        CREATE TABLE attendance_records_enhanced (
            record_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            subject_id INTEGER,
            class_date DATE,
            status TEXT DEFAULT 'present',
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            confidence_score REAL,
            notes TEXT,
            FOREIGN KEY (student_id) REFERENCES student_profiles_enhanced(student_id),
            FOREIGN KEY (subject_id) REFERENCES subjects_enhanced(subject_id)
        )
    ''')
    
    # 9. Facial Embeddings
    cursor.execute('''
        CREATE TABLE facial_embeddings (
            embedding_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            embedding_data TEXT NOT NULL,
            confidence_threshold REAL DEFAULT 0.6,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES student_profiles_enhanced(student_id)
        )
    ''')
    
    # 10. Professor Profiles
    cursor.execute('''
        CREATE TABLE professor_profiles (
            professor_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            department_id INTEGER,
            office_location TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (department_id) REFERENCES departments(department_id)
        )
    ''')
    
    # 11. Login Logs
    cursor.execute('''
        CREATE TABLE login_logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            role TEXT,
            login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT,
            user_agent TEXT,
            success BOOLEAN DEFAULT 1
        )
    ''')
    
    print("✅ Database structure created")
    
    # Insert sample data
    print("📊 Adding sample data...")
    
    # Departments
    departments = [
        ('CS', 'Computer Science', 'Dr. Ahmed Hassan', 'cs@university.edu'),
        ('AI', 'Artificial Intelligence', 'Dr. Fatma Ali', 'ai@university.edu'),
        ('IS', 'Information Systems', 'Dr. Mohamed Omar', 'is@university.edu'),
        ('IT', 'Information Technology', 'Dr. Sara Ahmed', 'it@university.edu'),
        ('SE', 'Software Engineering', 'Dr. Nour Hassan', 'se@university.edu'),
        ('CY', 'Cybersecurity', 'Dr. Amr Mohamed', 'cy@university.edu')
    ]
    
    for dept in departments:
        cursor.execute('''
            INSERT INTO departments (department_code, department_name, department_head, contact_email)
            VALUES (?, ?, ?, ?)
        ''', dept)
    
    # Academic Terms
    terms = [
        ('Fall 2024', '2024-09-01', '2024-12-31', 1),
        ('Spring 2025', '2025-02-01', '2025-06-30', 0),
        ('Summer 2025', '2025-07-01', '2025-08-31', 0)
    ]
    
    for term in terms:
        cursor.execute('''
            INSERT INTO academic_terms (term_name, start_date, end_date, is_active)
            VALUES (?, ?, ?, ?)
        ''', term)
    
    # Students
    students = [
        ('ahmed_hassan', 'Ahmed Hassan Mohamed', 'CS2024001', 'ahmed.hassan@student.edu', '01234567890', 1, 2, 1),
        ('fatma_ali', 'Fatma Ali Ahmed', 'CS2024002', 'fatma.ali@student.edu', '01234567891', 1, 2, 1),
        ('mohamed_omar', 'Mohamed Omar Hassan', 'AI2024001', 'mohamed.omar@student.edu', '01234567892', 2, 1, 2),
        ('sara_ahmed', 'Sara Ahmed Mohamed', 'AI2024002', 'sara.ahmed@student.edu', '01234567893', 2, 1, 2),
        ('nour_hassan', 'Nour Hassan Ali', 'IS2024001', 'nour.hassan@student.edu', '01234567894', 3, 3, 1),
        ('amr_mohamed', 'Amr Mohamed Omar', 'IS2024002', 'amr.mohamed@student.edu', '01234567895', 3, 3, 1),
        ('rana_ali', 'Rana Ali Hassan', 'IT2024001', 'rana.ali@student.edu', '01234567896', 4, 1, 1),
        ('khaled_ahmed', 'Khaled Ahmed Mohamed', 'IT2024002', 'khaled.ahmed@student.edu', '01234567897', 4, 1, 1),
        ('dina_hassan', 'Dina Hassan Omar', 'SE2024001', 'dina.hassan@student.edu', '01234567898', 5, 2, 2),
        ('omar_ali', 'Omar Ali Ahmed', 'SE2024002', 'omar.ali@student.edu', '01234567899', 5, 2, 2)
    ]
    
    for student in students:
        cursor.execute('''
            INSERT INTO student_profiles_enhanced 
            (username, name, student_number, email, phone, department_id, academic_year, current_semester)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', student)
    
    # User accounts for students
    cursor.execute("SELECT student_id, username, name FROM student_profiles_enhanced")
    students_data = cursor.fetchall()
    
    for student_id, username, name in students_data:
        # Generate password: firstname_lastname123
        name_parts = name.split()
        first_name = name_parts[0].lower()
        last_name = name_parts[-1].lower()
        password = f"{first_name}_{last_name}123"
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        cursor.execute('''
            INSERT INTO user_accounts_enhanced (username, password, role, student_id)
            VALUES (?, ?, 'student', ?)
        ''', (username, hashed_password, student_id))
    
    # Add admin account
    admin_password = hashlib.sha256('admin'.encode()).hexdigest()
    cursor.execute('''
        INSERT INTO user_accounts_enhanced (username, password, role, student_id)
        VALUES ('admin', ?, 'admin', NULL)
    ''', (admin_password,))
    
    # Subjects
    subjects = [
        ('Programming Fundamentals', 'CS101', 3, 1, 1, 1, 'Introduction to programming concepts'),
        ('Data Structures', 'CS201', 3, 1, 2, 1, 'Basic data structures and algorithms'),
        ('Database Systems', 'CS301', 3, 1, 3, 1, 'Database design and SQL'),
        ('Machine Learning Basics', 'AI101', 3, 2, 1, 1, 'Introduction to ML concepts'),
        ('Deep Learning', 'AI201', 3, 2, 2, 1, 'Neural networks and deep learning'),
        ('Computer Vision', 'AI301', 3, 2, 3, 1, 'Image processing and computer vision'),
        ('Systems Analysis', 'IS101', 3, 3, 1, 1, 'Business systems analysis'),
        ('Web Development', 'IT101', 3, 4, 1, 1, 'HTML, CSS, JavaScript'),
        ('Software Engineering', 'SE101', 3, 5, 1, 1, 'Software development methodologies'),
        ('Network Security', 'CY101', 3, 6, 1, 1, 'Cybersecurity fundamentals')
    ]
    
    for subject in subjects:
        cursor.execute('''
            INSERT INTO subjects_enhanced 
            (subject_name, course_code, credit_hours, department_id, academic_year, semester, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', subject)
    
    # Student enrollments (enroll students in subjects from their department)
    cursor.execute("SELECT student_id, department_id, academic_year, current_semester FROM student_profiles_enhanced")
    students_info = cursor.fetchall()
    
    cursor.execute("SELECT subject_id, department_id, academic_year, semester FROM subjects_enhanced")
    subjects_info = cursor.fetchall()
    
    for student_id, dept_id, year, semester in students_info:
        for subject_id, subj_dept_id, subj_year, subj_semester in subjects_info:
            if dept_id == subj_dept_id and year == subj_year and semester == subj_semester:
                cursor.execute('''
                    INSERT INTO student_enrollments (student_id, subject_id, term_id, status)
                    VALUES (?, ?, 1, 'enrolled')
                ''', (student_id, subject_id))
    
    # Class schedules
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    times = [('08:00', '09:30'), ('10:00', '11:30'), ('12:00', '13:30'), ('14:00', '15:30')]
    rooms = ['A101', 'A102', 'B201', 'B202', 'C301', 'C302']
    
    cursor.execute("SELECT subject_id, subject_name FROM subjects_enhanced")
    all_subjects = cursor.fetchall()
    
    for subject_id, subject_name in all_subjects:
        # Create 2 sessions per week for each subject
        selected_days = random.sample(days, 2)
        for day in selected_days:
            start_time, end_time = random.choice(times)
            room = random.choice(rooms)
            cursor.execute('''
                INSERT INTO class_schedules_enhanced 
                (subject_id, day_of_week, start_time, end_time, room, professor_name)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (subject_id, day, start_time, end_time, room, f'Prof. {subject_name[:10]}'))
    
    # Sample attendance records
    cursor.execute("SELECT student_id FROM student_profiles_enhanced")
    all_student_ids = [row[0] for row in cursor.fetchall()]
    
    cursor.execute("SELECT subject_id FROM subjects_enhanced")
    all_subject_ids = [row[0] for row in cursor.fetchall()]
    
    # Generate attendance for last 30 days
    for days_back in range(30):
        attendance_date = date.today().replace(day=1)  # Start of current month
        for student_id in all_student_ids[:5]:  # First 5 students
            for subject_id in all_subject_ids[:3]:  # First 3 subjects
                if random.random() > 0.2:  # 80% attendance rate
                    status = 'present' if random.random() > 0.1 else 'late'
                    cursor.execute('''
                        INSERT INTO attendance_records_enhanced 
                        (student_id, subject_id, class_date, status, confidence_score)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (student_id, subject_id, attendance_date, status, random.uniform(0.8, 0.99)))
    
    # Sample facial embeddings (mock data)
    for student_id in all_student_ids:
        # Generate a mock embedding (512 dimensions with random values)
        mock_embedding = [random.uniform(-1, 1) for _ in range(512)]
        embedding_json = json.dumps(mock_embedding)
        cursor.execute('''
            INSERT INTO facial_embeddings (student_id, embedding_data, confidence_threshold)
            VALUES (?, ?, 0.6)
        ''', (student_id, embedding_json))
    
    # Professor
    cursor.execute('''
        INSERT INTO professor_profiles (username, name, email, department_id, office_location)
        VALUES ('prof_ahmed', 'Prof. Ahmed Hassan', 'ahmed.hassan@university.edu', 1, 'Building A, Room 301')
    ''')
    
    conn.commit()
    conn.close()
    
    print("✅ Sample data added")

def verify_database():
    """Verify the database"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall() if not row[0].startswith('sqlite_')]
    
    print(f"\n📊 Database contains {len(tables)} tables:")
    
    total_records = 0
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"   📊 {table}: {count} rows")
        total_records += count
    
    print(f"✅ Total records: {total_records}")
    
    # Check consistency
    cursor.execute("SELECT COUNT(*) FROM student_profiles_enhanced")
    students = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM user_accounts_enhanced WHERE role='student'")
    accounts = cursor.fetchone()[0]
    
    print(f"✅ Students: {students}, Student accounts: {accounts-1}")  # -1 for admin
    print(f"✅ Consistency: {'PERFECT' if students == (accounts-1) else 'NEEDS REVIEW'}")
    
    conn.close()

def main():
    """Main function"""
    print("🆕 Creating Clean Database with Sample Data")
    print("=" * 45)
    
    create_clean_database()
    verify_database()
    
    print("\n🎉 Clean database created successfully!")
    print("✅ Only enhanced tables included")
    print("✅ Sample data populated")
    print("✅ Ready for use")

if __name__ == "__main__":
    main()
