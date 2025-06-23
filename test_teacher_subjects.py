#!/usr/bin/env python3
"""
Test Teacher Subject Retrieval Script
"""

import sqlite3

def get_teacher_subjects_direct(username):
    """Direct test of teacher subject retrieval"""
    conn = sqlite3.connect('attendance_system.db')
    cursor = conn.cursor()
    
    try:
        # First, get the teacher's linked_id from users_enhanced
        cursor.execute("""
            SELECT linked_id 
            FROM users_enhanced 
            WHERE username = ? AND role = 'teacher'
        """, (username,))
        
        result = cursor.fetchone()
        if not result:
            print(f"Teacher {username} not found in users_enhanced table")
            return []
        
        teacher_id = result[0]
        
        # Get subjects from teacher_subjects_enhanced table
        cursor.execute("""
            SELECT s.subject_name, s.course_code
            FROM teacher_subjects_enhanced ts
            JOIN subjects_enhanced s ON ts.subject_id = s.subject_id
            WHERE ts.teacher_id = ? AND ts.status = 'active'
            ORDER BY s.subject_name
        """, (teacher_id,))
        
        subjects = [f"{row[0]} ({row[1]})" for row in cursor.fetchall()]
        
        if subjects:
            print(f"Found {len(subjects)} subjects for teacher {username}: {subjects}")
            return subjects
        
        print(f"No subjects found for teacher {username} (teacher_id: {teacher_id})")
        return []
        
    except Exception as e:
        print(f"Error in get_teacher_subjects for {username}: {e}")
        return []
    finally:
        conn.close()

def test_teacher_subjects():
    """Test teacher subject retrieval for a few teachers"""
    
    test_teachers = ['emp2024001', 'emp2024003', 'emp2024005', 'emp2024009']
    
    print("🧪 Testing Teacher Subject Retrieval")
    print("=" * 40)
    
    for teacher_username in test_teachers:
        print(f"\n👨‍🏫 Testing teacher: {teacher_username}")
        subjects = get_teacher_subjects_direct(teacher_username)
        
        if subjects:
            print(f"  ✅ Found {len(subjects)} subjects:")
            for subject in subjects:
                print(f"    - {subject}")
        else:
            print("  ❌ No subjects found")
    
    print("\n" + "=" * 40)
    print("✅ Teacher subject retrieval test completed!")

if __name__ == "__main__":
    test_teacher_subjects()
