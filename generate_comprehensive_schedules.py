#!/usr/bin/env python3
"""
Comprehensive Schedule Generator
Creates class schedules for all departments and years across all days of the week.
"""

import sqlite3
from datetime import datetime, time

DATABASE_PATH = 'attendance_system.db'

def get_departments_and_years():
    """Get all department and year combinations that need schedules"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Get all department and year combinations from subjects
    cursor.execute("""
        SELECT DISTINCT s.department_id, s.academic_year, d.department_name, d.department_code
        FROM subjects_enhanced s
        JOIN departments d ON s.department_id = d.department_id
        ORDER BY s.department_id, s.academic_year
    """)
    
    combinations = cursor.fetchall()
    conn.close()
    return combinations

def get_subjects_by_dept_year(dept_id, year):
    """Get all subjects for a specific department and year"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT subject_id, subject_name, course_code
        FROM subjects_enhanced 
        WHERE department_id = ? AND academic_year = ?
        ORDER BY subject_name
    """, (dept_id, year))
    
    subjects = cursor.fetchall()
    conn.close()
    return subjects

def clear_existing_schedules():
    """Clear existing schedules to rebuild them"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    print("Clearing existing schedules...")
    cursor.execute("DELETE FROM class_schedules_enhanced")
    conn.commit()
    conn.close()
    print("✅ Existing schedules cleared")

def generate_schedule_for_dept_year(dept_id, year, dept_name, dept_code):
    """Generate a complete weekly schedule for a specific department and year"""
    subjects = get_subjects_by_dept_year(dept_id, year)
    
    if not subjects:
        print(f"⚠️  No subjects found for {dept_name} Year {year}")
        return
    
    print(f"📚 Generating schedule for {dept_name} (Year {year}) - {len(subjects)} subjects")
    
    # Define time slots for each day
    time_slots = {
        'Sunday': [
            ('08:00', '09:30'),
            ('10:00', '11:30'), 
            ('12:00', '13:30'),
            ('14:00', '15:30')
        ],
        'Monday': [
            ('08:00', '09:30'),
            ('10:00', '11:30'),
            ('12:00', '13:30'), 
            ('14:00', '15:30'),
            ('16:00', '17:30')
        ],
        'Tuesday': [
            ('08:00', '09:30'),
            ('10:00', '11:30'),
            ('12:00', '13:30'),
            ('14:00', '15:30'),
            ('16:00', '17:30')
        ],
        'Wednesday': [
            ('08:00', '09:30'),
            ('10:00', '11:30'),
            ('12:00', '13:30'),
            ('14:00', '15:30')
        ],
        'Thursday': [
            ('08:00', '09:30'),
            ('10:00', '11:30'),
            ('12:00', '13:30'),
            ('14:00', '15:30'),
            ('16:00', '17:30')
        ],
        'Friday': [
            ('08:00', '09:30'),
            ('10:00', '11:30'),
            ('12:00', '13:30'),
            ('14:00', '15:30')
        ],
        'Saturday': [
            ('09:00', '10:30'),
            ('11:00', '12:30'),
            ('14:00', '15:30')
        ]
    }
    
    # Room assignments based on department
    room_prefixes = {
        1: 'A',  # CS
        2: 'B',  # AI  
        3: 'C',  # IS
        4: 'D',  # IT
        5: 'E',  # SE
        6: 'F'   # CY
    }
    
    room_prefix = room_prefixes.get(dept_id, 'G')
    
    # Generate schedules
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    subject_index = 0
    schedules_created = 0
    
    for day, slots in time_slots.items():
        for slot_index, (start_time, end_time) in enumerate(slots):
            if subject_index < len(subjects):
                subject_id, subject_name, course_code = subjects[subject_index]
                
                # Assign room (100s for Year 1, 200s for Year 2, etc.)
                room_number = f"{room_prefix}{year}{slot_index + 1:02d}"
                
                # Create professor name
                prof_name = f"Prof. {course_code}"
                
                # Insert schedule
                cursor.execute("""
                    INSERT INTO class_schedules_enhanced 
                    (subject_id, day_of_week, start_time, end_time, room, professor_name, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (subject_id, day, start_time, end_time, room_number, prof_name, datetime.now()))
                
                schedules_created += 1
                subject_index += 1
                
                # If we've scheduled all subjects, start over for multiple sessions per week
                if subject_index >= len(subjects):
                    subject_index = 0
    
    conn.commit()
    conn.close()
    
    print(f"✅ Created {schedules_created} class schedules for {dept_name} Year {year}")
    return schedules_created

def generate_all_schedules():
    """Generate schedules for all department and year combinations"""
    print("🏫 Starting Comprehensive Schedule Generation")
    print("=" * 50)
    
    # Clear existing schedules
    clear_existing_schedules()
    
    # Get all department and year combinations
    combinations = get_departments_and_years()
    print(f"📋 Found {len(combinations)} department/year combinations to schedule")
    print()
    
    total_schedules = 0
    
    for dept_id, year, dept_name, dept_code in combinations:
        schedules_count = generate_schedule_for_dept_year(dept_id, year, dept_name, dept_code)
        total_schedules += schedules_count
        print()
    
    print("=" * 50)
    print(f"🎉 Schedule Generation Complete!")
    print(f"📊 Total schedules created: {total_schedules}")
    
    # Verify the results
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Get schedule summary by day
    cursor.execute("""
        SELECT 
            day_of_week,
            COUNT(*) as class_count,
            COUNT(DISTINCT subject_id) as unique_subjects,
            COUNT(DISTINCT room) as rooms_used
        FROM class_schedules_enhanced
        GROUP BY day_of_week
        ORDER BY 
            CASE day_of_week 
                WHEN 'Sunday' THEN 1
                WHEN 'Monday' THEN 2
                WHEN 'Tuesday' THEN 3
                WHEN 'Wednesday' THEN 4
                WHEN 'Thursday' THEN 5
                WHEN 'Friday' THEN 6
                WHEN 'Saturday' THEN 7
            END
    """)
    
    day_summary = cursor.fetchall()
    
    print("\n📅 Schedule Summary by Day:")
    print("-" * 40)
    for day, classes, subjects, rooms in day_summary:
        print(f"{day:>9}: {classes:>3} classes, {subjects:>2} subjects, {rooms:>2} rooms")
    
    # Get schedule summary by department
    cursor.execute("""
        SELECT 
            d.department_name,
            s.academic_year,
            COUNT(*) as class_count
        FROM class_schedules_enhanced cs
        JOIN subjects_enhanced s ON cs.subject_id = s.subject_id
        JOIN departments d ON s.department_id = d.department_id
        GROUP BY d.department_name, s.academic_year
        ORDER BY d.department_name, s.academic_year
    """)
    
    dept_summary = cursor.fetchall()
    
    print("\n🏛️  Schedule Summary by Department & Year:")
    print("-" * 45)
    for dept, year, classes in dept_summary:
        print(f"{dept:>20} Year {year}: {classes:>3} classes")
    
    conn.close()
    
    return total_schedules

if __name__ == "__main__":
    # Run the comprehensive schedule generation
    total = generate_all_schedules()
    
    print(f"\n✅ SUCCESS: Generated {total} class schedules for all departments and years!")
    print("All students now have comprehensive weekly schedules.")
