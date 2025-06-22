#!/usr/bin/env python3
"""
Assign Students to Departments and Years
This script assigns students to specific departments and academic years
so they see the appropriate class schedules.
"""

import sqlite3
from datetime import datetime

DATABASE_PATH = 'attendance_system.db'

def assign_students_to_programs():
    """Assign existing students to departments and years"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    print("👥 Assigning Students to Academic Programs")
    print("=" * 50)
    
    # Get all student users
    cursor.execute("SELECT username FROM user_accounts_enhanced WHERE role = 'student'")
    students = [row[0] for row in cursor.fetchall()]
    
    print(f"📋 Found {len(students)} student accounts")
    
    # Define department and year assignments
    assignments = [
        # Computer Science students
        ("ahmed_hassan", 1, 2, "Ahmed Hassan"),  # CS Year 2
        ("fatma_ali", 1, 1, "Fatma Ali"),       # CS Year 1  
        ("mohamed_omar", 1, 3, "Mohamed Omar"),  # CS Year 3
        
        # AI students
        ("sara_ahmed", 2, 1, "Sara Ahmed"),     # AI Year 1
        ("nour_hassan", 2, 2, "Nour Hassan"),   # AI Year 2
        ("amr_mohamed", 2, 3, "Amr Mohamed"),   # AI Year 3
        
        # IS students
        ("rana_ali", 3, 1, "Rana Ali"),         # IS Year 1
        
        # IT students
        ("khaled_ahmed", 4, 1, "Khaled Ahmed"), # IT Year 1
        
        # SE students  
        ("dina_hassan", 5, 1, "Dina Hassan"),   # SE Year 1
        
        # Cybersecurity students
        ("omar_ali", 6, 1, "Omar Ali"),         # CY Year 1
        
        # Test student
        ("student", 1, 2, "Test Student"),      # CS Year 2
    ]
    
    students_assigned = 0
    
    for username, dept_id, year, full_name in assignments:
        if username in students:
            # Check if student already exists in students_enhanced
            cursor.execute("""
                SELECT student_id FROM students_enhanced 
                WHERE name = ? OR roll_number LIKE ?
            """, (username, f"{username}%"))
            
            existing = cursor.fetchone()
            
            if existing:
                student_id = existing[0]
                # Update existing record
                cursor.execute("""
                    UPDATE students_enhanced 
                    SET name = ?, department = (SELECT department_name FROM departments WHERE department_id = ?),
                        year = ?, section = 'A', email = ?
                    WHERE student_id = ?
                """, (full_name, dept_id, year, f"{username}@university.edu", student_id))
                print(f"✅ Updated: {full_name} -> {get_dept_name(cursor, dept_id)} Year {year}")
            else:
                # Create new student record
                roll_number = f"{get_dept_code(cursor, dept_id)}{year:02d}{students_assigned + 1:03d}"
                cursor.execute("""
                    INSERT INTO students_enhanced 
                    (name, roll_number, email, phone, department, year, section, enrollment_date)
                    VALUES (?, ?, ?, ?, 
                           (SELECT department_name FROM departments WHERE department_id = ?), 
                           ?, 'A', date('now'))
                """, (full_name, roll_number, f"{username}@university.edu", 
                     f"+20{1000000000 + students_assigned}", dept_id, year))
                
                print(f"✅ Created: {full_name} ({roll_number}) -> {get_dept_name(cursor, dept_id)} Year {year}")
            
            students_assigned += 1
        else:
            print(f"⚠️  Student account '{username}' not found")
    
    conn.commit()
    
    # Create student enrollments for their department's subjects
    print(f"\n📚 Creating Subject Enrollments...")
    enrollment_count = 0
    
    for username, dept_id, year, full_name in assignments:
        if username in students:
            # Get student_id
            cursor.execute("SELECT student_id FROM students_enhanced WHERE name = ?", (full_name,))
            student_result = cursor.fetchone()
            
            if student_result:
                student_id = student_result[0]
                
                # Get all subjects for this department and year
                cursor.execute("""
                    SELECT subject_id FROM subjects_enhanced 
                    WHERE department_id = ? AND academic_year = ?
                """, (dept_id, year))
                
                subjects = cursor.fetchall()
                
                for (subject_id,) in subjects:
                    cursor.execute("""
                        INSERT OR IGNORE INTO student_enrollments_enhanced 
                        (student_id, subject_id, academic_year, semester, enrollment_date, status)
                        VALUES (?, ?, ?, 1, date('now'), 'enrolled')
                    """, (student_id, subject_id, f"2024-{year + 2024}"))
                    enrollment_count += 1
                
                print(f"  📖 Enrolled {full_name} in {len(subjects)} subjects")
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Successfully assigned {students_assigned} students to programs")
    print(f"📚 Created {enrollment_count} subject enrollments")
    
    return students_assigned, enrollment_count

def get_dept_name(cursor, dept_id):
    """Get department name by ID"""
    cursor.execute("SELECT department_name FROM departments WHERE department_id = ?", (dept_id,))
    result = cursor.fetchone()
    return result[0] if result else f"Dept {dept_id}"

def get_dept_code(cursor, dept_id):
    """Get department code by ID"""
    cursor.execute("SELECT department_code FROM departments WHERE department_id = ?", (dept_id,))
    result = cursor.fetchone()
    return result[0] if result else f"D{dept_id}"

def verify_assignments():
    """Verify student assignments"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            s.name,
            s.roll_number,
            s.department,
            s.year,
            COUNT(se.subject_id) as enrolled_subjects
        FROM students_enhanced s
        LEFT JOIN student_enrollments_enhanced se ON s.student_id = se.student_id
        GROUP BY s.student_id, s.name, s.roll_number, s.department, s.year
        ORDER BY s.department, s.year, s.name
    """)
    
    results = cursor.fetchall()
    
    print("\n👥 Student Assignment Summary:")
    print("-" * 80)
    print(f"{'Name':<15} {'Roll Number':<10} {'Department':<20} {'Year':<4} {'Subjects':<8}")
    print("-" * 80)
    
    for name, roll_num, dept, year, subjects in results:
        print(f"{name:<15} {roll_num:<10} {dept:<20} {year:<4} {subjects:<8}")
    
    print("-" * 80)
    print(f"Total Students: {len(results)}")
    
    conn.close()

if __name__ == "__main__":
    # Assign students to programs
    assigned, enrollments = assign_students_to_programs()
    
    # Verify the assignments
    verify_assignments()
    
    print(f"\n🎉 SUCCESS!")
    print(f"👥 Assigned {assigned} students to academic programs")
    print(f"📚 Created {enrollments} subject enrollments")
    print("\nStudents will now see schedules specific to their department and year!")
