#!/usr/bin/env python3
"""
Assign Unique Subjects to Teachers Script

This script assigns different subjects to each teacher to ensure variety in teaching assignments.
Each teacher will get 1-3 subjects based on their expertise area.
"""

import sqlite3
from datetime import datetime

def assign_unique_subjects_to_teachers():
    """Assign unique subjects to each teacher"""
    
    conn = sqlite3.connect('attendance_system.db')
    cursor = conn.cursor()
    
    try:
        # First, clear existing teacher-subject assignments
        print("Clearing existing teacher-subject assignments...")
        cursor.execute("DELETE FROM teacher_subjects_enhanced")
        conn.commit()
        print("✅ Cleared existing assignments")
        
        # Get all teachers with their linked_id
        cursor.execute("""
            SELECT username, full_name, linked_id 
            FROM users_enhanced 
            WHERE role = 'teacher' 
            ORDER BY username
        """)
        teachers = cursor.fetchall()
        
        # Get all subjects
        cursor.execute("""
            SELECT subject_id, subject_name, course_code, department 
            FROM subjects_enhanced 
            ORDER BY subject_name
        """)
        subjects = cursor.fetchall()
        
        print(f"Found {len(teachers)} teachers and {len(subjects)} subjects")
        
        # Create subject assignments based on teacher expertise/department
        teacher_assignments = [
            # Mathematics and Physics teachers
            ('emp2024001', 'Dr. Mariam Abdel Rahman', ['Classical Mechanics', 'Quantum Physics']),
            ('emp2024002', 'Dr. Yasmin Ibrahim', ['Electromagnetism', 'Thermodynamics']),
            ('emp2024003', 'Dr. Youssef Farouk', ['Calculus I', 'Linear Algebra', 'Statistics']),
            ('emp2024004', 'Dr. Ali Farouk', ['Discrete Mathematics', 'Engineering Mathematics']),
            
            # Computer Science teachers
            ('emp2024005', 'Dr. Ahmed Mahmoud', ['Data Structures', 'Machine Learning']),
            ('emp2024006', 'Dr. Sara Abdel Rahman', ['Database Systems', 'Web Development']),
            
            # Engineering teachers
            ('emp2024007', 'Dr. Mariam El Sayed', ['Circuit Analysis', 'Materials Science']),
            ('emp2024008', 'Dr. Aya Khaled', ['Project Management']),
            
            # Business teachers
            ('emp2024009', 'Dr. Nour Omar', ['Management Principles', 'Marketing']),
            ('emp2024010', 'Dr. Hassan Mostafa', ['Financial Accounting', 'Business Statistics']),
            
            # Mixed assignments for remaining teachers
            ('emp2024011', 'Dr. Reem Mostafa', ['Statistics']),
            ('emp2024012', 'Dr. Mahmoud Khaled', ['Engineering Mathematics']),
            ('emp2024013', 'Dr. Laila Farouk', ['Marketing']),
            ('emp2024014', 'Dr. Heba Khaled', ['Project Management']),
            ('emp2024015', 'Dr. Fatma Ibrahim', ['Business Statistics']),
        ]
        
        # Create a mapping of subject names to IDs
        subject_name_to_id = {name: sid for sid, name, code, dept in subjects}
        
        # Create a mapping of teacher usernames to linked_ids
        teacher_username_to_id = {username: linked_id for username, full_name, linked_id in teachers}
        
        assignment_count = 0
        
        for teacher_username, teacher_name, assigned_subjects in teacher_assignments:
            if teacher_username not in teacher_username_to_id:
                print(f"⚠️ Teacher {teacher_username} not found in database")
                continue
                
            teacher_id = teacher_username_to_id[teacher_username]
            
            for subject_name in assigned_subjects:
                if subject_name in subject_name_to_id:
                    subject_id = subject_name_to_id[subject_name]
                    
                    # Insert the assignment
                    cursor.execute("""
                        INSERT INTO teacher_subjects_enhanced 
                        (teacher_id, subject_id, academic_year, semester, section, assigned_date, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (teacher_id, subject_id, '2024-2025', 'Fall', 'A', datetime.now().date(), 'active'))
                    
                    assignment_count += 1
                    print(f"✅ Assigned {subject_name} to {teacher_name}")
                else:
                    print(f"⚠️ Subject '{subject_name}' not found in database")
        
        conn.commit()
        print(f"\n🎉 Successfully created {assignment_count} teacher-subject assignments!")
        
        # Verify assignments
        print("\n📊 Assignment Summary:")
        cursor.execute("""
            SELECT u.username, u.full_name, COUNT(ts.subject_id) as subject_count
            FROM users_enhanced u
            LEFT JOIN teacher_subjects_enhanced ts ON u.linked_id = ts.teacher_id
            WHERE u.role = 'teacher'
            GROUP BY u.username, u.full_name
            ORDER BY u.username
        """)
        
        for username, full_name, count in cursor.fetchall():
            print(f"  {full_name} ({username}): {count} subjects")
        
        # Show detailed assignments
        print("\n📚 Detailed Assignments:")
        cursor.execute("""
            SELECT u.username, u.full_name, s.subject_name, s.course_code
            FROM users_enhanced u
            JOIN teacher_subjects_enhanced ts ON u.linked_id = ts.teacher_id
            JOIN subjects_enhanced s ON ts.subject_id = s.subject_id
            WHERE u.role = 'teacher'
            ORDER BY u.username, s.subject_name
        """)
        
        current_teacher = None
        for username, full_name, subject_name, course_code in cursor.fetchall():
            if current_teacher != username:
                print(f"\n  👩‍🏫 {full_name} ({username}):")
                current_teacher = username
            print(f"    - {subject_name} ({course_code})")
            
    except Exception as e:
        print(f"❌ Error assigning subjects to teachers: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
    
    return True

if __name__ == "__main__":
    print("🏫 Egyptian University - Teacher Subject Assignment")
    print("=" * 50)
    
    success = assign_unique_subjects_to_teachers()
    
    if success:
        print("\n✅ Teacher subject assignment completed successfully!")
        print("Each teacher now has unique subject assignments.")
    else:
        print("\n❌ Teacher subject assignment failed!")
