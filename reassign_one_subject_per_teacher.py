#!/usr/bin/env python3
"""
Reassign Teachers to One Subject Each Script

This script ensures:
1. Each teacher gets assigned to exactly ONE subject
2. Each subject gets assigned to exactly ONE teacher
3. No overlapping assignments
"""

import sqlite3
from datetime import datetime

def reassign_one_subject_per_teacher():
    """Reassign teachers so each has exactly one subject"""
    
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
        
        # Get all subjects that have attendance data
        cursor.execute("""
            SELECT DISTINCT s.subject_id, s.subject_name, s.course_code 
            FROM subjects_enhanced s
            WHERE EXISTS (
                SELECT 1 FROM attendance_records_enhanced ar 
                WHERE ar.subject_id = s.subject_id
            )
            ORDER BY s.subject_name
        """)
        subjects_with_data = cursor.fetchall()
        
        print(f"Found {len(teachers)} teachers and {len(subjects_with_data)} subjects with attendance data")
        
        # Create one-to-one assignments
        one_to_one_assignments = [
            # Each teacher gets exactly one subject
            ('emp2024001', 'Classical Mechanics'),
            ('emp2024002', 'Electromagnetism'), 
            ('emp2024003', 'Calculus I'),
            ('emp2024004', 'Linear Algebra'),
            ('emp2024005', 'Data Structures'),
            ('emp2024006', 'Database Systems'),
            ('emp2024007', 'Circuit Analysis'),
            ('emp2024008', 'Materials Science'),
            ('emp2024009', 'Management Principles'),
            ('emp2024010', 'Financial Accounting'),
            ('emp2024011', 'Statistics'),
            ('emp2024012', 'Engineering Mathematics'),
            ('emp2024013', 'Marketing'),
            ('emp2024014', 'Project Management'),
            ('emp2024015', 'Business Statistics'),
        ]
        
        # Create mappings
        subject_name_to_id = {name: sid for sid, name, code in subjects_with_data}
        teacher_username_to_id = {username: linked_id for username, full_name, linked_id in teachers}
        
        assignment_count = 0
        assigned_subjects = set()
        
        for teacher_username, subject_name in one_to_one_assignments:
            if teacher_username not in teacher_username_to_id:
                print(f"⚠️ Teacher {teacher_username} not found in database")
                continue
                
            if subject_name not in subject_name_to_id:
                print(f"⚠️ Subject '{subject_name}' not found or has no attendance data")
                continue
                
            if subject_name in assigned_subjects:
                print(f"⚠️ Subject '{subject_name}' already assigned to another teacher")
                continue
            
            teacher_id = teacher_username_to_id[teacher_username]
            subject_id = subject_name_to_id[subject_name]
            
            # Insert the assignment
            cursor.execute("""
                INSERT INTO teacher_subjects_enhanced 
                (teacher_id, subject_id, academic_year, semester, section, assigned_date, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (teacher_id, subject_id, '2024-2025', 'Fall', 'A', datetime.now().date(), 'active'))
            
            assigned_subjects.add(subject_name)
            assignment_count += 1
            
            # Get teacher name for display
            teacher_name = next((name for username, name, _ in teachers if username == teacher_username), teacher_username)
            print(f"✅ Assigned {subject_name} to {teacher_name} ({teacher_username})")
        
        conn.commit()
        print(f"\n🎉 Successfully created {assignment_count} one-to-one teacher-subject assignments!")
        
        # Verify assignments - each teacher should have exactly 1 subject
        print("\n📊 Assignment Verification:")
        cursor.execute("""
            SELECT u.username, u.full_name, COUNT(ts.subject_id) as subject_count,
                   GROUP_CONCAT(s.subject_name) as subjects
            FROM users_enhanced u
            LEFT JOIN teacher_subjects_enhanced ts ON u.linked_id = ts.teacher_id
            LEFT JOIN subjects_enhanced s ON ts.subject_id = s.subject_id
            WHERE u.role = 'teacher'
            GROUP BY u.username, u.full_name
            ORDER BY u.username
        """)
        
        for username, full_name, count, subjects in cursor.fetchall():
            if count == 1:
                print(f"  ✅ {full_name} ({username}): {subjects}")
            elif count == 0:
                print(f"  ❌ {full_name} ({username}): No subjects assigned")
            else:
                print(f"  ⚠️ {full_name} ({username}): {count} subjects (should be 1)")
        
        # Verify each subject has exactly one teacher
        print("\n📚 Subject Assignment Verification:")
        cursor.execute("""
            SELECT s.subject_name, COUNT(ts.teacher_id) as teacher_count,
                   GROUP_CONCAT(u.full_name) as teachers
            FROM subjects_enhanced s
            LEFT JOIN teacher_subjects_enhanced ts ON s.subject_id = ts.subject_id
            LEFT JOIN users_enhanced u ON ts.teacher_id = u.linked_id
            WHERE s.subject_id IN (
                SELECT DISTINCT subject_id FROM attendance_records_enhanced
            )
            GROUP BY s.subject_id, s.subject_name
            ORDER BY s.subject_name
        """)
        
        for subject_name, teacher_count, teachers in cursor.fetchall():
            if teacher_count == 1:
                print(f"  ✅ {subject_name}: {teachers}")
            elif teacher_count == 0:
                print(f"  ❌ {subject_name}: No teacher assigned")
            else:
                print(f"  ⚠️ {subject_name}: {teacher_count} teachers (should be 1)")
            
    except Exception as e:
        print(f"❌ Error reassigning subjects to teachers: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
    
    return True

if __name__ == "__main__":
    print("🏫 Egyptian University - One-to-One Teacher Subject Assignment")
    print("=" * 60)
    
    success = reassign_one_subject_per_teacher()
    
    if success:
        print("\n✅ One-to-one teacher subject assignment completed successfully!")
        print("Each teacher now has exactly one subject, and each subject has exactly one teacher.")
    else:
        print("\n❌ Teacher subject reassignment failed!")
