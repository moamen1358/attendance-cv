#!/usr/bin/env python3
"""
Egyptian Sample Data Population Script
Populates all enhanced tables with realistic Egyptian university data.
Password = Username for easy testing
"""

import sqlite3
import random
from datetime import datetime, date, timedelta
import hashlib

# Import centralized database initialization
try:
    from src.db_init import initialize_database, check_database_integrity
except ImportError:
    import sys
    sys.path.append('src')
    from db_init import initialize_database, check_database_integrity

def hash_password(password):
    """Create a hash for passwords - using MD5 for consistency"""
    return hashlib.md5(password.encode()).hexdigest()

def populate_egyptian_data():
    """Populate all tables with Egyptian sample data"""
    
    # Initialize database first
    print("🏛️ Initializing database...")
    initialize_database()
    
    conn = sqlite3.connect('attendance_system.db')
    cursor = conn.cursor()
    
    try:
        print("🇪🇬 POPULATING EGYPTIAN UNIVERSITY DATA")
        print("=" * 50)
        
        # Clear existing data
        tables_to_clear = [
            'student_enrollments_enhanced',
            'attendance_records_enhanced', 
            'attendance_sessions_enhanced',
            'class_schedules_enhanced',
            'teacher_subjects_enhanced',
            'student_profiles_enhanced',
            'users_enhanced',
            'students_enhanced',
            'subjects_enhanced', 
            'teachers_enhanced'
        ]
        
        print("🗑️ Clearing existing data...")
        for table in tables_to_clear:
            try:
                cursor.execute(f"DELETE FROM {table}")
                print(f"   Cleared {table}")
            except sqlite3.OperationalError:
                print(f"   Table {table} not found, skipping...")
        
        # Clear departments table if it exists
        try:
            cursor.execute("DELETE FROM departments")
            print("   Cleared departments")
        except sqlite3.OperationalError:
            pass
        
        conn.commit()
        
        # 1. DEPARTMENTS
        print("\n🏢 Adding Departments...")
        departments_data = [
            ('Computer Science', 'CS', 'Study of algorithms, programming, and computational systems'),
            ('Artificial Intelligence', 'AI', 'Machine learning, neural networks, and intelligent systems'),
            ('Information Systems', 'IS', 'Business information systems and enterprise solutions'),
            ('Information Technology', 'IT', 'Network administration and technology infrastructure'),
            ('Software Engineering', 'SE', 'Software development methodologies and engineering'),
            ('Cybersecurity', 'CY', 'Information security and digital forensics')
        ]
        
        for dept in departments_data:
            try:
                cursor.execute("""
                    INSERT INTO departments (name, code, description) 
                    VALUES (?, ?, ?)
                """, dept)
            except sqlite3.OperationalError:
                # If departments table doesn't exist, skip
                pass
        
        print(f"   Added {len(departments_data)} departments")
        
        # 2. EGYPTIAN STUDENTS
        print("\n👥 Adding Egyptian Students...")
        egyptian_students = [
            ('Ahmed Mohamed Hassan', 'CS2021001', 'ahmed.mohamed.hassan@aun.edu.eg', '01012345678', 'Computer Science', 3, 'A'),
            ('Fatma Ali Ibrahim', 'CS2022002', 'fatma.ali.ibrahim@aun.edu.eg', '01023456789', 'Computer Science', 2, 'A'),
            ('Mohamed Omar Khalil', 'CS2023003', 'mohamed.omar.khalil@aun.edu.eg', '01034567890', 'Computer Science', 1, 'B'),
            ('Sara Ahmed Mahmoud', 'CS2021004', 'sara.ahmed.mahmoud@aun.edu.eg', '01045678901', 'Computer Science', 3, 'A'),
            ('Nour Hassan Farouk', 'CS2022005', 'nour.hassan.farouk@aun.edu.eg', '01056789012', 'Computer Science', 2, 'B'),
            ('Omar Ali Hassan', 'AI2021006', 'omar.ali.hassan@aun.edu.eg', '01067890123', 'Artificial Intelligence', 3, 'A'),
            ('Mariam Mostafa Ali', 'AI2022007', 'mariam.mostafa.ali@aun.edu.eg', '01078901234', 'Artificial Intelligence', 2, 'A'),
            ('Amr Khaled Mohamed', 'AI2023008', 'amr.khaled.mohamed@aun.edu.eg', '01089012345', 'Artificial Intelligence', 1, 'B'),
            ('Yasmin Ibrahim Saeed', 'IS2021009', 'yasmin.ibrahim.saeed@aun.edu.eg', '01090123456', 'Information Systems', 3, 'A'),
            ('Hassan Mohamed Omar', 'IS2022010', 'hassan.mohamed.omar@aun.edu.eg', '01001234567', 'Information Systems', 2, 'B'),
            ('Dina Ali Mahmoud', 'IT2021011', 'dina.ali.mahmoud@aun.edu.eg', '01112345678', 'Information Technology', 3, 'A'),
            ('Karim Hassan Ibrahim', 'IT2022012', 'karim.hassan.ibrahim@aun.edu.eg', '01123456789', 'Information Technology', 2, 'A'),
            ('Aya Mohamed Khalil', 'IT2023013', 'aya.mohamed.khalil@aun.edu.eg', '01134567890', 'Information Technology', 1, 'B'),
            ('Mostafa Omar Hassan', 'SE2021014', 'mostafa.omar.hassan@aun.edu.eg', '01145678901', 'Software Engineering', 3, 'A'),
            ('Rania Ali Mohamed', 'SE2022015', 'rania.ali.mohamed@aun.edu.eg', '01156789012', 'Software Engineering', 2, 'B'),
            ('Youssef Hassan Ali', 'SE2023016', 'youssef.hassan.ali@aun.edu.eg', '01167890123', 'Software Engineering', 1, 'A'),
            ('Nada Ibrahim Omar', 'CY2021017', 'nada.ibrahim.omar@aun.edu.eg', '01178901234', 'Cybersecurity', 3, 'A'),
            ('Mahmoud Ali Hassan', 'CY2022018', 'mahmoud.ali.hassan@aun.edu.eg', '01189012345', 'Cybersecurity', 2, 'B'),
            ('Salma Mohamed Ibrahim', 'CY2023019', 'salma.mohamed.ibrahim@aun.edu.eg', '01190123456', 'Cybersecurity', 1, 'A'),
            ('Tarek Hassan Mohamed', 'CS2022020', 'tarek.hassan.mohamed@aun.edu.eg', '01101234567', 'Computer Science', 2, 'B')
        ]
        
        for student in egyptian_students:
            cursor.execute("""
                INSERT INTO students_enhanced 
                (name, roll_number, email, phone, department, year, section, enrollment_date, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active')
            """, student + (date.today(),))
        
        print(f"   Added {len(egyptian_students)} Egyptian students")
        
        # 3. EGYPTIAN TEACHERS
        print("\n👨‍🏫 Adding Egyptian Teachers...")
        egyptian_teachers = [
            ('Dr. Ahmed Hassan Mohamed', 'ahmed.hassan@aun.edu.eg', '01012345001', 'Computer Science', 'Software Engineering'),
            ('Dr. Fatma Ali Ibrahim', 'fatma.ali@aun.edu.eg', '01012345002', 'Computer Science', 'Database Systems'),
            ('Dr. Mohamed Omar Khalil', 'mohamed.omar@aun.edu.eg', '01012345003', 'Artificial Intelligence', 'Machine Learning'),
            ('Dr. Sara Ahmed Mahmoud', 'sara.ahmed@aun.edu.eg', '01012345004', 'Information Systems', 'System Analysis'),
            ('Dr. Nour Hassan Farouk', 'nour.hassan@aun.edu.eg', '01012345005', 'Information Technology', 'Network Security'),
            ('Dr. Omar Ali Hassan', 'omar.ali@aun.edu.eg', '01012345006', 'Software Engineering', 'Software Architecture'),
            ('Dr. Mariam Mostafa Ali', 'mariam.mostafa@aun.edu.eg', '01012345007', 'Cybersecurity', 'Digital Forensics'),
            ('Dr. Amr Khaled Mohamed', 'amr.khaled@aun.edu.eg', '01012345008', 'Artificial Intelligence', 'Natural Language Processing'),
            ('Dr. Yasmin Ibrahim Saeed', 'yasmin.ibrahim@aun.edu.eg', '01012345009', 'Information Systems', 'Business Intelligence'),
            ('Dr. Hassan Mohamed Omar', 'hassan.mohamed@aun.edu.eg', '01012345010', 'Computer Science', 'Algorithms')
        ]
        
        for teacher in egyptian_teachers:
            # Generate employee ID
            employee_id = f"EMP{random.randint(1000, 9999)}"
            cursor.execute("""
                INSERT INTO teachers_enhanced 
                (name, employee_id, email, phone, department, specialization, status)
                VALUES (?, ?, ?, ?, ?, ?, 'active')
            """, (teacher[0], employee_id, teacher[1], teacher[2], teacher[3], teacher[4]))
        
        print(f"   Added {len(egyptian_teachers)} Egyptian teachers")
        
        # 4. SUBJECTS
        print("\n📚 Adding Subjects...")
        subjects_data = [
            # Computer Science Subjects
            ('Programming Fundamentals', 'CS101', 3, 'Introduction to programming concepts', 'Computer Science', 1, 1),
            ('Data Structures and Algorithms', 'CS201', 4, 'Core data structures and algorithmic thinking', 'Computer Science', 2, 1),
            ('Database Systems', 'CS202', 3, 'Relational databases and SQL', 'Computer Science', 2, 2),
            ('Software Engineering', 'CS301', 4, 'Software development lifecycle', 'Computer Science', 3, 1),
            ('Computer Networks', 'CS302', 3, 'Network protocols and architecture', 'Computer Science', 3, 2),
            
            # AI Subjects
            ('Introduction to AI', 'AI101', 3, 'Fundamentals of artificial intelligence', 'Artificial Intelligence', 1, 1),
            ('Machine Learning', 'AI201', 4, 'ML algorithms and applications', 'Artificial Intelligence', 2, 1),
            ('Deep Learning', 'AI301', 4, 'Neural networks and deep learning', 'Artificial Intelligence', 3, 1),
            ('Natural Language Processing', 'AI302', 3, 'Text processing and language models', 'Artificial Intelligence', 3, 2),
            
            # Information Systems Subjects
            ('System Analysis', 'IS101', 3, 'Business system analysis methods', 'Information Systems', 1, 1),
            ('Business Intelligence', 'IS201', 3, 'Data analysis for business decisions', 'Information Systems', 2, 1),
            ('Enterprise Systems', 'IS301', 4, 'Large-scale business systems', 'Information Systems', 3, 1),
            
            # IT Subjects
            ('Network Administration', 'IT101', 3, 'Network setup and management', 'Information Technology', 1, 1),
            ('System Administration', 'IT201', 3, 'Server and system management', 'Information Technology', 2, 1),
            ('Cloud Computing', 'IT301', 4, 'Cloud platforms and services', 'Information Technology', 3, 1),
            
            # Software Engineering Subjects
            ('Software Architecture', 'SE201', 4, 'System design and architecture patterns', 'Software Engineering', 2, 1),
            ('Software Testing', 'SE301', 3, 'Testing methodologies and tools', 'Software Engineering', 3, 1),
            ('DevOps', 'SE302', 3, 'Development and operations integration', 'Software Engineering', 3, 2),
            
            # Cybersecurity Subjects
            ('Ethical Hacking', 'CY201', 4, 'Penetration testing techniques', 'Cybersecurity', 2, 1),
            ('Digital Forensics', 'CY301', 3, 'Digital investigation methods', 'Cybersecurity', 3, 1)
        ]
        
        for subject in subjects_data:
            cursor.execute("""
                INSERT INTO subjects_enhanced 
                (subject_name, course_code, credit_hours, description, department, year, semester, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'active')
            """, subject)
        
        print(f"   Added {len(subjects_data)} subjects")
        
        # 5. TEACHER-SUBJECT ASSIGNMENTS
        print("\n🎓 Assigning Teachers to Subjects...")
        
        # Get teachers and subjects for assignment
        cursor.execute("SELECT teacher_id, name, department FROM teachers_enhanced")
        teachers = cursor.fetchall()
        
        cursor.execute("SELECT subject_id, subject_name, department FROM subjects_enhanced")
        subjects = cursor.fetchall()
        
        # Assign teachers to subjects in their departments
        assignments = []
        for teacher_id, teacher_name, teacher_dept in teachers:
            # Find subjects in the same department
            dept_subjects = [s for s in subjects if s[2] == teacher_dept]
            
            # Assign 2-4 subjects to each teacher
            num_assignments = random.randint(2, min(4, len(dept_subjects)))
            assigned_subjects = random.sample(dept_subjects, num_assignments)
            
            for subject_id, subject_name, _ in assigned_subjects:
                assignments.append((teacher_id, subject_id, '2024-2025', 1, 'active'))
        
        for assignment in assignments:
            cursor.execute("""
                INSERT INTO teacher_subjects_enhanced 
                (teacher_id, subject_id, academic_year, semester, status, assigned_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, assignment + (date.today(),))
        
        print(f"   Added {len(assignments)} teacher-subject assignments")
        
        # 6. CLASS SCHEDULES
        print("\n📅 Creating Class Schedules...")
        
        days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday']  # Egyptian work week
        time_slots = [
            ('08:00', '09:30'),
            ('09:45', '11:15'),
            ('11:30', '13:00'),
            ('13:30', '15:00'),
            ('15:15', '16:45')
        ]
        
        rooms = [f'A{i}' for i in range(101, 106)] + [f'B{i}' for i in range(201, 206)] + [f'C{i}' for i in range(301, 306)]
        
        schedules = []
        used_combinations = set()
        
        for assignment in assignments:
            teacher_id, subject_id = assignment[0], assignment[1]
            
            # Create 1-2 weekly sessions for each teacher-subject pair
            for _ in range(random.randint(1, 2)):
                attempts = 0
                while attempts < 10:  # Avoid infinite loop
                    day = random.choice(days)
                    start_time, end_time = random.choice(time_slots)
                    room = random.choice(rooms)
                    
                    # Check for conflicts
                    combo = (teacher_id, day, start_time)
                    if combo not in used_combinations:
                        used_combinations.add(combo)
                        schedules.append((
                            subject_id, teacher_id, day, start_time, end_time, room,
                            'Lecture', 'A', '2024-2025', '1', 'active'
                        ))
                        break
                    attempts += 1
        
        for schedule in schedules:
            cursor.execute("""
                INSERT INTO class_schedules_enhanced 
                (subject_id, teacher_id, day_of_week, start_time, end_time, room_number,
                 class_type, section, academic_year, semester, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, schedule)
        
        print(f"   Added {len(schedules)} class schedules")
        
        # 7. USER ACCOUNTS (Password = Username)
        print("\n🔐 Creating User Accounts (Password = Username)...")
        
        # Admin accounts
        admin_users = [
            ('admin', 'admin', 'admin@aun.edu.eg', 'System Administrator', 'admin', None),
            ('dean', 'dean', 'dean@aun.edu.eg', 'Dean of Faculty', 'admin', None)
        ]
        
        for user in admin_users:
            username, password, email, full_name, role, linked_id = user
            cursor.execute("""
                INSERT INTO users_enhanced 
                (username, password_hash, email, full_name, role, linked_id, status)
                VALUES (?, ?, ?, ?, ?, ?, 'active')
            """, (username, hash_password(password), email, full_name, role, linked_id))
        
        # Teacher accounts (Password = Username)
        for teacher_id, name, department in teachers:
            username = name.replace('Dr. ', '').replace(' ', '.').lower()
            # Ensure unique username
            counter = 1
            original_username = username
            while True:
                cursor.execute("SELECT 1 FROM users_enhanced WHERE username = ?", (username,))
                if not cursor.fetchone():
                    break
                username = f"{original_username}{counter}"
                counter += 1
                
            cursor.execute("""
                INSERT INTO users_enhanced 
                (username, password_hash, email, full_name, role, linked_id, status)
                VALUES (?, ?, ?, ?, 'teacher', ?, 'active')
            """, (username, hash_password(username), f"{username}@aun.edu.eg", name, teacher_id))
        
        # Student accounts (Password = Username)
        cursor.execute("SELECT student_id, name, email FROM students_enhanced")
        students = cursor.fetchall()
        
        for student_id, name, email in students:
            username = name.replace(' ', '.').lower()
            # Ensure unique username
            counter = 1
            original_username = username
            while True:
                cursor.execute("SELECT 1 FROM users_enhanced WHERE username = ?", (username,))
                if not cursor.fetchone():
                    break
                username = f"{original_username}{counter}"
                counter += 1
                
            cursor.execute("""
                INSERT INTO users_enhanced 
                (username, password_hash, email, full_name, role, linked_id, status)
                VALUES (?, ?, ?, ?, 'student', ?, 'active')
            """, (username, hash_password(username), email, name, student_id))
        
        print(f"   Added user accounts for admins, {len(teachers)} teachers, {len(students)} students")
        
        # 8. STUDENT PROFILES
        print("\n👤 Creating Student Profiles...")
        
        for student_id, name, email in students:
            cursor.execute("""
                INSERT INTO student_profiles_enhanced 
                (student_id, profile_name, confidence_threshold, status)
                VALUES (?, ?, ?, 'active')
            """, (student_id, name, 0.75))
        
        print(f"   Added {len(students)} student profiles")
        
        # 9. STUDENT ENROLLMENTS
        print("\n📝 Creating Student Enrollments...")
        
        enrollments = []
        for student_id, name, _ in students[:15]:  # Enroll first 15 students
            # Get student's department
            cursor.execute("SELECT department, year FROM students_enhanced WHERE student_id = ?", (student_id,))
            student_dept, student_year = cursor.fetchone()
            
            # Find subjects for their department and year
            cursor.execute("SELECT subject_id FROM subjects_enhanced WHERE department = ? AND year <= ?", 
                         (student_dept, student_year))
            available_subjects = cursor.fetchall()
            
            # Enroll in 2-4 subjects
            if available_subjects:
                num_enrollments = min(random.randint(2, 4), len(available_subjects))
                enrolled_subjects = random.sample(available_subjects, num_enrollments)
                
                for (subject_id,) in enrolled_subjects:
                    enrollments.append((
                        student_id, subject_id, '2024-2025', 1, 
                        'enrolled', date.today()
                    ))
        
        for enrollment in enrollments:
            cursor.execute("""
                INSERT INTO student_enrollments_enhanced 
                (student_id, subject_id, academic_year, semester, status, enrollment_date)
                VALUES (?, ?, ?, ?, ?, ?)
            """, enrollment)
        
        print(f"   Added {len(enrollments)} student enrollments")
        
        # 10. ATTENDANCE RECORDS
        print("\n✅ Creating Sample Attendance Records...")
        
        # Generate attendance for the past 3 months
        start_date = date.today() - timedelta(days=90)
        
        attendance_records = []
        for enrollment in enrollments:
            student_id, subject_id = enrollment[0], enrollment[1]
            
            # Get teacher for this subject
            cursor.execute("SELECT teacher_id FROM teacher_subjects_enhanced WHERE subject_id = ? LIMIT 1", 
                         (subject_id,))
            teacher_result = cursor.fetchone()
            if not teacher_result:
                continue
            teacher_id = teacher_result[0]
            
            # Generate 15-20 attendance records per enrollment
            for _ in range(random.randint(15, 20)):
                attendance_date = start_date + timedelta(days=random.randint(0, 89))
                status = random.choices(['present', 'absent', 'late', 'excused'], 
                                      weights=[70, 15, 10, 5])[0]
                
                attendance_records.append((
                    student_id, subject_id, teacher_id, attendance_date,
                    f"{random.randint(8, 16):02d}:{random.randint(0, 59):02d}:00",
                    status, 'system', None, '2024-2025', '1', 'A'
                ))
        
        cursor.executemany("""
            INSERT INTO attendance_records_enhanced 
            (student_id, subject_id, teacher_id, attendance_date, attendance_time, 
             status, marked_by, notes, academic_year, semester, section, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, attendance_records)
        
        print(f"   Added {len(attendance_records)} attendance records")
        
        # 11. ATTENDANCE SESSIONS
        print("\n🏫 Creating Attendance Sessions...")
        
        # Create attendance sessions for class schedules
        sessions = []
        for schedule in schedules:
            subject_id, teacher_id, day, start_time, end_time = schedule[0], schedule[1], schedule[2], schedule[3], schedule[4]
            
            # Create 10-15 sessions for each schedule over the past 3 months
            for week in range(12):  # 12 weeks of classes
                session_date = start_date + timedelta(weeks=week)
                # Adjust to the correct day of week
                days_mapping = {'Sunday': 6, 'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3}
                target_weekday = days_mapping.get(day, 0)
                current_weekday = session_date.weekday()
                
                # Calculate days to add to get to target weekday
                days_to_add = (target_weekday - current_weekday) % 7
                session_date = session_date + timedelta(days=days_to_add)
                
                if session_date <= date.today():
                    sessions.append((
                        subject_id, teacher_id, session_date, start_time, end_time
                    ))
        
        for session in sessions:
            cursor.execute("""
                INSERT INTO attendance_sessions_enhanced 
                (subject_id, teacher_id, session_date, start_time, end_time, 
                 session_type, location, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (session[0], session[1], session[2], session[3], session[4], 
                  'Lecture', 'Main Campus', 'completed'))
        
        print(f"   Added {len(sessions)} attendance sessions")
        
        # FINAL VERIFICATION
        print("\n📊 FINAL VERIFICATION:")
        
        tables_to_check = [
            'departments', 'students_enhanced', 'teachers_enhanced', 'subjects_enhanced',
            'teacher_subjects_enhanced', 'class_schedules_enhanced', 'users_enhanced',
            'student_profiles_enhanced', 'student_enrollments_enhanced', 
            'attendance_records_enhanced', 'attendance_sessions_enhanced'
        ]
        
        for table in tables_to_check:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"   {table}: {count} records")
            except sqlite3.OperationalError:
                print(f"   {table}: Table not found")
        
        conn.commit()
        
        print("\n🎉 EGYPTIAN UNIVERSITY DATA POPULATION COMPLETE!")
        print("=" * 50)
        print("📋 Sample Login Credentials (Password = Username):")
        print("   Admin: admin / admin")
        print("   Admin: dean / dean")
        print("   Teacher: ahmed.hassan.mohamed / ahmed.hassan.mohamed")
        print("   Student: ahmed.mohamed.hassan / ahmed.mohamed.hassan")
        print("\n🇪🇬 All passwords are the same as usernames for easy testing!")
        
    except Exception as e:
        print(f"❌ Error during data population: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()
    
    print("\n✅ Data population completed successfully!")

if __name__ == "__main__":
    populate_egyptian_data()
