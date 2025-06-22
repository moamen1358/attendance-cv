#!/usr/bin/env python3
"""
Enhanced Egyptian University Data Population Script
Generates realistic sample data with proper time distribution and comprehensive attendance.
"""

import sqlite3
import random
import hashlib
import sys
import os
from datetime import date, datetime, timedelta

# Add the src directory to the path to import db_init
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from db_init import initialize_database

def hash_password(password):
    """Create both MD5 and SHA256 hashes for compatibility"""
    # Return SHA256 hash for better security
    return hashlib.sha256(password.encode()).hexdigest()

def get_egyptian_names():
    """Generate Egyptian student and teacher names"""
    first_names_male = [
        'Ahmed', 'Mohamed', 'Mahmoud', 'Ali', 'Hassan', 'Omar', 'Khaled', 'Amr',
        'Tarek', 'Mostafa', 'Islam', 'Youssef', 'Ibrahim', 'Ayman', 'Sherif'
    ]
    
    first_names_female = [
        'Fatma', 'Aisha', 'Mariam', 'Nour', 'Sara', 'Dina', 'Heba', 'Aya',
        'Rana', 'Yasmin', 'Nada', 'Reem', 'Hala', 'Mona', 'Laila'
    ]
    
    last_names = [
        'Hassan', 'Mohamed', 'Ali', 'Ibrahim', 'Mahmoud', 'Omar', 'Khaled',
        'Ahmed', 'Youssef', 'Mostafa', 'Farouk', 'Abdel Rahman', 'El Sayed',
        'Morsi', 'Gaber', 'Soliman', 'Rashad', 'Naguib', 'Saad', 'Helmy'
    ]
    
    return first_names_male, first_names_female, last_names

