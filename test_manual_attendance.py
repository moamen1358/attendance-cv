#!/usr/bin/env python3
"""Test manual attendance entry and student dashboard refresh"""

import sqlite3
from datetime import datetime

DATABASE_PATH = 'attendance_system.db'

def add_test_attendance():
    """Add a test attendance record for today"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        student_id = 111  # Fatma Khaled Ibrahim
        subject_id = 118  # Marketing
        today = datetime.now().strftime('%Y-%m-%d')
        current_time = datetime.now().strftime('%H:%M:%S')
        
        # Check if record already exists for today
        cursor.execute("""
            SELECT id FROM attendance_records_enhanced 
            WHERE student_id = ? AND subject_id = ? AND attendance_date = ?
        """, (student_id, subject_id, today))
        
        existing_record = cursor.fetchone()
        
        if existing_record:
            # Update existing record
            cursor.execute("""
                UPDATE attendance_records_enhanced 
                SET status = 'present', attendance_time = ?, notes = 'Manual test entry', 
                    marked_by = 'test_teacher', created_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (current_time, existing_record[0]))
            print(f"Updated existing attendance record for student {student_id} on {today}")
        else:
            # Get teacher_id for this subject
            cursor.execute("""
                SELECT teacher_id FROM teacher_subjects_enhanced 
                WHERE subject_id = ? LIMIT 1
            """, (subject_id,))
            teacher_result = cursor.fetchone()
            teacher_id = teacher_result[0] if teacher_result else 1
            
            # Create new record
            cursor.execute("""
                INSERT INTO attendance_records_enhanced 
                (student_id, subject_id, teacher_id, attendance_date, attendance_time, 
                 status, marked_by, notes, academic_year, semester, created_at)
                VALUES (?, ?, ?, ?, ?, 'present', 'test_teacher', 'Manual test entry', '2024-2025', 'Fall', CURRENT_TIMESTAMP)
            """, (student_id, subject_id, teacher_id, today, current_time))
            print(f"Added new attendance record for student {student_id} on {today}")
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error adding test attendance: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_student_recent_attendance():
    """Get recent attendance for the test student"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        student_id = 111  # Fatma Khaled Ibrahim
        
        cursor.execute("""
            SELECT ar.attendance_date, se.subject_name, ar.status, ar.attendance_time, ar.notes, ar.created_at
            FROM attendance_records_enhanced ar
            LEFT JOIN subjects_enhanced se ON ar.subject_id = se.subject_id
            WHERE ar.student_id = ?
            ORDER BY ar.created_at DESC
            LIMIT 5
        """, (student_id,))
        
        records = cursor.fetchall()
        
        print(f"Recent attendance records for student {student_id}:")
        for record in records:
            print(f"  - {record[0]} {record[3]}: {record[1]} - {record[2]} (notes: {record[4] or 'None'}) [Created: {record[5]}]")
        
        return records
    except Exception as e:
        print(f"Error getting attendance: {e}")
        return []
    finally:
        conn.close()

if __name__ == "__main__":
    print("=== Before adding test attendance ===")
    get_student_recent_attendance()
    
    print("\n=== Adding test attendance for today ===")
    success = add_test_attendance()
    
    if success:
        print("\n=== After adding test attendance ===")
        get_student_recent_attendance()
    else:
        print("Failed to add test attendance")
