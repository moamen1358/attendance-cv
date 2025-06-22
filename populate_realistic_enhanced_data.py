#!/usr/bin/env python3
"""
Enhanced Realistic Egyptian University Data Population Script
Generates comprehensive realistic data matching the actual database schema.
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
    """Create SHA256 hash for passwords"""
    return hashlib.sha256(password.encode()).hexdigest()

def get_egyptian_names():
    """Generate Egyptian names"""
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
        'Ahmed', 'Youssef', 'Mostafa', 'Farouk', 'Abdel Rahman', 'El Sayed'
    ]
    
    return first_names_male, first_names_female, last_names

def create_enhanced_realistic_data():
    """Create comprehensive realistic Egyptian university data"""
    
    print("🏛️ Initializing database...")
    result = initialize_database()
    if result:
        print("✅ Database initialized successfully!")
    
    conn = sqlite3.connect('attendance_system.db')
    cursor = conn.cursor()
    
    print("\n🇪🇬 CREATING ENHANCED REALISTIC EGYPTIAN UNIVERSITY DATA")
    print("=" * 65)
    
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
            ('Computer Science', 'CS', 'Dr. Ahmed Hassan', 'ahmed.hassan@uni.edu.eg'),
            ('Mathematics', 'MATH', 'Dr. Fatma Mohamed', 'fatma.mohamed@uni.edu.eg'),
            ('Physics', 'PHYS', 'Dr. Omar Ali', 'omar.ali@uni.edu.eg'),
            ('Engineering', 'ENG', 'Dr. Mahmoud Ibrahim', 'mahmoud.ibrahim@uni.edu.eg'),
            ('Business', 'BUS', 'Dr. Sara Khaled', 'sara.khaled@uni.edu.eg'),
        ]
        
        for dept in departments:
            cursor.execute("""
                INSERT INTO departments (department_name, department_code, head_name, email)
                VALUES (?, ?, ?, ?)
            """, dept)
        
        print(f"   Added {len(departments)} departments")
        
        # 2. STUDENTS (30 Egyptian students)
        print("\n👥 Adding Egyptian Students...")
        first_males, first_females, last_names = get_egyptian_names()
        students = []
        
        for i in range(30):
            is_male = random.choice([True, False])
            first_name = random.choice(first_males if is_male else first_females)
            middle_name = random.choice(first_males)
            last_name = random.choice(last_names)
            
            full_name = f"{first_name} {middle_name} {last_name}"
            roll_number = f"2024{i+1:03d}"
            email = f"{first_name.lower()}.{last_name.lower()}@student.uni.edu.eg"
            phone = f"01{random.choice([0, 1, 2, 5])}{random.randint(10000000, 99999999)}"
            
            department = random.choice(['Computer Science', 'Mathematics', 'Physics', 'Engineering', 'Business'])
            year = random.choice([1, 2, 3, 4])
            section = random.choice(['A', 'B'])
            
            students.append((full_name, roll_number, email, phone, department, year, section, 'active'))
        
        for student in students:
            cursor.execute("""
                INSERT INTO students_enhanced 
                (name, roll_number, email, phone, department, year, section, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, student)
        
        print(f"   Added {len(students)} Egyptian students")
        
        # 3. TEACHERS (15 Egyptian teachers)
        print("\n👨‍🏫 Adding Egyptian Teachers...")
        teachers = []
        
        specializations = {
            'Computer Science': ['Machine Learning', 'Database Systems', 'Software Engineering'],
            'Mathematics': ['Calculus', 'Linear Algebra', 'Statistics'],
            'Physics': ['Classical Mechanics', 'Quantum Physics', 'Electromagnetism'],
            'Engineering': ['Electrical Engineering', 'Mechanical Engineering'],
            'Business': ['Management', 'Marketing', 'Finance']
        }
        
        for i in range(15):
            is_male = random.choice([True, False])
            first_name = random.choice(first_males if is_male else first_females)
            last_name = random.choice(last_names)
            
            full_name = f"Dr. {first_name} {last_name}"
            employee_id = f"EMP{2024}{i+1:03d}"
            email = f"{first_name.lower()}.{last_name.lower()}@uni.edu.eg"
            phone = f"01{random.choice([0, 1, 2, 5])}{random.randint(10000000, 99999999)}"
            
            department = random.choice(list(specializations.keys()))
            specialization = random.choice(specializations[department])
            
            teachers.append((full_name, employee_id, email, phone, department, specialization, 'active'))
        
        for teacher in teachers:
            cursor.execute("""
                INSERT INTO teachers_enhanced 
                (name, employee_id, email, phone, department, specialization, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, teacher)
        
        print(f"   Added {len(teachers)} Egyptian teachers")
        
        # 4. SUBJECTS (20 subjects across departments)
        print("\n📚 Adding Subjects...")
        subjects_by_dept = {
            'Computer Science': [
                ('Data Structures', 'CS101', 3), ('Database Systems', 'CS201', 3),
                ('Machine Learning', 'CS301', 4), ('Web Development', 'CS202', 3)
            ],
            'Mathematics': [
                ('Calculus I', 'MATH101', 4), ('Linear Algebra', 'MATH201', 3),
                ('Statistics', 'MATH301', 3), ('Discrete Mathematics', 'MATH151', 3)
            ],
            'Physics': [
                ('Classical Mechanics', 'PHYS101', 4), ('Electromagnetism', 'PHYS201', 4),
                ('Quantum Physics', 'PHYS301', 4), ('Thermodynamics', 'PHYS251', 3)
            ],
            'Engineering': [
                ('Engineering Mathematics', 'ENG101', 4), ('Circuit Analysis', 'ENG201', 3),
                ('Materials Science', 'ENG151', 3), ('Project Management', 'ENG301', 2)
            ],
            'Business': [
                ('Management Principles', 'BUS101', 3), ('Marketing', 'BUS201', 3),
                ('Financial Accounting', 'BUS151', 3), ('Business Statistics', 'BUS251', 3)
            ]
        }
        
        subjects = []
        for dept, dept_subjects in subjects_by_dept.items():
            for subject_name, code, credits in dept_subjects:
                subjects.append((
                    subject_name, code, credits, f"Description for {subject_name}",
                    dept, 1, 2024, 'active'
                ))
        
        for subject in subjects:
            cursor.execute("""
                INSERT INTO subjects_enhanced 
                (subject_name, course_code, credit_hours, description, department, semester, year, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, subject)
        
        print(f"   Added {len(subjects)} subjects")
        
        # 5. TEACHER-SUBJECT ASSIGNMENTS
        print("\n🎓 Assigning Teachers to Subjects...")
        
        cursor.execute("SELECT teacher_id, department FROM teachers_enhanced")
        teachers_data = cursor.fetchall()
        
        cursor.execute("SELECT subject_id, department FROM subjects_enhanced")
        subjects_data = cursor.fetchall()
        
        assignments = []
        for teacher_id, teacher_dept in teachers_data:
            # Find subjects in the same department
            dept_subjects = [s[0] for s in subjects_data if s[1] == teacher_dept]
            
            # Assign 2-3 subjects to each teacher
            if dept_subjects:
                num_assignments = min(random.randint(2, 3), len(dept_subjects))
                assigned_subjects = random.sample(dept_subjects, num_assignments)
                
                for subject_id in assigned_subjects:
                    assignments.append((teacher_id, subject_id, '2024-2025', '1', 'A', 'active'))
        
        for assignment in assignments:
            cursor.execute("""
                INSERT INTO teacher_subjects_enhanced 
                (teacher_id, subject_id, academic_year, semester, section, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, assignment)
        
        print(f"   Added {len(assignments)} teacher-subject assignments")
        
        # 6. ENHANCED CLASS SCHEDULES (Better time distribution)
        print("\n📅 Creating Enhanced Class Schedules...")
        
        # Egyptian university work week
        days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday']
        
        # Realistic time slots with proper breaks
        time_slots = [
            ('08:00', '09:30'),   # Early morning
            ('09:45', '11:15'),   # Mid morning
            ('11:30', '13:00'),   # Pre-lunch
            ('14:00', '15:30'),   # Post-lunch
            ('15:45', '17:15')    # Late afternoon
        ]
        
        rooms = [f'{building}{floor}{room:02d}' for building in ['A', 'B', 'C'] 
                for floor in [1, 2] for room in range(1, 4)]
        
        # Select first 12 assignments for main schedule (to cover all patterns)
        main_assignments = assignments[:12]
        
        schedules = []
        
        # Create well-distributed schedule across days and times
        schedule_patterns = [
            ('Sunday', 0, 'Lecture'),    ('Sunday', 2, 'Tutorial'),
            ('Monday', 1, 'Lecture'),    ('Monday', 3, 'Lab'),
            ('Tuesday', 0, 'Tutorial'),  ('Tuesday', 4, 'Lecture'),
            ('Wednesday', 1, 'Lab'),     ('Wednesday', 2, 'Tutorial'),
            ('Thursday', 0, 'Lecture'),  ('Thursday', 3, 'Lab'),
            ('Thursday', 4, 'Tutorial'),  # Additional Thursday class
        ]
        
        for i, (day, time_idx, class_type) in enumerate(schedule_patterns):
            if i < len(main_assignments):
                teacher_id, subject_id = main_assignments[i][0], main_assignments[i][1]
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
                 class_type, section, academic_year, semester, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, schedule)
        
        print(f"   Added {len(schedules)} class schedules across 5 days with varied times")
        
        # 7. USER ACCOUNTS
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
        
        # Teacher users (using employee_id as username)
        cursor.execute("SELECT teacher_id, employee_id, name, email FROM teachers_enhanced")
        teacher_list = cursor.fetchall()
        
        for teacher_id, employee_id, name, email in teacher_list:
            username = employee_id.lower()
            cursor.execute("""
                INSERT INTO users_enhanced 
                (username, password_hash, email, full_name, role, linked_id, status)
                VALUES (?, ?, ?, ?, 'teacher', ?, 'active')
            """, (username, hash_password(username), email, name, teacher_id))
        
        # Student users (using roll_number as username)
        cursor.execute("SELECT student_id, roll_number, name, email FROM students_enhanced")
        student_list = cursor.fetchall()
        
        for student_id, roll_number, name, email in student_list:
            username = roll_number.lower()
            cursor.execute("""
                INSERT INTO users_enhanced 
                (username, password_hash, email, full_name, role, linked_id, status)
                VALUES (?, ?, ?, ?, 'student', ?, 'active')
            """, (username, hash_password(username), email, name, student_id))
        
        print(f"   Added user accounts for 2 admins, {len(teacher_list)} teachers, {len(student_list)} students")
        
        # 8. STUDENT PROFILES
        print("\n👤 Creating Student Profiles...")
        
        for student_id, roll_number, name, email in student_list:
            cursor.execute("""
                INSERT INTO student_profiles_enhanced 
                (student_id, profile_name, confidence_threshold, status)
                VALUES (?, ?, ?, 'active')
            """, (student_id, name, 0.75))
        
        print(f"   Added {len(student_list)} student profiles")
        
        # 9. STUDENT ENROLLMENTS (All students in main subjects)
        print("\n📝 Creating Student Enrollments...")
        
        # Get the main subject IDs from our schedules
        main_subject_ids = list(set([schedule[0] for schedule in schedules]))
        
        enrollments = []
        for student_id, roll_number, name, email in student_list:
            # Enroll each student in all main subjects for comprehensive data
            for subject_id in main_subject_ids:
                enrollments.append((
                    student_id, subject_id, '2024-2025', '1', 'enrolled'
                ))
        
        for enrollment in enrollments:
            cursor.execute("""
                INSERT INTO student_enrollments_enhanced 
                (student_id, subject_id, academic_year, semester, status)
                VALUES (?, ?, ?, ?, ?)
            """, enrollment)
        
        print(f"   Added {len(enrollments)} student enrollments")
        print(f"   All {len(student_list)} students enrolled in {len(main_subject_ids)} main subjects")
        
        # 10. COMPREHENSIVE ATTENDANCE RECORDS
        print("\n✅ Creating Comprehensive Attendance Records...")
        
        # Generate attendance for the past 4 months
        start_date = date.today() - timedelta(days=120)
        end_date = date.today()
        
        # Get all active class schedules
        cursor.execute("""
            SELECT cs.subject_id, cs.teacher_id, cs.day_of_week, cs.start_time, cs.end_time,
                   s.subject_name, cs.class_type
            FROM class_schedules_enhanced cs
            JOIN subjects_enhanced s ON cs.subject_id = s.subject_id
            WHERE cs.status = 'active'
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
        
        # Day mapping for SQLite strftime('%w') where Sunday=0
        day_to_weekday = {
            'Sunday': 0, 'Monday': 1, 'Tuesday': 2, 
            'Wednesday': 3, 'Thursday': 4, 'Friday': 5, 'Saturday': 6
        }
        
        # Create student attendance profiles
        student_profiles = {}
        for student_id, _, student_name in enrolled_students:
            if student_id not in student_profiles:
                profile_type = random.choices(
                    ['excellent', 'good', 'average', 'struggling'],
                    weights=[0.25, 0.40, 0.25, 0.10]
                )[0]
                
                if profile_type == 'excellent':
                    base_attendance = random.uniform(0.90, 0.97)
                elif profile_type == 'good':
                    base_attendance = random.uniform(0.80, 0.89)
                elif profile_type == 'average':
                    base_attendance = random.uniform(0.65, 0.79)
                else:  # struggling
                    base_attendance = random.uniform(0.50, 0.64)
                
                # Day preferences
                day_factors = {
                    'Sunday': random.uniform(0.90, 1.05),
                    'Monday': random.uniform(0.80, 1.00),
                    'Tuesday': random.uniform(0.95, 1.10),
                    'Wednesday': random.uniform(0.95, 1.10),
                    'Thursday': random.uniform(0.85, 1.00),
                }
                
                # Time preferences
                time_factors = {
                    '08:00': random.uniform(0.75, 0.95),
                    '09:45': random.uniform(0.90, 1.05),
                    '11:30': random.uniform(0.95, 1.10),
                    '14:00': random.uniform(0.85, 1.00),
                    '15:45': random.uniform(0.80, 0.95),
                }
                
                student_profiles[student_id] = {
                    'name': student_name,
                    'type': profile_type,
                    'base_attendance': base_attendance,
                    'day_factors': day_factors,
                    'time_factors': time_factors
                }
        
        attendance_records = []
        
        # Generate attendance for each day
        current_date = start_date
        while current_date <= end_date:
            # Get SQLite weekday (Sunday=0)
            current_weekday = current_date.weekday() + 1
            if current_weekday == 7:
                current_weekday = 0
            
            # Seasonal effects
            days_elapsed = (current_date - start_date).days
            seasonal_factor = 1.0 - (days_elapsed / 200) * 0.10
            
            # Random events
            event_factor = 1.0
            if random.random() < 0.04:  # 4% chance of disruptive event
                event_factor = random.uniform(0.75, 0.90)
            
            # Check each schedule
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
                        
                        final_prob = base_prob * day_factor * time_factor * seasonal_factor * event_factor
                        final_prob = max(0.0, min(1.0, final_prob))
                        
                        # Determine status
                        rand = random.random()
                        if rand < final_prob * 0.85:
                            status = 'present'
                            time_offset = random.randint(-2, 5)
                        elif rand < final_prob * 0.92:
                            status = 'late'
                            time_offset = random.randint(5, 25)
                        elif rand < final_prob * 0.96:
                            status = 'excused'
                            time_offset = 0
                        else:
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
                        
                        # Generate notes
                        notes = None
                        if status == 'late':
                            notes = f"Arrived {time_offset} minutes late"
                        elif status == 'excused':
                            notes = random.choice([
                                'Medical appointment', 'Family emergency', 'University business'
                            ])
                        
                        attendance_records.append((
                            student_id, subject_id, teacher_id, current_date,
                            attendance_time, status, 'system', notes,
                            '2024-2025', '1', 'A'
                        ))
            
            current_date += timedelta(days=1)
        
        # Insert attendance records
        print(f"   Inserting {len(attendance_records)} attendance records...")
        cursor.executemany("""
            INSERT INTO attendance_records_enhanced 
            (student_id, subject_id, teacher_id, attendance_date, attendance_time, 
             status, marked_by, notes, academic_year, semester, section)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, attendance_records)
        
        # Statistics
        total_records = len(attendance_records)
        present_count = sum(1 for r in attendance_records if r[5] == 'present')
        late_count = sum(1 for r in attendance_records if r[5] == 'late')
        absent_count = sum(1 for r in attendance_records if r[5] == 'absent')
        excused_count = sum(1 for r in attendance_records if r[5] == 'excused')
        
        print(f"   ✅ Added {total_records} comprehensive attendance records")
        print(f"   📊 Distribution: Present={present_count} ({present_count/total_records*100:.1f}%), " +
              f"Late={late_count} ({late_count/total_records*100:.1f}%), " +
              f"Absent={absent_count} ({absent_count/total_records*100:.1f}%), " +
              f"Excused={excused_count} ({excused_count/total_records*100:.1f}%)")
        
        # 11. ATTENDANCE SESSIONS
        print("\n🏫 Creating Attendance Sessions...")
        
        sessions = []
        session_counter = 1
        
        # Create sessions for each class
        for schedule in schedules:
            subject_id, teacher_id, day, start_time, end_time = schedule[0], schedule[1], schedule[2], schedule[3], schedule[4]
            schedule_weekday = day_to_weekday[day]
            
            current_date = start_date
            while current_date <= end_date:
                date_weekday = current_date.weekday() + 1
                if date_weekday == 7:
                    date_weekday = 0
                
                if date_weekday == schedule_weekday:
                    sessions.append((
                        subject_id, teacher_id, current_date, start_time, end_time,
                        'lecture', f"Room-{random.randint(101, 310)}", 'completed'
                    ))
                    session_counter += 1
                
                current_date += timedelta(days=1)
        
        for session in sessions:
            cursor.execute("""
                INSERT INTO attendance_sessions_enhanced 
                (subject_id, teacher_id, session_date, start_time, end_time, 
                 session_type, location, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, session)
        
        print(f"   Added {len(sessions)} attendance sessions")
        
        # Final verification
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
        
        # Day distribution
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
        
        # Time distribution
        print("\n⏰ ATTENDANCE DISTRIBUTION BY TIME:")
        cursor.execute("""
            SELECT cs.start_time, COUNT(ar.id) as count 
            FROM class_schedules_enhanced cs
            JOIN attendance_records_enhanced ar ON cs.subject_id = ar.subject_id
            GROUP BY cs.start_time 
            ORDER BY cs.start_time
        """)
        
        time_stats = cursor.fetchall()
        for time_slot, count in time_stats:
            print(f"   {time_slot}: {count} attendance records")
        
        conn.commit()
        
        print("\n🎉 ENHANCED REALISTIC DATA POPULATION COMPLETE!")
        print("=" * 65)
        print("📋 Sample Login Credentials (Password = Username):")
        print("   Admin: admin / admin")
        print("   Admin: dean / dean")
        print("   Teacher: emp202401 / emp202401")
        print("   Student: 2024001 / 2024001")
        print("\n✅ Comprehensive realistic data with 120 days of attendance!")
        print("📈 Perfect for visualization: All days covered, varied times, realistic patterns!")
        
    except Exception as e:
        print(f"❌ Error during data population: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    create_enhanced_realistic_data()