def create_realistic_sample_data():
    """Create comprehensive realistic Egyptian university data"""
    
    print("🏛️ Initializing database...")
    # Initialize database first
    result = initialize_database()
    if result:
        print(f"Enhanced tables created: {result}")
    
    # Connect to database
    conn = sqlite3.connect('attendance_system.db')
    cursor = conn.cursor()
    
    print("\n🇪🇬 POPULATING ENHANCED EGYPTIAN UNIVERSITY DATA")
    print("=" * 60)
    
    try:
        # Clear existing data
        print("🗑️ Clearing existing data...")
        tables_to_clear = [
            'student_enrollments_enhanced', 'attendance_records_enhanced', 'attendance_sessions_enhanced',
            'class_schedules_enhanced', 'teacher_subjects_enhanced', 'student_profiles_enhanced',
            'users_enhanced', 'students_enhanced', 'subjects_enhanced', 'teachers_enhanced', 'departments'
        ]
        
        for table in tables_to_clear:
            cursor.execute(f"DELETE FROM {table}")
            print(f"   Cleared {table}")
        
        # 1. DEPARTMENTS
        print("\n🏢 Adding Departments...")
        departments = [
            ('Computer Science', 'CS', 'Building A', 'Dr. Ahmed Hassan', 'ahmed.hassan@uni.edu.eg'),
            ('Mathematics', 'MATH', 'Building B', 'Dr. Fatma Mohamed', 'fatma.mohamed@uni.edu.eg'),
            ('Physics', 'PHYS', 'Building C', 'Dr. Omar Ali', 'omar.ali@uni.edu.eg'),
            ('Engineering', 'ENG', 'Building D', 'Dr. Mahmoud Ibrahim', 'mahmoud.ibrahim@uni.edu.eg'),
            ('Business', 'BUS', 'Building E', 'Dr. Sara Khaled', 'sara.khaled@uni.edu.eg'),
            ('Arabic Literature', 'ARAB', 'Building F', 'Dr. Hassan Mostafa', 'hassan.mostafa@uni.edu.eg')
        ]
        
        for dept in departments:
            cursor.execute("""
                INSERT INTO departments (department_name, department_code, head_name, email)
                VALUES (?, ?, ?, ?)
            """, (dept[0], dept[1], dept[3], dept[4]))
        
        print(f"   Added {len(departments)} departments")
        
        # 2. STUDENTS (25 Egyptian students for better data volume)
        print("\n👥 Adding Egyptian Students...")
        first_males, first_females, last_names = get_egyptian_names()
        students = []
        
        for i in range(25):
            # Randomly choose gender
            is_male = random.choice([True, False])
            first_name = random.choice(first_males if is_male else first_females)
            middle_name = random.choice(first_males)  # Father's name
            last_name = random.choice(last_names)
            
            full_name = f"{first_name} {middle_name} {last_name}"
            roll_number = f"STU{2024}{i+1:03d}"
            email = f"{first_name.lower()}.{middle_name.lower()}.{last_name.lower()}@student.uni.edu.eg"
            
            # Random Egyptian phone numbers and addresses
            phone = f"01{random.choice([0, 1, 2, 5])}{random.randint(10000000, 99999999)}"
            
            year = random.choice([1, 2, 3, 4])
            department = random.choice(['Computer Science', 'Mathematics', 'Physics', 'Engineering'])
            
            students.append((full_name, roll_number, email, phone, department, year, 'A', 'active'))
        
        for student in students:
            cursor.execute("""
                INSERT INTO students_enhanced 
                (name, roll_number, email, phone, department, year, section, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, student)
        
        print(f"   Added {len(students)} Egyptian students")
        
        # 3. TEACHERS (12 Egyptian teachers)
        print("\n👨‍🏫 Adding Egyptian Teachers...")
        teachers = []
        
        teacher_titles = ['Dr.', 'Prof.', 'Eng.', 'Mr.', 'Mrs.']
        specializations = {
            'Computer Science': ['Machine Learning', 'Database Systems', 'Software Engineering', 'Computer Networks'],
            'Mathematics': ['Calculus', 'Linear Algebra', 'Statistics', 'Discrete Mathematics'],
            'Physics': ['Classical Mechanics', 'Quantum Physics', 'Thermodynamics', 'Electromagnetism'],
            'Engineering': ['Structural Engineering', 'Electrical Engineering', 'Mechanical Engineering'],
            'Business': ['Management', 'Marketing', 'Finance', 'Economics'],
            'Arabic Literature': ['Classical Arabic', 'Modern Literature', 'Poetry', 'Linguistics']
        }
        
        for i in range(12):
            is_male = random.choice([True, False])
            title = random.choice(teacher_titles)
            first_name = random.choice(first_males if is_male else first_females)
            last_name = random.choice(last_names)
            
            full_name = f"{title} {first_name} {last_name}"
            teacher_id = f"TCH{2024}{i+1:03d}"
            email = f"{first_name.lower()}.{last_name.lower()}@uni.edu.eg"
            
            phone = f"01{random.choice([0, 1, 2, 5])}{random.randint(10000000, 99999999)}"
            department = random.choice(list(specializations.keys()))
            specialization = random.choice(specializations[department])
            
            office = f"{department[:3].upper()}-{random.randint(101, 399)}"
            
            teachers.append((teacher_id, full_name, email, phone, department, specialization, office, 'active'))
        
        for teacher in teachers:
            cursor.execute("""
                INSERT INTO teachers_enhanced 
                (teacher_id, name, email, phone, department, specialization, office_location, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, teacher)
        
        print(f"   Added {len(teachers)} Egyptian teachers")
        
        # 4. SUBJECTS (Enhanced with better variety)
        print("\n📚 Adding Enhanced Subjects...")
        subjects_by_dept = {
            'Computer Science': [
                ('Data Structures', 'CS101', 3, 'Core programming concepts and algorithms'),
                ('Database Systems', 'CS201', 3, 'Relational databases and SQL'),
                ('Machine Learning', 'CS301', 4, 'AI and pattern recognition'),
                ('Web Development', 'CS202', 3, 'Frontend and backend technologies')
            ],
            'Mathematics': [
                ('Calculus I', 'MATH101', 4, 'Differential and integral calculus'),
                ('Linear Algebra', 'MATH201', 3, 'Vectors, matrices, and linear transformations'),
                ('Statistics', 'MATH301', 3, 'Probability and statistical inference'),
                ('Discrete Mathematics', 'MATH151', 3, 'Logic, sets, and combinatorics')
            ],
            'Physics': [
                ('Classical Mechanics', 'PHYS101', 4, 'Newton\'s laws and motion'),
                ('Electromagnetism', 'PHYS201', 4, 'Electric and magnetic fields'),
                ('Quantum Physics', 'PHYS301', 4, 'Quantum mechanics principles'),
                ('Thermodynamics', 'PHYS251', 3, 'Heat and energy transfer')
            ],
            'Engineering': [
                ('Engineering Mathematics', 'ENG101', 4, 'Mathematical methods for engineers'),
                ('Circuit Analysis', 'ENG201', 3, 'Electrical circuit fundamentals'),
                ('Materials Science', 'ENG151', 3, 'Properties of engineering materials'),
                ('Project Management', 'ENG301', 2, 'Engineering project planning')
            ],
            'Business': [
                ('Principles of Management', 'BUS101', 3, 'Fundamentals of business management'),
                ('Marketing', 'BUS201', 3, 'Consumer behavior and market analysis'),
                ('Financial Accounting', 'BUS151', 3, 'Basic accounting principles'),
                ('Business Statistics', 'BUS251', 3, 'Statistical methods in business')
            ]
        }
        
        subjects = []
        subject_id_counter = 1
        
        for dept, dept_subjects in subjects_by_dept.items():
            for subject_name, code, credits, description in dept_subjects:
                subjects.append((
                    subject_id_counter, subject_name, code, credits, 
                    description, dept, '2024-2025', 1, 'active'
                ))
                subject_id_counter += 1
        
        for subject in subjects:
            cursor.execute("""
                INSERT INTO subjects_enhanced 
                (subject_id, subject_name, subject_code, credits, description, 
                 department, academic_year, semester, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, subject)
        
        print(f"   Added {len(subjects)} enhanced subjects")
        
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
            
            # Assign 2-3 subjects to each teacher for focused teaching
            if dept_subjects:
                num_assignments = min(random.randint(2, 3), len(dept_subjects))
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
        
        # 6. ENHANCED CLASS SCHEDULES (Better time distribution)
        print("\n📅 Creating Enhanced Class Schedules...")
        
        # Egyptian university work week (Sunday to Thursday)
        days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday']
        
        # More realistic time slots with breaks
        time_slots = [
            ('08:00', '09:30'),   # Early morning
            ('09:45', '11:15'),   # Mid morning
            ('11:30', '13:00'),   # Pre-lunch
            ('14:00', '15:30'),   # Post-lunch
            ('15:45', '17:15')    # Late afternoon
        ]
        
        rooms = [f'{building}{floor}{room:02d}' for building in ['A', 'B', 'C'] 
                for floor in [1, 2, 3] for room in range(1, 6)]
        
        # Select top 6 subjects for main schedule (2 from CS, 1 from each other dept)
        main_assignments = []
        cs_assignments = [a for a in assignments if any(s[2] == 'Computer Science' for s in subjects if s[0] == a[1])]
        other_assignments = [a for a in assignments if not any(s[2] == 'Computer Science' for s in subjects if s[0] == a[1])]
        
        # Select 2 CS subjects and 4 from other departments
        main_assignments.extend(random.sample(cs_assignments, min(2, len(cs_assignments))))
        main_assignments.extend(random.sample(other_assignments, min(4, len(other_assignments))))
        
        schedules = []
        
        # Create a well-distributed weekly schedule
        schedule_template = [
            # Day, Time Slot Index, Class Type
            ('Sunday', 0, 'Lecture'),    # 08:00-09:30
            ('Sunday', 1, 'Lecture'),    # 09:45-11:15
            ('Sunday', 2, 'Tutorial'),   # 11:30-13:00
            
            ('Monday', 1, 'Lecture'),    # 09:45-11:15
            ('Monday', 3, 'Tutorial'),   # 14:00-15:30
            ('Monday', 4, 'Lab'),        # 15:45-17:15
            
            ('Tuesday', 0, 'Tutorial'),  # 08:00-09:30
            ('Tuesday', 2, 'Lecture'),   # 11:30-13:00
            ('Tuesday', 3, 'Lab'),       # 14:00-15:30
            
            ('Wednesday', 1, 'Lab'),     # 09:45-11:15
            ('Wednesday', 2, 'Tutorial'), # 11:30-13:00
            ('Wednesday', 4, 'Lecture'), # 15:45-17:15
            
            ('Thursday', 0, 'Lecture'),  # 08:00-09:30
            ('Thursday', 2, 'Lab'),      # 11:30-13:00
            ('Thursday', 3, 'Tutorial'), # 14:00-15:30
        ]
        
        for i, (day, time_idx, class_type) in enumerate(schedule_template):
            if i < len(main_assignments):
                assignment = main_assignments[i]
                teacher_id, subject_id = assignment[0], assignment[1]
                
                start_time, end_time = time_slots[time_idx]
                room = rooms[i % len(rooms)]
                
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
        
        print(f"   Added {len(schedules)} class schedules across 5 days with varied times")
        
        # 7. USER ACCOUNTS (Password = Username)
        print("\n🔐 Creating User Accounts...")
        
        # Admin users
        admin_users = [
            ('admin', 'System Administrator', 'admin@uni.edu.eg', 'admin'),
            ('dean', 'Dean of Faculty', 'dean@uni.edu.eg', 'admin'),
        ]
        
        for username, full_name, email, role in admin_users:
            cursor.execute("""
                INSERT INTO users_enhanced 
                (username, password_hash, email, full_name, role, status)
                VALUES (?, ?, ?, ?, ?, 'active')
            """, (username, hash_password(username), email, full_name, role))
        
        # Teacher users
        for teacher_id, name, email, _, _, _, _, _ in teachers:
            username = teacher_id.lower()
            cursor.execute("""
                INSERT INTO users_enhanced 
                (username, password_hash, email, full_name, role, linked_id, status)
                VALUES (?, ?, ?, ?, 'teacher', ?, 'active')
            """, (username, hash_password(username), email, name, teacher_id))
        
        # Student users  
        for student_id, name, email, _, _, _, _, _ in students:
            username = student_id.lower()
            cursor.execute("""
                INSERT INTO users_enhanced 
                (username, password_hash, email, full_name, role, linked_id, status)
                VALUES (?, ?, ?, ?, 'student', ?, 'active')
            """, (username, hash_password(username), email, name, student_id))
        
        print(f"   Added user accounts for 2 admins, {len(teachers)} teachers, {len(students)} students")
        
        # 8. STUDENT PROFILES
        print("\n👤 Creating Student Profiles...")
        
        for student_id, name, _, _, _, _, _, _ in students:
            cursor.execute("""
                INSERT INTO student_profiles_enhanced 
                (student_id, profile_name, confidence_threshold, status)
                VALUES (?, ?, ?, 'active')
            """, (student_id, name, 0.75))
        
        print(f"   Added {len(students)} student profiles")
        
        # 9. STUDENT ENROLLMENTS (All students in main subjects)
        print("\n📝 Creating Student Enrollments...")
        
        # Get the main subject IDs from our schedules
        main_subject_ids = list(set([schedule[0] for schedule in schedules]))
        
        enrollments = []
        # Enroll ALL students in ALL main subjects for comprehensive data
        for student_id, name, _, _, _, _, _, _ in students:
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
        
        # 10. COMPREHENSIVE ATTENDANCE RECORDS
        print("\n✅ Creating Comprehensive Attendance Records...")
        
        # Generate attendance for the past 4 months (120 days) for robust data
        start_date = date.today() - timedelta(days=120)
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
        
        print(f"   Generating attendance for {len(enrolled_students)} enrollments across {len(active_schedules)} schedules")
        
        # Fixed day mapping for SQLite strftime('%w') where Sunday=0
        day_to_weekday = {
            'Sunday': 0, 'Monday': 1, 'Tuesday': 2, 
            'Wednesday': 3, 'Thursday': 4, 'Friday': 5, 'Saturday': 6
        }
        
        # Create diverse student attendance profiles
        student_profiles = {}
        for student_id, _, student_name in enrolled_students:
            if student_id not in student_profiles:
                # Create different student personality types
                profile_types = ['excellent', 'good', 'average', 'struggling']
                weights = [0.2, 0.4, 0.3, 0.1]  # Most students are good/average
                profile_type = random.choices(profile_types, weights=weights)[0]
                
                if profile_type == 'excellent':
                    base_attendance = random.uniform(0.90, 0.97)
                    day_consistency = 0.95  # Very consistent
                elif profile_type == 'good':
                    base_attendance = random.uniform(0.80, 0.89)
                    day_consistency = 0.85
                elif profile_type == 'average':
                    base_attendance = random.uniform(0.65, 0.79)
                    day_consistency = 0.75
                else:  # struggling
                    base_attendance = random.uniform(0.45, 0.64)
                    day_consistency = 0.60
                
                # Day-of-week preferences (realistic patterns)
                day_factors = {
                    'Sunday': random.uniform(0.85, 1.05),    # Start of week
                    'Monday': random.uniform(0.80, 1.00),    # Monday blues
                    'Tuesday': random.uniform(0.90, 1.10),   # Peak performance
                    'Wednesday': random.uniform(0.95, 1.10), # Mid-week high
                    'Thursday': random.uniform(0.85, 1.00),  # End of week fatigue
                }
                
                # Time-of-day preferences
                time_factors = {
                    '08:00': random.uniform(0.75, 0.95),  # Early morning challenge
                    '09:45': random.uniform(0.90, 1.05),  # Good morning time
                    '11:30': random.uniform(0.95, 1.10),  # Peak morning focus
                    '14:00': random.uniform(0.85, 1.00),  # Post-lunch dip
                    '15:45': random.uniform(0.80, 0.95),  # Late afternoon fatigue
                }
                
                student_profiles[student_id] = {
                    'name': student_name,
                    'type': profile_type,
                    'base_attendance': base_attendance,
                    'day_consistency': day_consistency,
                    'day_factors': day_factors,
                    'time_factors': time_factors
                }
        
        attendance_records = []
        
        # Generate attendance for each day in the range
        current_date = start_date
        while current_date <= end_date:
            # SQLite weekday: Sunday=0, Monday=1, ..., Saturday=6
            current_weekday = current_date.weekday() + 1
            if current_weekday == 7:  # Sunday
                current_weekday = 0
            
            # Add seasonal effects (slight decline over semester)
            days_elapsed = (current_date - start_date).days
            seasonal_factor = 1.0 - (days_elapsed / 200) * 0.15  # Gradual decline
            
            # Random events (weather, holidays, etc.)
            event_factor = 1.0
            if random.random() < 0.03:  # 3% chance of disruptive event
                event_factor = random.uniform(0.70, 0.85)
            
            # Find classes scheduled for this weekday
            for schedule in active_schedules:
                subject_id, teacher_id, day_of_week, start_time, end_time, subject_name, class_type = schedule
                schedule_weekday = day_to_weekday[day_of_week]
                
                if current_weekday == schedule_weekday:
                    # Find students enrolled in this subject
                    subject_students = [
                        (student_id, student_name) for student_id, enroll_subject_id, student_name 
                        in enrolled_students if enroll_subject_id == subject_id
                    ]
                    
                    # Generate attendance for each student
                    for student_id, student_name in subject_students:
                        profile = student_profiles[student_id]
                        
                        # Calculate attendance probability
                        base_prob = profile['base_attendance']
                        day_factor = profile['day_factors'].get(day_of_week, 1.0)
                        time_factor = profile['time_factors'].get(start_time, 1.0)
                        consistency = profile['day_consistency']
                        
                        # Combine all factors
                        final_prob = base_prob * day_factor * time_factor * seasonal_factor * event_factor * consistency
                        final_prob = max(0.0, min(1.0, final_prob))
                        
                        # Determine attendance status
                        rand = random.random()
                        if rand < final_prob * 0.88:  # 88% of prob = present
                            status = 'present'
                            # Arrival time variation
                            time_offset = random.randint(-3, 8)
                        elif rand < final_prob * 0.94:  # Next 6% = late
                            status = 'late'
                            time_offset = random.randint(5, 30)
                        elif rand < final_prob * 0.97:  # Next 3% = excused
                            status = 'excused'
                            time_offset = 0
                        else:  # Remaining = absent
                            status = 'absent'
                            time_offset = 0
                        
                        # Calculate attendance time
                        attendance_time = None
                        if status in ['present', 'late']:
                            hour, minute = map(int, start_time.split(':'))
                            total_minutes = hour * 60 + minute + time_offset
                            final_hour = (total_minutes // 60) % 24
                            final_minute = total_minutes % 60
                            attendance_time = f"{final_hour:02d}:{final_minute:02d}:00"
                        
                        # Generate appropriate notes
                        notes = None
                        if status == 'late':
                            notes = f"Arrived {time_offset} minutes late"
                        elif status == 'excused':
                            excuses = [
                                'Medical appointment', 'Family emergency', 'University official business',
                                'Religious observance', 'Transportation issue'
                            ]
                            notes = random.choice(excuses)
                        elif status == 'absent':
                            notes = 'Unexcused absence'
                        
                        attendance_records.append((
                            student_id, subject_id, teacher_id, current_date,
                            attendance_time, status, 'system', notes,
                            '2024-2025', '1', 'A'
                        ))
            
            current_date += timedelta(days=1)
        
        # Insert attendance records in batches
        print(f"   Inserting {len(attendance_records)} attendance records...")
        batch_size = 200
        for i in range(0, len(attendance_records), batch_size):
            batch = attendance_records[i:i + batch_size]
            cursor.executemany("""
                INSERT INTO attendance_records_enhanced 
                (student_id, subject_id, teacher_id, attendance_date, attendance_time, 
                 status, marked_by, notes, academic_year, semester, section, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, batch)
        
        # Calculate and display comprehensive statistics
        total_records = len(attendance_records)
        present_count = sum(1 for r in attendance_records if r[5] == 'present')
        late_count = sum(1 for r in attendance_records if r[5] == 'late')
        absent_count = sum(1 for r in attendance_records if r[5] == 'absent')
        excused_count = sum(1 for r in attendance_records if r[5] == 'excused')
        
        print(f"   ✅ Added {total_records} comprehensive attendance records")
        print(f"   📊 Realistic Distribution:")
        print(f"      Present: {present_count} ({present_count/total_records*100:.1f}%)")
        print(f"      Late: {late_count} ({late_count/total_records*100:.1f}%)")
        print(f"      Absent: {absent_count} ({absent_count/total_records*100:.1f}%)")
        print(f"      Excused: {excused_count} ({excused_count/total_records*100:.1f}%)")
        print(f"   🎯 Enhanced Features: Student profiles, day/time preferences, seasonal effects")
        print(f"   📈 Visualization Ready: 120 days of data across all subjects and students")
        
        # 11. ATTENDANCE SESSIONS
        print("\n🏫 Creating Attendance Sessions...")
        
        sessions = []
        session_counter = 1
        
        # Create sessions for each class over the past 4 months
        for schedule in schedules:
            subject_id, teacher_id, day, start_time, end_time = schedule[0], schedule[1], schedule[2], schedule[3], schedule[4]
            schedule_weekday = day_to_weekday[day]
            
            # Find all dates for this weekday in our range
            current_date = start_date
            while current_date <= end_date:
                date_weekday = current_date.weekday() + 1
                if date_weekday == 7:
                    date_weekday = 0
                
                if date_weekday == schedule_weekday:
                    sessions.append((
                        session_counter, subject_id, teacher_id, current_date,
                        start_time, end_time, f"Session {session_counter}", 'completed'
                    ))
                    session_counter += 1
                
                current_date += timedelta(days=1)
        
        for session in sessions:
            cursor.execute("""
                INSERT INTO attendance_sessions_enhanced 
                (session_id, subject_id, teacher_id, session_date, start_time, end_time, 
                 session_name, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, session)
        
        print(f"   Added {len(sessions)} attendance sessions")
        
        # 12. FINAL VERIFICATION
        print("\n📊 FINAL DATABASE VERIFICATION:")
        
        tables = [
            'departments', 'students_enhanced', 'teachers_enhanced', 'subjects_enhanced',
            'teacher_subjects_enhanced', 'class_schedules_enhanced', 'users_enhanced',
            'student_profiles_enhanced', 'student_enrollments_enhanced', 
            'attendance_records_enhanced', 'attendance_sessions_enhanced'
        ]
        
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   {table}: {count} records")
        
        # Day distribution check
        print("\n📅 ATTENDANCE DISTRIBUTION BY DAY:")
        cursor.execute("""
            SELECT 
                CASE strftime('%w', attendance_date) 
                    WHEN '0' THEN 'Sunday'
                    WHEN '1' THEN 'Monday' 
                    WHEN '2' THEN 'Tuesday'
                    WHEN '3' THEN 'Wednesday'
                    WHEN '4' THEN 'Thursday'
                    WHEN '5' THEN 'Friday'
                    WHEN '6' THEN 'Saturday'
                END as day_name,
                COUNT(*) as count
            FROM attendance_records_enhanced 
            GROUP BY strftime('%w', attendance_date)
            ORDER BY strftime('%w', attendance_date)
        """)
        
        day_stats = cursor.fetchall()
        for day, count in day_stats:
            print(f"   {day}: {count} attendance records")
        
        # Commit all changes
        conn.commit()
        
        print("\n🎉 ENHANCED EGYPTIAN UNIVERSITY DATA POPULATION COMPLETE!")
        print("=" * 60)
        print("📋 Sample Login Credentials (Password = Username):")
        print("   Admin: admin / admin")
        print("   Admin: dean / dean")
        print("   Teacher: tch202401 / tch202401")
        print("   Student: stu202401 / stu202401")
        print("\n🇪🇬 All passwords are the same as usernames for easy testing!")
        print("✅ Comprehensive realistic data with 120 days of attendance across 5 weekdays!")
        
    except Exception as e:
        print(f"❌ Error during data population: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    create_realistic_sample_data()
