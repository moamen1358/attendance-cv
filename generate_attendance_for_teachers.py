#!/usr/bin/env python3
"""
Generate Realistic Attendance Data for All Teacher Subjects

This script generates attendance records for all subjects assigned to teachers
to ensure each teacher has realistic and unique attendance statistics.
"""

import sqlite3
import random
from datetime import datetime, timedelta
import os

def generate_attendance_for_missing_subjects():
    """Generate attendance data for subjects that are assigned to teachers but missing attendance records"""
    
    conn = sqlite3.connect('attendance_system.db')
    cursor = conn.cursor()
    
    try:
        # Get subjects assigned to teachers but missing attendance data
        cursor.execute("""
            SELECT DISTINCT s.subject_id, s.subject_name 
            FROM teacher_subjects_enhanced ts 
            JOIN subjects_enhanced s ON ts.subject_id = s.subject_id 
            WHERE s.subject_name NOT IN (
                SELECT DISTINCT sub.subject_name 
                FROM attendance_records_enhanced ar 
                JOIN subjects_enhanced sub ON ar.subject_id = sub.subject_id
            )
            ORDER BY s.subject_name
        """)
        
        missing_subjects = cursor.fetchall()
        print(f"Found {len(missing_subjects)} subjects missing attendance data:")
        for subject_id, subject_name in missing_subjects:
            print(f"  - {subject_name} (ID: {subject_id})")
        
        # Get all students
        cursor.execute("SELECT student_id, name FROM students_enhanced ORDER BY student_id")
        students = cursor.fetchall()
        print(f"Found {len(students)} students")
        
        # Generate attendance data for each missing subject
        total_records = 0
        
        for subject_id, subject_name in missing_subjects:
            print(f"\nGenerating attendance for {subject_name}...")
            
            # Generate different class frequencies for different subjects
            if "Project" in subject_name or "Management" in subject_name:
                classes_per_week = 1  # Once per week
            elif "Statistics" in subject_name or "Accounting" in subject_name:
                classes_per_week = 2  # Twice per week
            else:
                classes_per_week = 3  # Three times per week (default for most subjects)
            
            # Generate classes from September 2024 to May 2025 (academic year)
            start_date = datetime(2024, 9, 1)
            end_date = datetime(2025, 5, 31)
            
            # Generate class dates based on frequency
            class_dates = []
            current_date = start_date
            
            while current_date <= end_date:
                # Skip weekends for most subjects
                if current_date.weekday() < 5:  # Monday = 0, Friday = 4
                    # Add classes based on frequency
                    if classes_per_week == 1:
                        if current_date.weekday() == 1:  # Tuesday only
                            class_dates.append(current_date)
                    elif classes_per_week == 2:
                        if current_date.weekday() in [1, 3]:  # Tuesday and Thursday
                            class_dates.append(current_date)
                    else:  # 3 times per week
                        if current_date.weekday() in [0, 2, 4]:  # Monday, Wednesday, Friday
                            class_dates.append(current_date)
                
                current_date += timedelta(days=1)
            
            print(f"  Generated {len(class_dates)} class dates")
            
            # Create attendance records for each student for each class
            subject_records = 0
            for student_id, student_name in students:
                # Create different attendance patterns for different students
                base_attendance_rate = random.uniform(0.65, 0.95)  # 65% to 95% base rate
                
                for class_date in class_dates:
                    # Add some randomness to attendance
                    attendance_probability = base_attendance_rate + random.uniform(-0.1, 0.1)
                    attendance_probability = max(0.0, min(1.0, attendance_probability))  # Clamp to 0-1
                    
                    status = 'present' if random.random() < attendance_probability else 'absent'
                    
                    # Insert attendance record
                    cursor.execute("""
                        INSERT INTO attendance_records_enhanced 
                        (student_id, subject_id, attendance_date, status, created_at)
                        VALUES (?, ?, ?, ?, ?)
                    """, (student_id, subject_id, class_date.date(), status, datetime.now()))
                    
                    subject_records += 1
            
            total_records += subject_records
            print(f"  Created {subject_records} attendance records")
        
        conn.commit()
        print(f"\n🎉 Successfully generated {total_records} attendance records for {len(missing_subjects)} subjects!")
        
        # Verify the results
        print("\n📊 Verification - Attendance summary by subject:")
        cursor.execute("""
            SELECT sub.subject_name, 
                   COUNT(*) as total_records,
                   COUNT(CASE WHEN ar.status = 'present' THEN 1 END) as present_count,
                   COUNT(CASE WHEN ar.status = 'present' THEN 1 END) * 100.0 / COUNT(*) as attendance_rate
            FROM attendance_records_enhanced ar
            JOIN subjects_enhanced sub ON ar.subject_id = sub.subject_id
            GROUP BY sub.subject_name
            ORDER BY sub.subject_name
        """)
        
        for subject_name, total, present, rate in cursor.fetchall():
            print(f"  {subject_name}: {present}/{total} ({rate:.1f}%)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error generating attendance data: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("🏫 Egyptian University - Attendance Data Generator")
    print("=" * 55)
    
    success = generate_attendance_for_missing_subjects()
    
    if success:
        print("\n✅ Attendance data generation completed successfully!")
        print("All teachers should now have realistic attendance statistics.")
    else:
        print("\n❌ Attendance data generation failed!")
