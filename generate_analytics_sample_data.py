#!/usr/bin/env python3
"""
Generate comprehensive sample attendance data for analytics
This script creates realistic attendance patterns for all students over the past 8 weeks
"""

import sqlite3
import random
from datetime import datetime, timedelta
import json

DATABASE_PATH = 'attendance_system.db'

def generate_analytics_sample_data():
    """Generate comprehensive attendance data for analytics"""
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        print("🔄 Generating analytics sample data...")
        
        # Get all students
        cursor.execute("SELECT student_id, name, department FROM students_enhanced")
        students = cursor.fetchall()
        print(f"📚 Found {len(students)} students")
        
        # Get all subjects and their schedules
        cursor.execute("""
            SELECT DISTINCT se.subject_id, se.subject_name, cs.day_of_week, cs.start_time, cs.end_time
            FROM subjects_enhanced se
            JOIN class_schedules_enhanced cs ON se.subject_id = cs.subject_id
            WHERE cs.status = 'active'
            ORDER BY se.subject_name, cs.day_of_week
        """)
        schedules = cursor.fetchall()
        print(f"📅 Found {len(schedules)} class schedules")
        
        # Generate data for the past 8 weeks
        end_date = datetime.now().date()
        start_date = end_date - timedelta(weeks=8)
        
        print(f"📊 Generating data from {start_date} to {end_date}")
        
        # Clear existing sample data (keep today's data)
        today_str = datetime.now().strftime('%Y-%m-%d')
        cursor.execute("""
            DELETE FROM attendance_records_enhanced 
            WHERE attendance_date != ? AND created_at < ?
        """, (today_str, datetime.now() - timedelta(hours=1)))
        
        records_added = 0
        
        # For each student
        for student_id, student_name, department in students:
            print(f"👤 Processing {student_name} ({department})")
            
            # Get subjects this student is enrolled in
            cursor.execute("""
                SELECT se.subject_id, se.subject_name
                FROM student_enrollments_enhanced sen
                JOIN subjects_enhanced se ON sen.subject_id = se.subject_id
                WHERE sen.student_id = ? AND sen.status = 'active'
            """, (student_id,))
            student_subjects = cursor.fetchall()
            
            # Create attendance patterns based on student personality
            # Some students are very regular, others have patterns
            student_reliability = random.choice([
                'excellent',    # 90-95% attendance
                'good',         # 80-90% attendance  
                'average',      # 70-80% attendance
                'irregular',    # 60-75% attendance
                'poor'          # 40-60% attendance
            ])
            
            # Generate weekly patterns (some students skip Mondays, others skip Fridays)
            weekly_pattern = {
                'Monday': random.uniform(0.7, 1.0),
                'Tuesday': random.uniform(0.8, 1.0),
                'Wednesday': random.uniform(0.8, 1.0),
                'Thursday': random.uniform(0.8, 1.0),
                'Friday': random.uniform(0.6, 0.9),
                'Saturday': random.uniform(0.5, 0.8),
                'Sunday': random.uniform(0.7, 0.9)
            }
            
            # Set base attendance rate based on reliability
            base_rates = {
                'excellent': 0.92,
                'good': 0.85,
                'average': 0.75,
                'irregular': 0.68,
                'poor': 0.50
            }
            base_rate = base_rates[student_reliability]
            
            # Generate attendance for each day in the period
            current_date = start_date
            while current_date <= end_date:
                day_name = current_date.strftime('%A')
                
                # Skip today (we already have real data for today)
                if current_date.strftime('%Y-%m-%d') == today_str:
                    current_date += timedelta(days=1)
                    continue
                
                # For each subject this student is enrolled in
                for subject_id, subject_name in student_subjects:
                    # Check if there's a class for this subject on this day
                    subject_schedules = [s for s in schedules if s[0] == subject_id and s[2] == day_name]
                    
                    for schedule in subject_schedules:
                        schedule_subject_id, schedule_subject_name, day_of_week, start_time, end_time = schedule
                        
                        # Calculate attendance probability
                        day_modifier = weekly_pattern[day_name]
                        
                        # Add some randomness for special events
                        if random.random() < 0.05:  # 5% chance of special event
                            # Special events: exam days (higher attendance), holidays (lower attendance)
                            event_modifier = random.choice([1.2, 0.3])  # Exam day or holiday
                        else:
                            event_modifier = 1.0
                        
                        # Calculate final probability
                        attendance_prob = base_rate * day_modifier * event_modifier
                        attendance_prob = min(1.0, max(0.0, attendance_prob))  # Clamp between 0 and 1
                        
                        # Determine if student attended
                        attended = random.random() < attendance_prob
                        status = 'present' if attended else 'absent'
                        
                        # Create timestamp for this attendance record
                        # Make it look realistic - sometime during the class period
                        class_start = datetime.strptime(f"{current_date} {start_time}", '%Y-%m-%d %H:%M')
                        class_end = datetime.strptime(f"{current_date} {end_time}", '%Y-%m-%d %H:%M')
                        
                        # Random time during class (for attendance marking)
                        time_diff = class_end - class_start
                        random_offset = timedelta(minutes=random.randint(5, int(time_diff.total_seconds()/60) - 5))
                        record_time = class_start + random_offset
                        
                        # Insert attendance record
                        cursor.execute("""
                            INSERT INTO attendance_records_enhanced 
                            (student_id, subject_id, attendance_date, status, created_at)
                            VALUES (?, ?, ?, ?, ?)
                        """, (
                            student_id,
                            subject_id,
                            current_date.strftime('%Y-%m-%d'),
                            status,
                            record_time.strftime('%Y-%m-%d %H:%M:%S')
                        ))
                        records_added += 1
                
                current_date += timedelta(days=1)
        
        # Commit all changes
        conn.commit()
        print(f"✅ Successfully added {records_added} attendance records!")
        
        # Show some statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_records,
                COUNT(CASE WHEN status = 'present' THEN 1 END) as present_count,
                COUNT(CASE WHEN status = 'absent' THEN 1 END) as absent_count,
                ROUND(COUNT(CASE WHEN status = 'present' THEN 1 END) * 100.0 / COUNT(*), 1) as attendance_rate
            FROM attendance_records_enhanced
            WHERE attendance_date >= ?
        """, (start_date.strftime('%Y-%m-%d'),))
        
        stats = cursor.fetchone()
        print(f"📈 Overall Statistics:")
        print(f"   Total Records: {stats[0]}")
        print(f"   Present: {stats[1]}")
        print(f"   Absent: {stats[2]}")
        print(f"   Overall Attendance Rate: {stats[3]}%")
        
        # Show per-student stats for a few students
        print(f"\n👥 Sample Student Statistics:")
        for student_id, student_name, department in students[:5]:
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN status = 'present' THEN 1 END) as present,
                    ROUND(COUNT(CASE WHEN status = 'present' THEN 1 END) * 100.0 / COUNT(*), 1) as rate
                FROM attendance_records_enhanced
                WHERE student_id = ? AND attendance_date >= ?
            """, (student_id, start_date.strftime('%Y-%m-%d')))
            
            student_stats = cursor.fetchone()
            print(f"   {student_name}: {student_stats[2]}% ({student_stats[1]}/{student_stats[0]})")
        
    except Exception as e:
        print(f"❌ Error generating sample data: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    generate_analytics_sample_data()
