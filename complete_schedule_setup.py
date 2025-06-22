#!/usr/bin/env python3
"""
Complete Schedule Setup Script
Ensures every department has subjects and schedules for years 1, 2, and 3 for all 7 days of the week.
"""

import sqlite3
import random
from datetime import datetime

def initialize_complete_schedules():
    """Initialize complete schedules for all departments and years."""
    
    conn = sqlite3.connect('attendance_system.db')
    cursor = conn.cursor()
    
    try:
        # Get all departments
        cursor.execute("SELECT department_id, department_name, department_code FROM departments")
        departments = cursor.fetchall()
        
        # Academic years to ensure (1, 2, 3)
        academic_years = [1, 2, 3]
        
        # Days of the week
        days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        # Time slots for classes
        time_slots = [
            ('08:00', '09:30'),
            ('09:45', '11:15'),
            ('11:30', '13:00'),
            ('13:30', '15:00'),
            ('15:15', '16:45'),
            ('17:00', '18:30')
        ]
        
        # Subject templates for each year
        subject_templates = {
            1: [
                "Introduction to {dept}",
                "Programming Fundamentals",
                "Mathematics I",
                "English Communication",
                "Computer Fundamentals",
                "Logic and Critical Thinking",
                "Ethics in Technology"
            ],
            2: [
                "Advanced {dept} Concepts",
                "Data Structures and Algorithms",
                "Mathematics II",
                "Database Systems",
                "Software Engineering Principles",
                "Research Methodology",
                "Project Management"
            ],
            3: [
                "Advanced {dept} Applications",
                "Capstone Project",
                "Professional Ethics",
                "Industry Internship",
                "Advanced Algorithms",
                "System Design",
                "Thesis Preparation"
            ]
        }
        
        # Room templates
        rooms = ['Room A101', 'Room A102', 'Room A103', 'Room B201', 'Room B202', 'Room B203', 
                'Lab C301', 'Lab C302', 'Lab C303', 'Auditorium D401']
        
        # Professor names
        professors = [
            'Dr. Ahmed Hassan', 'Dr. Fatma Ali', 'Dr. Mohamed Omar', 'Dr. Sara Ahmed',
            'Dr. Nour Hassan', 'Dr. Amr Mohamed', 'Dr. Laila Ibrahim', 'Dr. Khaled Mahmoud',
            'Dr. Yasmin Farouk', 'Dr. Tamer Adel', 'Dr. Rania Mostafa', 'Dr. Hany Selim'
        ]
        
        print("Setting up complete schedules for all departments and years...")
        
        for dept_id, dept_name, dept_code in departments:
            print(f"\nProcessing {dept_name} ({dept_code})...")
            
            for year in academic_years:
                print(f"  Year {year}:")
                
                # Ensure subjects exist for this department/year
                subjects_for_year = subject_templates[year]
                
                for idx, subject_template in enumerate(subjects_for_year):
                    subject_name = subject_template.format(dept=dept_name)
                    
                    # Check if subject already exists
                    cursor.execute("""
                        SELECT subject_id, course_code FROM subjects_enhanced 
                        WHERE department_id = ? AND academic_year = ? AND subject_name = ?
                    """, (dept_id, year, subject_name))
                    
                    existing_subject = cursor.fetchone()
                    
                    if not existing_subject:
                        # Generate unique course code
                        base_code = f"{dept_code}{year}{idx+1:02d}"
                        course_code = base_code
                        counter = 1
                        
                        # Ensure course code is unique
                        while True:
                            cursor.execute("SELECT 1 FROM subjects_enhanced WHERE course_code = ?", (course_code,))
                            if not cursor.fetchone():
                                break
                            course_code = f"{base_code}_{counter}"
                            counter += 1
                        
                        # Create new subject
                        cursor.execute("""
                            INSERT INTO subjects_enhanced 
                            (subject_name, course_code, credit_hours, department_id, academic_year, semester, description)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            subject_name,
                            course_code,
                            random.choice([2, 3, 4]),  # Credit hours
                            dept_id,
                            year,
                            1,  # Semester
                            f"Core subject for {dept_name} Year {year}"
                        ))
                        subject_id = cursor.lastrowid
                        print(f"    Created subject: {subject_name} ({course_code})")
                    else:
                        subject_id = existing_subject[0]
                        print(f"    Subject exists: {subject_name} ({existing_subject[1]})")
                
                # Get all subjects for this department/year
                cursor.execute("""
                    SELECT subject_id, subject_name FROM subjects_enhanced 
                    WHERE department_id = ? AND academic_year = ?
                """, (dept_id, year))
                
                year_subjects = cursor.fetchall()
                
                # Ensure schedules exist for all days of the week
                for day in days_of_week:
                    print(f"    {day}:")
                    
                    # Check if any schedule exists for this day/department/year
                    cursor.execute("""
                        SELECT COUNT(*) FROM class_schedules_enhanced cs
                        JOIN subjects_enhanced s ON cs.subject_id = s.subject_id
                        WHERE s.department_id = ? AND s.academic_year = ? AND cs.day_of_week = ?
                    """, (dept_id, year, day))
                    
                    existing_schedules = cursor.fetchone()[0]
                    
                    if existing_schedules == 0:
                        # Create schedules for this day
                        subjects_to_schedule = random.sample(year_subjects, min(3, len(year_subjects)))
                        
                        for i, (subject_id, subject_name) in enumerate(subjects_to_schedule):
                            start_time, end_time = time_slots[i]
                            room = random.choice(rooms)
                            professor = random.choice(professors)
                            
                            cursor.execute("""
                                INSERT INTO class_schedules_enhanced
                                (subject_id, day_of_week, start_time, end_time, room, professor_name)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (subject_id, day, start_time, end_time, room, professor))
                            
                            print(f"      {start_time}-{end_time}: {subject_name} ({room}, {professor})")
                    else:
                        print(f"      Already has {existing_schedules} classes scheduled")
        
        conn.commit()
        print("\n✅ Complete schedule setup completed successfully!")
        
        # Verify the results
        print("\n📊 Verification Report:")
        cursor.execute("""
            SELECT d.department_name, s.academic_year, COUNT(DISTINCT cs.day_of_week) as days_with_classes,
                   COUNT(cs.schedule_id) as total_classes
            FROM departments d
            LEFT JOIN subjects_enhanced s ON d.department_id = s.department_id
            LEFT JOIN class_schedules_enhanced cs ON s.subject_id = cs.subject_id
            GROUP BY d.department_name, s.academic_year
            ORDER BY d.department_name, s.academic_year
        """)
        
        results = cursor.fetchall()
        for dept_name, year, days_count, total_classes in results:
            if year:  # Only show if year is not None
                status = "✅ Complete" if days_count == 7 else f"⚠️  Missing {7-days_count} days"
                print(f"{dept_name} Year {year}: {days_count}/7 days, {total_classes} total classes - {status}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    initialize_complete_schedules()
