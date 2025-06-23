#!/usr/bin/env python3
"""
Generate Realistic Class Schedules and Attendance
- 15 classes per subject per term (weekly classes over 15 weeks)
- Each subject meets once per week
- More realistic attendance patterns
"""

import sqlite3
import random
from datetime import datetime, timedelta

def generate_realistic_attendance():
    """Generate realistic attendance data with 15 classes per subject per term"""
    
    conn = sqlite3.connect('attendance_system.db')
    cursor = conn.cursor()
    
    try:
        print("🧹 Clearing existing attendance records...")
        cursor.execute("DELETE FROM attendance_records_enhanced")
        conn.commit()
        
        # Get all subjects with their enrolled students and assigned teachers
        cursor.execute("""
            SELECT s.subject_id, s.subject_name, s.course_code,
                   GROUP_CONCAT(se.student_id) as student_ids,
                   ts.teacher_id
            FROM subjects_enhanced s
            JOIN student_enrollments_enhanced se ON s.subject_id = se.subject_id
            LEFT JOIN teacher_subjects_enhanced ts ON s.subject_id = ts.subject_id
            GROUP BY s.subject_id, s.subject_name, s.course_code, ts.teacher_id
        """)
        subjects_data = cursor.fetchall()
        
        print(f"📚 Processing {len(subjects_data)} subjects...")
        
        # Define semester start date (September 2024)
        semester_start = datetime(2024, 9, 1)
        
        total_records = 0
        
        for subject_id, subject_name, course_code, student_ids_str, teacher_id in subjects_data:
            if not student_ids_str:
                print(f"⚠️ No students enrolled in {subject_name}, skipping...")
                continue
                
            # Use teacher_id if available, otherwise use 1 as default
            actual_teacher_id = teacher_id if teacher_id else 1
                
            student_ids = [int(sid) for sid in student_ids_str.split(',')]
            print(f"\n📖 Processing {subject_name} ({course_code}) with {len(student_ids)} students, teacher_id: {actual_teacher_id}")
            
            # Generate 15 class dates (weekly classes)
            class_dates = []
            current_date = semester_start
            
            for week in range(15):  # 15 weeks of classes
                # Add some randomness to avoid all classes on the same day
                day_offset = random.randint(0, 4)  # Monday to Friday
                class_date = current_date + timedelta(days=day_offset, weeks=week)
                class_dates.append(class_date.date())
            
            print(f"  📅 Generated {len(class_dates)} class dates from {class_dates[0]} to {class_dates[-1]}")
            
            # Generate attendance for each student for each class
            subject_records = 0
            for student_id in student_ids:
                # Create a student profile for attendance patterns
                # Some students are regular (85% attendance), some irregular (60%), some poor (40%)
                attendance_pattern = random.choices(
                    ['regular', 'irregular', 'poor'], 
                    weights=[60, 30, 10], 
                    k=1
                )[0]
                
                if attendance_pattern == 'regular':
                    base_attendance_rate = 0.85
                elif attendance_pattern == 'irregular':
                    base_attendance_rate = 0.60
                else:  # poor
                    base_attendance_rate = 0.40
                
                for class_date in class_dates:
                    # Add some randomness around the base rate
                    attendance_probability = base_attendance_rate + random.uniform(-0.15, 0.15)
                    attendance_probability = max(0.1, min(0.95, attendance_probability))  # Clamp between 10% and 95%
                    
                    status = 'present' if random.random() < attendance_probability else 'absent'
                    
                    # Generate realistic class times
                    class_hour = random.choice([8, 9, 10, 11, 12, 13, 14, 15, 16])
                    class_time = f"{class_hour:02d}:00:00"
                    
                    cursor.execute("""
                        INSERT INTO attendance_records_enhanced 
                        (student_id, subject_id, teacher_id, attendance_date, attendance_time, status, 
                         academic_year, semester, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, (student_id, subject_id, actual_teacher_id, class_date, class_time, status, '2024-2025', 'Fall'))
                    
                    subject_records += 1
                    total_records += 1
            
            print(f"  ✅ Created {subject_records} attendance records for {subject_name}")
        
        conn.commit()
        print(f"\n🎉 Successfully generated {total_records} realistic attendance records!")
        
        # Show summary statistics
        print("\n📊 Summary by Subject:")
        cursor.execute("""
            SELECT s.subject_name, 
                   COUNT(DISTINCT se.student_id) as students,
                   COUNT(DISTINCT ar.attendance_date) as classes,
                   COUNT(*) as total_records,
                   ROUND(AVG(CASE WHEN ar.status = 'present' THEN 1.0 ELSE 0.0 END) * 100, 1) as avg_attendance
            FROM subjects_enhanced s
            JOIN student_enrollments_enhanced se ON s.subject_id = se.subject_id
            JOIN attendance_records_enhanced ar ON s.subject_id = ar.subject_id
            GROUP BY s.subject_id, s.subject_name
            ORDER BY s.subject_name
        """)
        
        for subject_name, students, classes, records, avg_attendance in cursor.fetchall():
            print(f"  {subject_name}: {students} students, {classes} classes, {records} records, {avg_attendance}% attendance")
            
    except Exception as e:
        print(f"❌ Error generating attendance data: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
    
    return True

if __name__ == "__main__":
    print("🏫 Egyptian University - Realistic Attendance Data Generation")
    print("=" * 60)
    
    success = generate_realistic_attendance()
    
    if success:
        print("\n✅ Realistic attendance data generation completed!")
        print("Each subject now has ~15 classes per term with realistic attendance patterns.")
    else:
        print("\n❌ Attendance data generation failed!")
