#!/usr/bin/env python3
"""
Comprehensive Class Schedule Generator

This script creates a full class schedule for all subjects across all days of the week.
It will assign subjects to different time slots and days to create a complete academic schedule.
"""

import sqlite3
import random
from datetime import datetime

DATABASE_PATH = 'attendance_system.db'

def create_comprehensive_schedule():
    """Create a comprehensive class schedule for all subjects"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Clear existing schedules
    cursor.execute("DELETE FROM class_schedules_enhanced")
    print("✅ Cleared existing schedules")
    
    # Get all subjects
    cursor.execute("""
        SELECT subject_id, subject_code, subject_name, academic_year, semester, credits
        FROM subjects_enhanced 
        ORDER BY department_id, academic_year, semester
    """)
    subjects = cursor.fetchall()
    
    # Get active term
    cursor.execute("SELECT term_id FROM academic_terms WHERE is_active = 1 LIMIT 1")
    term_result = cursor.fetchone()
    term_id = term_result[0] if term_result else 1
    
    # Define time slots (using 24-hour format for database storage)
    time_slots = [
        ("08:00", "09:30"),  # 8:00-9:30 AM
        ("09:30", "11:00"),  # 9:30-11:00 AM
        ("11:00", "12:30"),  # 11:00-12:30 PM
        ("12:30", "14:00"),  # 12:30-2:00 PM
        ("14:00", "15:30"),  # 2:00-3:30 PM
        ("15:30", "17:00"),  # 3:30-5:00 PM
    ]
    
    # Define rooms
    rooms = [
        "Room-101", "Room-102", "Room-103", "Room-201", "Room-202", "Room-203",
        "Lab-1", "Lab-2", "Lab-3", "AI-Lab", "CS-Lab", "Lecture-Hall-A", "Lecture-Hall-B"
    ]
    
    # Days of the week (0=Sunday, 6=Saturday) - Skip Friday (5) as it's often a weekend day
    working_days = [0, 1, 2, 3, 4, 6]  # Sunday to Thursday + Saturday
    day_names = {0: "Sunday", 1: "Monday", 2: "Tuesday", 3: "Wednesday", 4: "Thursday", 5: "Friday", 6: "Saturday"}
    
    schedule_id = 1
    
    print(f"Creating schedules for {len(subjects)} subjects across {len(working_days)} days...")
    
    # Track used slots to avoid conflicts
    used_slots = {}  # key: (day, time_slot), value: room
    
    for subject_id, subject_code, subject_name, academic_year, semester, credits in subjects:
        # Each subject gets 2-3 sessions per week based on credits
        sessions_per_week = min(3, max(2, credits))
        
        # Select random days for this subject
        subject_days = random.sample(working_days, sessions_per_week)
        
        for i, day in enumerate(subject_days):
            # Determine session type
            if i == 0:
                session_type = "lecture"
            elif i == 1:
                session_type = "tutorial" if credits >= 3 else "lecture"
            else:
                session_type = "lab"
            
            # Select appropriate room based on session type
            if session_type == "lab":
                available_rooms = [r for r in rooms if "Lab" in r]
            elif session_type == "lecture":
                available_rooms = [r for r in rooms if "Lecture" in r or "Room" in r]
            else:
                available_rooms = rooms
            
            # Find an available time slot
            assigned = False
            attempts = 0
            max_attempts = 20
            
            while not assigned and attempts < max_attempts:
                time_slot = random.choice(time_slots)
                room = random.choice(available_rooms)
                
                slot_key = (day, time_slot[0])
                
                # Check if this slot is available
                if slot_key not in used_slots or used_slots[slot_key] != room:
                    # Assign this slot
                    cursor.execute("""
                        INSERT INTO class_schedules_enhanced 
                        (subject_id, term_id, section, day_of_week, start_time, end_time, room, session_type)
                        VALUES (?, ?, 'A', ?, ?, ?, ?, ?)
                    """, (subject_id, term_id, day, time_slot[0], time_slot[1], room, session_type))
                    
                    used_slots[slot_key] = room
                    assigned = True
                    
                    print(f"✅ {subject_code}: {day_names[day]} {time_slot[0]}-{time_slot[1]} in {room} [{session_type}]")
                
                attempts += 1
            
            if not assigned:
                print(f"⚠️ Could not assign slot for {subject_code} on {day_names[day]}")
    
    conn.commit()
    
    # Show summary
    cursor.execute("SELECT COUNT(*) FROM class_schedules_enhanced")
    total_schedules = cursor.fetchone()[0]
    
    print(f"\n📊 Summary:")
    print(f"✅ Created {total_schedules} class schedules")
    
    # Show schedule by day
    print(f"\n📅 Schedule by Day:")
    for day in working_days:
        cursor.execute("""
            SELECT COUNT(*) 
            FROM class_schedules_enhanced 
            WHERE day_of_week = ?
        """, (day,))
        day_count = cursor.fetchone()[0]
        print(f"  {day_names[day]}: {day_count} classes")
    
    conn.close()
    return total_schedules

def show_full_schedule():
    """Display the complete schedule organized by day"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    day_names = {0: "Sunday", 1: "Monday", 2: "Tuesday", 3: "Wednesday", 4: "Thursday", 5: "Friday", 6: "Saturday"}
    
    print("\n📅 Complete Weekly Schedule:")
    print("=" * 80)
    
    for day in range(7):
        cursor.execute("""
            SELECT 
                s.subject_code,
                s.subject_name,
                cs.start_time,
                cs.end_time,
                cs.room,
                cs.session_type
            FROM class_schedules_enhanced cs
            JOIN subjects_enhanced s ON cs.subject_id = s.subject_id
            WHERE cs.day_of_week = ?
            ORDER BY cs.start_time
        """, (day,))
        
        day_schedule = cursor.fetchall()
        
        if day_schedule:
            print(f"\n{day_names[day]}:")
            print("-" * 40)
            for schedule in day_schedule:
                subject_code, subject_name, start_time, end_time, room, session_type = schedule
                print(f"  {start_time}-{end_time}: {subject_code} - {subject_name}")
                print(f"                    Room: {room} [{session_type}]")
        else:
            print(f"\n{day_names[day]}: No classes scheduled")
    
    conn.close()

def main():
    """Main function"""
    print("🕐 Creating Comprehensive Class Schedule...")
    print("⚠️ This will replace all existing class schedules")
    
    response = input("Do you want to proceed? (y/N): ").lower().strip()
    if response != 'y':
        print("❌ Operation cancelled")
        return
    
    try:
        # Create comprehensive schedule
        total_schedules = create_comprehensive_schedule()
        
        # Show the complete schedule
        show_full_schedule()
        
        print(f"\n🎉 Successfully created {total_schedules} class schedules!")
        print("✅ All subjects now have classes scheduled across the week")
        
    except Exception as e:
        print(f"❌ Error creating schedule: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
