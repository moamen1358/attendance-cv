#!/usr/bin/env python3
"""
Quick setup script to add test students and prepare the database for face recognition
"""

import sqlite3
import json
import uuid
from datetime import datetime
import os

DATABASE_PATH = 'attendance_system.db'

def add_test_students():
    """Add some test students to the database"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        print("🎓 Adding test students...")
        
        # Sample students
        test_students = [
            {
                'name': 'John Smith',
                'roll_number': 'CS001',
                'email': 'john.smith@university.edu',
                'department': 'Computer Science',
                'year': 2,
                'section': 'A'
            },
            {
                'name': 'Alice Johnson',
                'roll_number': 'CS002', 
                'email': 'alice.johnson@university.edu',
                'department': 'Computer Science',
                'year': 2,
                'section': 'A'
            },
            {
                'name': 'Bob Wilson',
                'roll_number': 'CS003',
                'email': 'bob.wilson@university.edu', 
                'department': 'Computer Science',
                'year': 2,
                'section': 'B'
            },
            {
                'name': 'Emma Davis',
                'roll_number': 'CS004',
                'email': 'emma.davis@university.edu',
                'department': 'Computer Science', 
                'year': 3,
                'section': 'A'
            },
            {
                'name': 'Michael Brown',
                'roll_number': 'CS005',
                'email': 'michael.brown@university.edu',
                'department': 'Computer Science',
                'year': 3,
                'section': 'B'
            }
        ]
        
        for student in test_students:
            # Insert student
            cursor.execute("""
                INSERT OR REPLACE INTO students_enhanced 
                (name, roll_number, email, department, year, section, enrollment_date, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'active')
            """, (
                student['name'],
                student['roll_number'], 
                student['email'],
                student['department'],
                student['year'],
                student['section'],
                datetime.now().strftime('%Y-%m-%d')
            ))
            
            student_id = cursor.lastrowid
            print(f"✅ Added student: {student['name']} (ID: {student_id})")
            
            # Create a placeholder profile (without facial encoding for now)
            cursor.execute("""
                INSERT OR REPLACE INTO student_profiles_enhanced
                (student_id, profile_name, status, created_at)
                VALUES (?, ?, 'pending', ?)
            """, (student_id, student['name'], datetime.now().isoformat()))
            
            print(f"📝 Created profile placeholder for: {student['name']}")
        
        conn.commit()
        conn.close()
        
        print(f"\n✅ Successfully added {len(test_students)} test students!")
        print("📝 Next step: Use the face registration page to add facial encodings")
        
    except Exception as e:
        print(f"❌ Error adding test students: {e}")
        import traceback
        traceback.print_exc()

def show_database_status():
    """Show current database status"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        print("\n📊 DATABASE STATUS:")
        print("=" * 50)
        
        # Count students
        cursor.execute("SELECT COUNT(*) FROM students_enhanced;")
        student_count = cursor.fetchone()[0]
        print(f"👥 Total Students: {student_count}")
        
        # Count profiles
        cursor.execute("SELECT COUNT(*) FROM student_profiles_enhanced;")
        profile_count = cursor.fetchone()[0]
        print(f"📝 Total Profiles: {profile_count}")
        
        # Count profiles with encodings
        cursor.execute("SELECT COUNT(*) FROM student_profiles_enhanced WHERE encoding_data IS NOT NULL;")
        encoded_count = cursor.fetchone()[0]
        print(f"🎯 Profiles with Face Data: {encoded_count}")
        
        # Count attendance records
        cursor.execute("SELECT COUNT(*) FROM attendance_records_enhanced;")
        attendance_count = cursor.fetchone()[0]
        print(f"📋 Attendance Records: {attendance_count}")
        
        if student_count > 0:
            print("\n👥 Current Students:")
            cursor.execute("SELECT student_id, name, roll_number FROM students_enhanced LIMIT 5;")
            students = cursor.fetchall()
            for student in students:
                print(f"   - {student[1]} ({student[2]}) [ID: {student[0]}]")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking database status: {e}")

def main():
    print("🚀 Database Setup Utility")
    print("=" * 50)
    
    # Show current status
    show_database_status()
    
    # Check if we need to add students
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM students_enhanced;")
    student_count = cursor.fetchone()[0]
    conn.close()
    
    if student_count == 0:
        print(f"\n⚠️ No students found in database!")
        print("🔧 Adding test students...")
        add_test_students()
        show_database_status()
    else:
        print(f"\n✅ Database already has {student_count} students")
    
    print("\n📝 NEXT STEPS:")
    print("1. 🎯 Use the face registration page to capture student faces")
    print("2. 📷 This will generate facial encodings for recognition")
    print("3. 🚀 Then run the live attendance system")
    print("\n💡 The live attendance system needs facial encodings to work!")

if __name__ == "__main__":
    main()
