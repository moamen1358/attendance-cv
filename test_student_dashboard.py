#!/usr/bin/env python3
"""Test script for student dashboard functions"""

import sqlite3
import sys

DATABASE_PATH = 'attendance_system.db'

def get_student_info(username):
    """Get student information from enhanced database"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get from enhanced tables using proper joins
        cursor.execute("""
            SELECT s.student_id, s.name, s.roll_number, s.department, 
                   s.year, s.section, s.email, s.phone, u.full_name
            FROM users_enhanced u
            JOIN students_enhanced s ON u.linked_id = s.student_id
            WHERE u.username = ? AND u.role = 'student'
        """, (username,))
        
        result = cursor.fetchone()
        if result:
            return {
                'id': result[0],
                'name': result[1],
                'student_id': result[2],
                'department': result[3],
                'academic_year': result[4],
                'section': result[5],
                'email': result[6],
                'phone': result[7],
                'gpa': None  # GPA not stored in current schema
            }
        
        return None
        
    except Exception as e:
        print(f"Error getting student info: {e}")
        return None
    finally:
        conn.close()

def get_student_subjects(student_id):
    """Get subjects enrolled by the student"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get enrolled subjects through enhanced tables
        cursor.execute("""
            SELECT DISTINCT se.subject_id, se.subject_name, se.course_code, se.credit_hours, 
                   se.description, se.semester, cs.room_number as room, cs.day_of_week, cs.start_time, cs.end_time,
                   en.status, en.grade, 
                   COALESCE(att.attendance_percentage, 0) as attendance_percentage
            FROM student_enrollments_enhanced en
            JOIN subjects_enhanced se ON en.subject_id = se.subject_id  
            LEFT JOIN class_schedules_enhanced cs ON se.subject_id = cs.subject_id
            LEFT JOIN (
                SELECT subject_id, student_id, 
                       ROUND(AVG(CASE WHEN status = 'present' THEN 100.0 ELSE 0.0 END), 1) as attendance_percentage
                FROM attendance_records_enhanced 
                WHERE student_id = ?
                GROUP BY subject_id, student_id
            ) att ON se.subject_id = att.subject_id AND en.student_id = att.student_id
            WHERE en.student_id = ? AND en.status = 'active'
            ORDER BY se.subject_name
        """, (student_id, student_id))
        
        subjects = cursor.fetchall()
        
        subject_list = []
        for subject in subjects:
            subject_list.append({
                'id': subject[0],
                'name': subject[1],
                'course_code': subject[2],
                'credit_hours': subject[3],
                'description': subject[4],
                'section': subject[5],  # semester
                'room': subject[6],
                'schedule_days': subject[7],  # day_of_week
                'start_time': subject[8],
                'end_time': subject[9],
                'status': subject[10],
                'grade': subject[11],
                'attendance_percentage': subject[12]
            })
        
        return subject_list
        
    except Exception as e:
        print(f"Error getting student subjects: {e}")
        return []
    finally:
        conn.close()

def get_student_attendance(student_name, limit_days=30):
    """Get student attendance records from enhanced database"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get student ID from students_enhanced table
        cursor.execute("SELECT student_id FROM students_enhanced WHERE name = ?", (student_name,))
        student_result = cursor.fetchone()
        if not student_result:
            return []
        student_id = student_result[0]
        
        # Get attendance from the last N days (or all records if limit_days is high)
        cursor.execute("""
            SELECT ar.created_at as timestamp, ar.subject_id, se.subject_name, ar.status, ar.attendance_date
            FROM attendance_records_enhanced ar
            LEFT JOIN subjects_enhanced se ON ar.subject_id = se.subject_id
            WHERE ar.student_id = ?
            ORDER BY ar.attendance_date DESC, ar.attendance_time DESC
            LIMIT ?
        """, (student_id, limit_days * 10))  # Assume max 10 classes per day
        
        attendance = cursor.fetchall()
        
        attendance_list = []
        for record in attendance:
            attendance_list.append({
                'timestamp': record[0],
                'subject_id': record[1],
                'subject_name': record[2] or 'Unknown Subject',
                'status': record[3],
                'class_date': record[4]
            })
        
        return attendance_list
        
    except Exception as e:
        print(f"Error getting attendance: {e}")
        return []
    finally:
        conn.close()

if __name__ == "__main__":
    # Test with a sample student
    username = '2024001'  # Fatma Khaled Ibrahim
    print(f'Testing with username: {username}')

    # Test get_student_info
    print('\n=== Testing get_student_info ===')
    student_info = get_student_info(username)
    print(f'Student info: {student_info}')

    if student_info:
        # Test get_student_subjects
        print('\n=== Testing get_student_subjects ===')
        subjects = get_student_subjects(student_info['id'])
        print(f'Found {len(subjects)} subjects')
        for subject in subjects[:2]:  # Show first 2 subjects
            print(f'  - {subject["name"]} ({subject["course_code"]}): {subject["attendance_percentage"]}% attendance')
        
        # Test get_student_attendance
        print('\n=== Testing get_student_attendance ===')
        attendance = get_student_attendance(student_info['name'])
        print(f'Found {len(attendance)} attendance records')
        for record in attendance[:3]:  # Show first 3 records
            print(f'  - {record["class_date"]}: {record["subject_name"]} - {record["status"]}')
    else:
        print("Student info not found!")
