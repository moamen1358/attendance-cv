#!/usr/bin/env python3
"""
Script to enroll students in subjects and assign them to sections
so they can see their class schedules
"""

import sqlite3
import random

DATABASE_PATH = 'attendance_system.db'

def get_db_connection():
    """Get a connection to the SQLite database"""
    return sqlite3.connect(DATABASE_PATH)

def assign_students_to_sections():
    """Assign students to sections and enroll them in subjects"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get all students
        cursor.execute("SELECT username, full_name FROM users_enhanced WHERE role='student'")
        students = cursor.fetchall()
        
        # Get students from the enhanced table
        cursor.execute("SELECT student_id, name FROM students_enhanced")
        students_enhanced = cursor.fetchall()
        
        # Update students_enhanced table with section assignments
        sections = ['A', 'B', 'C']
        
        print("Assigning students to sections...")
        for student_id, name in students_enhanced:
            section = random.choice(sections)
            
            # Update the section in students_enhanced table
            cursor.execute("""
                UPDATE students_enhanced 
                SET section = ? 
                WHERE student_id = ?
            """, (section, student_id))
            
            print(f"Assigned {name} to Section {section}")
        
        # Get all subjects
        cursor.execute("SELECT subject_id, subject_name FROM subjects_enhanced")
        subjects = cursor.fetchall()
        
        # Clear existing enrollments
        cursor.execute("DELETE FROM student_enrollments_enhanced")
        print("\nCleared existing enrollments")
        
        # Enroll each student in subjects based on their section's schedule
        print("\nEnrolling students in subjects...")
        
        for student_id, name in students_enhanced:
            # Get the student's section
            cursor.execute("SELECT section FROM students_enhanced WHERE student_id = ?", (student_id,))
            section_result = cursor.fetchone()
            if not section_result:
                continue
            section = section_result[0]
            
            # Get subjects scheduled for this section
            cursor.execute("""
                SELECT DISTINCT subject_id 
                FROM class_schedules_enhanced 
                WHERE section = ?
            """, (section,))
            
            section_subjects = cursor.fetchall()
            
            # Enroll student in all subjects for their section
            for (subject_id,) in section_subjects:
                try:
                    cursor.execute("""
                        INSERT INTO student_enrollments_enhanced 
                        (student_id, subject_id, academic_year, semester, status)
                        VALUES (?, ?, ?, ?, ?)
                    """, (student_id, subject_id, '2024-2025', 'Fall', 'enrolled'))
                    
                    # Get subject name for logging
                    cursor.execute("SELECT subject_name FROM subjects_enhanced WHERE subject_id = ?", (subject_id,))
                    subject_name = cursor.fetchone()[0]
                    print(f"Enrolled {name} (Section {section}) in {subject_name}")
                    
                except sqlite3.IntegrityError:
                    # Student already enrolled in this subject
                    pass
        
        # Commit all changes
        conn.commit()
        print(f"\nSuccessfully assigned students to sections and enrolled them in subjects!")
        
        # Show summary
        cursor.execute("SELECT COUNT(*) FROM student_enrollments_enhanced")
        total_enrollments = cursor.fetchone()[0]
        print(f"Total enrollments created: {total_enrollments}")
        
        # Show example for Fatma Khaled Ibrahim
        cursor.execute("""
            SELECT s.subject_name, cs.day_of_week, cs.start_time, cs.end_time, cs.room_number
            FROM student_enrollments_enhanced se
            JOIN subjects_enhanced s ON se.subject_id = s.subject_id
            JOIN students_enhanced st ON se.student_id = st.student_id
            JOIN class_schedules_enhanced cs ON se.subject_id = cs.subject_id AND st.section = cs.section
            WHERE st.name = 'Fatma Khaled Ibrahim'
            ORDER BY 
                CASE cs.day_of_week 
                    WHEN 'Sunday' THEN 1
                    WHEN 'Monday' THEN 2
                    WHEN 'Tuesday' THEN 3
                    WHEN 'Wednesday' THEN 4
                    WHEN 'Thursday' THEN 5
                END,
                cs.start_time
        """)
        
        print(f"\nSchedule for Fatma Khaled Ibrahim:")
        for row in cursor.fetchall():
            subject, day, start, end, room = row
            print(f"{day}: {subject} at {start}-{end} in {room}")
            
    except Exception as e:
        print(f"Error assigning students: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    assign_students_to_sections()
