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
        
        # 6. CLASS SCHEDULES (Realistic daily distribution)
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
        
        # Select first 5 subjects for focused schedule
        main_subjects = assignments[:5]
        
        # Create a realistic weekly schedule with different times each day
        schedule_plan = [
            # (subject_index, day, time_slot_index, class_type)
            (0, 'Sunday', 0, 'Lecture'),      # Subject 1: Sunday 08:00-09:30
            (1, 'Sunday', 1, 'Lecture'),      # Subject 2: Sunday 09:45-11:15
            (2, 'Sunday', 2, 'Lecture'),      # Subject 3: Sunday 11:30-13:00
            
            (0, 'Monday', 1, 'Tutorial'),     # Subject 1: Monday 09:45-11:15
            (1, 'Monday', 2, 'Tutorial'),     # Subject 2: Monday 11:30-13:00
            (3, 'Monday', 3, 'Lecture'),      # Subject 4: Monday 13:30-15:00
            
            (2, 'Tuesday', 0, 'Tutorial'),    # Subject 3: Tuesday 08:00-09:30
            (3, 'Tuesday', 1, 'Tutorial'),    # Subject 4: Tuesday 09:45-11:15
            (4, 'Tuesday', 2, 'Lecture'),     # Subject 5: Tuesday 11:30-13:00
            
            (0, 'Wednesday', 2, 'Lab'),       # Subject 1: Wednesday 11:30-13:00
            (1, 'Wednesday', 3, 'Lab'),       # Subject 2: Wednesday 13:30-15:00
            (2, 'Wednesday', 4, 'Lab'),       # Subject 3: Wednesday 15:15-16:45
            
            (3, 'Thursday', 0, 'Lab'),        # Subject 4: Thursday 08:00-09:30
            (4, 'Thursday', 1, 'Tutorial'),   # Subject 5: Thursday 09:45-11:15
            (4, 'Thursday', 3, 'Lab'),        # Subject 5: Thursday 13:30-15:00
        ]
        
        for plan in schedule_plan:
            subject_idx, day, time_idx, class_type = plan
            
            # Make sure we don't go out of bounds
            if subject_idx < len(main_subjects):
                assignment = main_subjects[subject_idx]
                teacher_id, subject_id = assignment[0], assignment[1]
                
                start_time, end_time = time_slots[time_idx]
                room = rooms[(subject_idx * 3 + time_idx) % len(rooms)]  # Distribute rooms
                
                schedules.append((
                    subject_id, teacher_id, day, start_time, end_time, room,
                    class_type, 'A', '2024-2025', '1', 'active'
                ))
        
        for schedule in schedules:
            cursor.execute("""
                INSERT INTO class_schedules_enhanced 
                (subject_id, teacher_id, day_of_week, start_time, end_time, room_number,
                 class_type, section, academic_year, semester, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, schedule)
        
        print(f"   Added {len(schedules)} class schedules with realistic time distribution")
        
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
        
        # 9. STUDENT ENROLLMENTS (All students in main 5 subjects)
        print("\n📝 Creating Student Enrollments...")
        
        # Get the main 5 subjects from our focused schedule
        main_subject_ids = list(set([schedule[0] for schedule in schedules[:5]]))
        
        enrollments = []
        # Enroll ALL students in the main 5 subjects for comprehensive attendance tracking
        for student_id, name, _ in students:
            for subject_id in main_subject_ids:
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
        print(f"   All {len(students)} students enrolled in {len(main_subject_ids)} main subjects")
        
        # 10. ENHANCED ATTENDANCE RECORDS (Realistic patterns for visualization)
        print("\n✅ Creating Enhanced Sample Attendance Records...")
        
        # Generate attendance for the past 3 months with realistic patterns
        start_date = date.today() - timedelta(days=90)
        end_date = date.today()
        
        # Get all active class schedules with detailed info
        cursor.execute("""
            SELECT cs.subject_id, cs.teacher_id, cs.day_of_week, cs.start_time, cs.end_time,
                   s.subject_name, cs.class_type
            FROM class_schedules_enhanced cs
            JOIN subjects_enhanced s ON cs.subject_id = s.subject_id
            WHERE cs.status = 'active'
            ORDER BY cs.day_of_week, cs.start_time
        """)
        active_schedules = cursor.fetchall()
        
        # Get all enrolled students
        cursor.execute("""
            SELECT DISTINCT se.student_id, se.subject_id, st.name
            FROM student_enrollments_enhanced se
            JOIN students_enhanced st ON se.student_id = st.student_id
            WHERE se.status = 'enrolled'
        """)
        enrolled_students = cursor.fetchall()
        
        print(f"   Generating enhanced attendance for {len(enrolled_students)} enrollments across {len(active_schedules)} schedules")
        
        attendance_records = []
        days_mapping = {'Sunday': 6, 'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3, 'Friday': 4, 'Saturday': 5}
        
        # Create student reliability profiles for realistic patterns
        student_profiles = {}
        for student_id, _, student_name in enrolled_students:
            if student_id not in student_profiles:
                # Create different student types for variety
                profile_type = random.choice(['excellent', 'good', 'average', 'poor'])
                
                if profile_type == 'excellent':
                    base_attendance = 0.92  # 92% attendance
                    variation = 0.05
                elif profile_type == 'good':
                    base_attendance = 0.82  # 82% attendance
                    variation = 0.08
                elif profile_type == 'average':
                    base_attendance = 0.72  # 72% attendance
                    variation = 0.12
                else:  # poor
                    base_attendance = 0.55  # 55% attendance
                    variation = 0.15
                
                # Add day-of-week preferences (some students struggle with Monday/Sunday)
                day_preferences = {
                    'Sunday': random.uniform(0.8, 1.2),    # Sunday factor
                    'Monday': random.uniform(0.7, 1.1),    # Monday blues
                    'Tuesday': random.uniform(0.9, 1.1),   # Mid-week stability
                    'Wednesday': random.uniform(0.9, 1.1), # Mid-week stability
                    'Thursday': random.uniform(0.8, 1.0),  # End of week fatigue
                }
                
                # Add time-of-day preferences (early morning vs afternoon)
                time_preferences = {
                    '08:00': random.uniform(0.7, 1.0),  # Early morning struggles
                    '09:45': random.uniform(0.9, 1.1),  # Good time
                    '11:30': random.uniform(1.0, 1.1),  # Peak time
                    '13:30': random.uniform(0.8, 1.0),  # Post-lunch dip
                    '15:15': random.uniform(0.7, 0.9),  # Late afternoon fatigue
                }
                
                student_profiles[student_id] = {
                    'name': student_name,
                    'type': profile_type,
                    'base_attendance': base_attendance,
                    'variation': variation,
                    'day_preferences': day_preferences,
                    'time_preferences': time_preferences
                }
        
        # For each day in the past 3 months
        current_date = start_date
        while current_date <= end_date:
            weekday = current_date.weekday()
            
            # Add seasonal effects (better attendance at start of semester)
            days_from_start = (current_date - start_date).days
            seasonal_factor = 1.0 - (days_from_start / 180) * 0.1  # Slight decline over time
            
            # Add weather/holiday effects (random occasional drops)
            random_factor = 1.0
            if random.random() < 0.05:  # 5% chance of bad weather/event
                random_factor = random.uniform(0.7, 0.9)
            
            # Find schedules for this weekday
            for schedule in active_schedules:
                subject_id, teacher_id, day_of_week, start_time, end_time, subject_name, class_type = schedule
                schedule_weekday = days_mapping.get(day_of_week, 0)
                
                # If this schedule is for today's weekday
                if weekday == schedule_weekday:
                    # Find all students enrolled in this subject
                    subject_students = [
                        (student_id, student_name) for student_id, enroll_subject_id, student_name 
                        in enrolled_students if enroll_subject_id == subject_id
                    ]
                    
                    # Generate attendance for each student
                    for student_id, student_name in subject_students:
                        profile = student_profiles[student_id]
                        
                        # Calculate attendance probability based on multiple factors
                        base_prob = profile['base_attendance']
                        day_factor = profile['day_preferences'].get(day_of_week, 1.0)
                        time_factor = profile['time_preferences'].get(start_time, 1.0)
                        
                        # Combine all factors
                        attendance_prob = base_prob * day_factor * time_factor * seasonal_factor * random_factor
                        attendance_prob = max(0.0, min(1.0, attendance_prob))  # Clamp to 0-1
                        
                        # Determine status based on probability
                        rand = random.random()
                        if rand < attendance_prob * 0.85:  # 85% of attendance_prob = present
                            status = 'present'
                            # Present students arrive on time or slightly early/late
                            time_offset = random.randint(-5, 10)
                        elif rand < attendance_prob * 0.95:  # Next 10% = late
                            status = 'late'
                            # Late students arrive 5-25 minutes after start
                            time_offset = random.randint(5, 25)
                        elif rand < attendance_prob * 0.98:  # Next 3% = excused
                            status = 'excused'
                            time_offset = 0  # No specific time for excused
                        else:  # Remaining = absent
                            status = 'absent'
                            time_offset = 0  # No time recorded for absent
                        
                        # Generate realistic attendance time
                        if status in ['present', 'late']:
                            base_hour = int(start_time.split(':')[0])
                            base_minute = int(start_time.split(':')[1])
                            
                            # Calculate actual attendance time
                            total_minutes = base_hour * 60 + base_minute + time_offset
                            actual_hour = (total_minutes // 60) % 24
                            actual_minute = total_minutes % 60
                            attendance_time = f"{actual_hour:02d}:{actual_minute:02d}:00"
                        else:
                            attendance_time = None
                        
                        # Add notes for non-present statuses
                        notes = None
                        if status == 'late':
                            notes = f"Arrived {time_offset} minutes late"
                        elif status == 'excused':
                            excuses = ['Medical appointment', 'Family emergency', 'Official university business', 'Religious observance']
                            notes = random.choice(excuses)
                        elif status == 'absent':
                            notes = 'Unexcused absence'
                        
                        attendance_records.append((
                            student_id, subject_id, teacher_id, current_date,
                            attendance_time, status, 'system', notes,
                            '2024-2025', '1', 'A'
                        ))
            
            current_date += timedelta(days=1)
        
        # Insert all attendance records in batches for better performance
        print(f"   Inserting {len(attendance_records)} attendance records...")
        batch_size = 100
        for i in range(0, len(attendance_records), batch_size):
            batch = attendance_records[i:i + batch_size]
            cursor.executemany("""
                INSERT INTO attendance_records_enhanced 
                (student_id, subject_id, teacher_id, attendance_date, attendance_time, 
                 status, marked_by, notes, academic_year, semester, section, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, batch)
        
        # Calculate and display statistics
        total_records = len(attendance_records)
        present_count = sum(1 for r in attendance_records if r[5] == 'present')
        late_count = sum(1 for r in attendance_records if r[5] == 'late')
        absent_count = sum(1 for r in attendance_records if r[5] == 'absent')
        excused_count = sum(1 for r in attendance_records if r[5] == 'excused')
        
        print(f"   ✅ Added {total_records} enhanced attendance records")
        print(f"   📊 Distribution: Present={present_count} ({present_count/total_records*100:.1f}%), " +
              f"Late={late_count} ({late_count/total_records*100:.1f}%), " +
              f"Absent={absent_count} ({absent_count/total_records*100:.1f}%), " +
              f"Excused={excused_count} ({excused_count/total_records*100:.1f}%)")
        print(f"   🎯 Realistic patterns: Student profiles, day preferences, time factors, seasonal effects")
        print(f"   📈 Perfect for visualization: Weekly/daily trends, time analysis, student comparison")
        
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
