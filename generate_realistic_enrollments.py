#!/usr/bin/env python3
"""
Generate Realistic Student Enrollments

This script creates more realistic student enrollments where:
- Each student takes 4-6 subjects (not all subjects)
- Each subject has 15-25 students (not all 30 students)
- Distribution varies by department (CS students take more CS courses, etc.)
"""

import sqlite3
import random
from datetime import datetime, timedelta

def generate_realistic_enrollments():
    """Generate realistic student enrollments for subjects"""
    
    conn = sqlite3.connect('attendance_system.db')
    cursor = conn.cursor()
    
    try:
        # Get all students
        cursor.execute("SELECT student_id, name FROM students_enhanced ORDER BY student_id")
        students = cursor.fetchall()
        
        # Get all subjects grouped by department
        cursor.execute("SELECT subject_id, subject_name, course_code, department FROM subjects_enhanced ORDER BY department, subject_name")
        subjects = cursor.fetchall()
        
        print(f"Found {len(students)} students and {len(subjects)} subjects")
        
        # Group subjects by department
        subjects_by_dept = {}
        for subject_id, subject_name, course_code, department in subjects:
            if department not in subjects_by_dept:
                subjects_by_dept[department] = []
            subjects_by_dept[department].append((subject_id, subject_name, course_code))
        
        print(f"Subjects by department: {list(subjects_by_dept.keys())}")
        
        # Clear existing enrollments
        print("Clearing existing enrollments...")
        cursor.execute("DELETE FROM student_enrollments_enhanced")
        conn.commit()
        
        # Create realistic enrollments
        enrollment_count = 0
        
        for student_id, student_name in students:
            # Each student gets 4-6 subjects
            num_subjects = random.randint(4, 6)
            
            # Students have preferences based on their ID (simulate different majors)
            student_major = None
            if student_id <= 10:  # First 10 students are CS majors
                student_major = "Computer Science"
            elif student_id <= 20:  # Next 10 are Engineering majors
                student_major = "Engineering"
            else:  # Last 10 are Business majors
                student_major = "Business"
            
            # Build subject preferences
            preferred_subjects = []
            other_subjects = []
            
            for dept, dept_subjects in subjects_by_dept.items():
                for subj in dept_subjects:
                    if (student_major == "Computer Science" and "CS" in subj[2]) or \
                       (student_major == "Engineering" and ("ENG" in subj[2] or "PHYS" in subj[2] or "MATH" in subj[2])) or \
                       (student_major == "Business" and "BUS" in subj[2]):
                        preferred_subjects.append(subj)
                    else:
                        other_subjects.append(subj)
            
            # Select subjects: 70% from preferred, 30% from others
            selected_subjects = []
            
            # Add preferred subjects (70% of selections)
            pref_count = max(1, int(num_subjects * 0.7))
            if len(preferred_subjects) >= pref_count:
                selected_subjects.extend(random.sample(preferred_subjects, pref_count))
            else:
                selected_subjects.extend(preferred_subjects)
            
            # Add other subjects to reach target count
            remaining_count = num_subjects - len(selected_subjects)
            if remaining_count > 0 and other_subjects:
                available_others = [s for s in other_subjects if s not in selected_subjects]
                if len(available_others) >= remaining_count:
                    selected_subjects.extend(random.sample(available_others, remaining_count))
                else:
                    selected_subjects.extend(available_others)
            
            # Insert enrollments
            for subject_id, subject_name, course_code in selected_subjects:
                cursor.execute("""
                    INSERT INTO student_enrollments_enhanced 
                    (student_id, subject_id, enrollment_date, status, semester, academic_year)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (student_id, subject_id, datetime.now().date(), 'active', 'Fall', '2024-2025'))
                
                enrollment_count += 1
            
            print(f"✅ {student_name} ({student_major}): enrolled in {len(selected_subjects)} subjects")
        
        conn.commit()
        print(f"\n🎉 Created {enrollment_count} realistic enrollments!")
        
        # Show summary statistics
        print("\n📊 Enrollment Summary by Subject:")
        cursor.execute("""
            SELECT s.subject_name, s.course_code, COUNT(se.student_id) as student_count
            FROM subjects_enhanced s
            LEFT JOIN student_enrollments_enhanced se ON s.subject_id = se.subject_id
            GROUP BY s.subject_id, s.subject_name, s.course_code
            ORDER BY student_count DESC, s.subject_name
        """)
        
        for subject_name, course_code, count in cursor.fetchall():
            print(f"  {subject_name} ({course_code}): {count} students")
        
        # Now update attendance records to only include enrolled students
        print("\n🔄 Updating attendance records to match enrollments...")
        
        # Delete attendance records for students not enrolled in the subject
        cursor.execute("""
            DELETE FROM attendance_records_enhanced 
            WHERE NOT EXISTS (
                SELECT 1 FROM student_enrollments_enhanced se 
                WHERE se.student_id = attendance_records_enhanced.student_id 
                AND se.subject_id = attendance_records_enhanced.subject_id
            )
        """)
        
        deleted_records = cursor.rowcount
        conn.commit()
        print(f"✅ Removed {deleted_records} attendance records for non-enrolled students")
        
        # Verify final attendance counts
        print("\n📊 Final Attendance Record Counts by Subject:")
        cursor.execute("""
            SELECT s.subject_name, s.course_code, COUNT(DISTINCT ar.student_id) as students_with_attendance
            FROM subjects_enhanced s
            LEFT JOIN attendance_records_enhanced ar ON s.subject_id = ar.subject_id
            GROUP BY s.subject_id, s.subject_name, s.course_code
            ORDER BY students_with_attendance DESC, s.subject_name
        """)
        
        for subject_name, course_code, count in cursor.fetchall():
            print(f"  {subject_name} ({course_code}): {count} students with attendance")
            
    except Exception as e:
        print(f"❌ Error generating realistic enrollments: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
    
    return True

if __name__ == "__main__":
    print("🎓 Egyptian University - Realistic Student Enrollment Generator")
    print("=" * 60)
    
    success = generate_realistic_enrollments()
    
    if success:
        print("\n✅ Realistic student enrollments generated successfully!")
        print("Each student now takes 4-6 subjects, and each subject has different student counts.")
    else:
        print("\n❌ Failed to generate realistic enrollments!")
