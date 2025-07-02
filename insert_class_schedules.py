#!/usr/bin/env python3
"""
Script to insert class schedule data into the class_schedules_enhanced table
ensuring each student has at least 2 subjects per day
"""

import sqlite3
import random
from datetime import datetime

DATABASE_PATH = 'attendance_system.db'

def get_db_connection():
    """Get a connection to the SQLite database"""
    return sqlite3.connect(DATABASE_PATH)

def insert_class_schedules():
    """Insert class schedule data for students"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get available subjects and teachers
        cursor.execute("SELECT subject_id, subject_name FROM subjects_enhanced")
        subjects = cursor.fetchall()
        
        cursor.execute("SELECT teacher_id, name FROM teachers_enhanced")
        teachers = cursor.fetchall()
        
        # Define days of the week
        days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday']
        
        # Define time slots (8 AM to 4 PM)
        time_slots = [
            ('08:00', '09:30'),
            ('09:45', '11:15'),
            ('11:30', '13:00'),
            ('13:15', '14:45'),
            ('15:00', '16:30')
        ]
        
        # Room numbers
        rooms = ['A101', 'A102', 'A103', 'B201', 'B202', 'B203', 'C301', 'C302', 'C303', 'Lab1', 'Lab2']
        
        # Class types
        class_types = ['lecture', 'tutorial', 'lab']
        
        # Sections
        sections = ['A', 'B', 'C']
        
        # Clear existing schedule data
        cursor.execute("DELETE FROM class_schedules_enhanced")
        print("Cleared existing class schedules")
        
        schedule_id = 1
        
        # For each day, ensure we have at least 2 subjects
        for day in days:
            for section in sections:
                # Select subjects for this day and section
                selected_subjects = random.sample(subjects, min(3, len(subjects)))  # 3 subjects per day
                
                for i, (subject_id, subject_name) in enumerate(selected_subjects):
                    # Select a random teacher
                    teacher_id, teacher_name = random.choice(teachers)
                    
                    # Select time slot
                    start_time, end_time = time_slots[i]
                    
                    # Select room
                    room = random.choice(rooms)
                    
                    # Select class type
                    class_type = random.choice(class_types)
                    
                    # Insert the schedule
                    cursor.execute("""
                        INSERT INTO class_schedules_enhanced 
                        (subject_id, teacher_id, day_of_week, start_time, end_time, 
                         room_number, class_type, section, academic_year, semester, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        subject_id, teacher_id, day, start_time, end_time,
                        room, class_type, section, '2024-2025', 'Fall', 'active'
                    ))
                    
                    print(f"Added {subject_name} for Section {section} on {day} at {start_time}-{end_time} in {room} with {teacher_name}")
        
        # Commit the changes
        conn.commit()
        print(f"\nSuccessfully inserted class schedules for all days and sections!")
        
        # Show summary
        cursor.execute("SELECT COUNT(*) FROM class_schedules_enhanced")
        total_schedules = cursor.fetchone()[0]
        print(f"Total class schedules created: {total_schedules}")
        
        # Show schedule for Wednesday as an example
        cursor.execute("""
            SELECT s.subject_name, t.name, cs.start_time, cs.end_time, cs.room_number, cs.section
            FROM class_schedules_enhanced cs
            JOIN subjects_enhanced s ON cs.subject_id = s.subject_id
            JOIN teachers_enhanced t ON cs.teacher_id = t.teacher_id
            WHERE cs.day_of_week = 'Wednesday'
            ORDER BY cs.section, cs.start_time
        """)
        
        print("\nWednesday Schedule Preview:")
        for row in cursor.fetchall():
            subject, teacher, start, end, room, section = row
            print(f"Section {section}: {subject} with {teacher} at {start}-{end} in {room}")
            
    except Exception as e:
        print(f"Error inserting class schedules: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    insert_class_schedules()
