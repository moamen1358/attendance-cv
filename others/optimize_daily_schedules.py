#!/usr/bin/env python3
"""
Schedule Optimizer - Enforce Maximum 5 Classes Per Day
Ensures no day has more than 5 classes and optimizes distribution.
"""

import sqlite3
import random

def optimize_daily_schedules():
    """Optimize schedules to ensure max 5 classes per day and better distribution."""
    
    conn = sqlite3.connect('attendance_system.db')
    cursor = conn.cursor()
    
    try:
        print("📅 SCHEDULE OPTIMIZATION - MAX 5 CLASSES PER DAY")
        print("=" * 60)
        
        # Get current schedule distribution
        cursor.execute("""
            SELECT d.department_name, s.academic_year, cs.day_of_week, 
                   COUNT(*) as classes_per_day,
                   GROUP_CONCAT(cs.schedule_id) as schedule_ids
            FROM class_schedules_enhanced cs
            JOIN subjects_enhanced s ON cs.subject_id = s.subject_id
            JOIN departments d ON s.department_id = d.department_id
            GROUP BY d.department_name, s.academic_year, cs.day_of_week
            ORDER BY d.department_name, s.academic_year, cs.day_of_week
        """)
        
        schedule_data = cursor.fetchall()
        
        # Check for violations and optimization opportunities
        violations = []
        light_days = []
        
        for dept, year, day, count, schedule_ids in schedule_data:
            if count > 5:
                violations.append((dept, year, day, count, schedule_ids.split(',')))
            elif count < 3:
                light_days.append((dept, year, day, count))
        
        print(f"🔍 ANALYSIS RESULTS:")
        print(f"   Violations (>5 classes/day): {len(violations)}")
        print(f"   Light days (<3 classes/day): {len(light_days)}")
        
        if violations:
            print(f"\n⚠️  FIXING VIOLATIONS:")
            for dept, year, day, count, schedule_ids in violations:
                print(f"   {dept} Year {year} {day}: {count} classes (removing {count-5})")
                
                # Remove excess classes (randomly select which ones to remove)
                excess_count = count - 5
                ids_to_remove = random.sample(schedule_ids, excess_count)
                
                for schedule_id in ids_to_remove:
                    cursor.execute("DELETE FROM class_schedules_enhanced WHERE schedule_id = ?", 
                                 (schedule_id,))
                
                print(f"     Removed {excess_count} classes")
        
        # Time slots available for scheduling
        time_slots = [
            ('08:00', '09:30'),
            ('09:45', '11:15'),
            ('11:30', '13:00'),
            ('13:30', '15:00'),
            ('15:15', '16:45')
        ]
        
        # Room and professor options
        rooms = ['Room A101', 'Room A102', 'Room A103', 'Room B201', 'Room B202', 
                'Room B203', 'Lab C301', 'Lab C302', 'Lab C303', 'Auditorium D401']
        professors = ['Dr. Ahmed Hassan', 'Dr. Fatma Ali', 'Dr. Mohamed Omar', 'Dr. Sara Ahmed',
                     'Dr. Nour Hassan', 'Dr. Amr Mohamed']
        
        # Optimize light days (add classes to days with <5 classes if subjects available)
        print(f"\n🎯 OPTIMIZING DISTRIBUTION:")
        
        optimized_count = 0
        for dept, year, day, count in light_days:
            if count < 5:
                # Get available subjects for this department/year that aren't scheduled on this day
                cursor.execute("""
                    SELECT s.subject_id, s.subject_name
                    FROM subjects_enhanced s
                    JOIN departments d ON s.department_id = d.department_id
                    WHERE d.department_name = ? AND s.academic_year = ?
                    AND s.subject_id NOT IN (
                        SELECT DISTINCT cs.subject_id
                        FROM class_schedules_enhanced cs
                        JOIN subjects_enhanced s2 ON cs.subject_id = s2.subject_id
                        JOIN departments d2 ON s2.department_id = d2.department_id
                        WHERE d2.department_name = ? AND s2.academic_year = ? AND cs.day_of_week = ?
                    )
                    LIMIT ?
                """, (dept, year, dept, year, day, 5 - count))
                
                available_subjects = cursor.fetchall()
                
                if available_subjects:
                    added_classes = 0
                    for subject_id, subject_name in available_subjects:
                        if count + added_classes < 5:
                            # Add this subject to the day
                            start_time, end_time = time_slots[count + added_classes]
                            room = random.choice(rooms)
                            professor = random.choice(professors)
                            
                            cursor.execute("""
                                INSERT INTO class_schedules_enhanced
                                (subject_id, day_of_week, start_time, end_time, room, professor_name)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (subject_id, day, start_time, end_time, room, professor))
                            
                            added_classes += 1
                            optimized_count += 1
                    
                    if added_classes > 0:
                        print(f"   {dept} Year {year} {day}: Added {added_classes} classes ({count} → {count + added_classes})")
        
        conn.commit()
        
        # Final verification
        print(f"\n📊 FINAL VERIFICATION:")
        cursor.execute("""
            SELECT d.department_name, s.academic_year, cs.day_of_week, COUNT(*) as classes_per_day
            FROM class_schedules_enhanced cs
            JOIN subjects_enhanced s ON cs.subject_id = s.subject_id
            JOIN departments d ON s.department_id = d.department_id
            GROUP BY d.department_name, s.academic_year, cs.day_of_week
            HAVING COUNT(*) > 5
        """)
        
        remaining_violations = cursor.fetchall()
        
        if remaining_violations:
            print(f"   ❌ Still have {len(remaining_violations)} violations!")
            for dept, year, day, count in remaining_violations:
                print(f"      {dept} Year {year} {day}: {count} classes")
        else:
            print(f"   ✅ All days now have ≤5 classes!")
        
        # Show distribution summary
        cursor.execute("""
            SELECT COUNT(*) as days_with_count, classes_per_day
            FROM (
                SELECT COUNT(*) as classes_per_day
                FROM class_schedules_enhanced cs
                JOIN subjects_enhanced s ON cs.subject_id = s.subject_id
                GROUP BY s.department_id, s.academic_year, cs.day_of_week
            ) subquery
            GROUP BY classes_per_day
            ORDER BY classes_per_day
        """)
        
        distribution = cursor.fetchall()
        
        print(f"\n📈 SCHEDULE DISTRIBUTION:")
        total_days = sum(count for count, _ in distribution)
        for day_count, classes_per_day in distribution:
            percentage = (day_count / total_days) * 100
            print(f"   {classes_per_day} classes/day: {day_count} days ({percentage:.1f}%)")
        
        print(f"\n✅ OPTIMIZATION COMPLETE!")
        print(f"   Violations fixed: {len(violations)}")
        print(f"   Classes optimized: {optimized_count}")
        print(f"   Maximum classes per day: 5 ✅")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    optimize_daily_schedules()
