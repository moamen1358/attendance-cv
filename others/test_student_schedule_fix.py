#!/usr/bin/env python3
"""
Student Schedule Fix Verification
Tests that students only see their own classes, not all classes in the system.
"""

import sqlite3
import sys
import os

# Add the src directory to the path so we can import the module
sys.path.append('src')

def test_student_schedule_filtering():
    """Test that student schedule filtering works correctly."""
    
    print("🔍 STUDENT SCHEDULE FILTERING TEST")
    print("=" * 50)
    
    # Test database queries directly first
    conn = sqlite3.connect('attendance_system.db')
    cursor = conn.cursor()
    
    # Get test student info
    cursor.execute("SELECT name, department, year FROM students_enhanced WHERE name = 'Test Student'")
    student_info = cursor.fetchone()
    
    if not student_info:
        print("❌ Test Student not found in database")
        return False
    
    student_name, department, year = student_info
    print(f"📚 Test Student: {student_name}")
    print(f"   Department: {department}")
    print(f"   Year: {year}")
    
    # Test Sunday classes - before fix (all classes)
    cursor.execute("SELECT COUNT(*) FROM class_schedules_enhanced WHERE day_of_week = 'Sunday'")
    total_sunday_classes = cursor.fetchone()[0]
    print(f"\n📊 Total Sunday classes in system: {total_sunday_classes}")
    
    # Test Sunday classes - after fix (student's classes only)
    cursor.execute("""
        SELECT COUNT(*) 
        FROM class_schedules_enhanced cs
        JOIN subjects_enhanced s ON cs.subject_id = s.subject_id
        JOIN departments d ON s.department_id = d.department_id
        WHERE cs.day_of_week = 'Sunday' 
        AND d.department_name = ? 
        AND s.academic_year = ?
    """, (department, year))
    student_sunday_classes = cursor.fetchone()[0]
    print(f"📚 Student's Sunday classes: {student_sunday_classes}")
    
    # Test with the updated function
    try:
        # Import from the src directory
        sys.path.insert(0, os.path.join(os.getcwd(), 'src'))
        from student_report import get_schedule_for_day
        
        # Test old behavior (no student filter)
        all_schedule = get_schedule_for_day('Sunday')
        print(f"\n🔧 Function test - All classes: {len(all_schedule)} classes")
        
        # Test new behavior (with student filter)
        student_schedule = get_schedule_for_day('Sunday', 'Test Student')
        print(f"🎯 Function test - Student classes: {len(student_schedule)} classes")
        
        if len(student_schedule) == student_sunday_classes:
            print("✅ Schedule filtering working correctly!")
            
            # Show student's actual schedule
            print(f"\n📅 {student_name}'s Sunday Schedule:")
            for _, row in student_schedule.iterrows():
                print(f"   {row['start_time']}-{row['end_time']}: {row['subject']} ({row['room']})")
            
            success = True
        else:
            print(f"❌ Mismatch: Function returned {len(student_schedule)}, expected {student_sunday_classes}")
            success = False
            
    except Exception as e:
        print(f"❌ Error testing function: {e}")
        success = False
    
    # Test other days as well
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    print(f"\n📈 Weekly Schedule Summary for {student_name}:")
    
    total_student_classes = 0
    for day in days + ['Sunday']:
        cursor.execute("""
            SELECT COUNT(*) 
            FROM class_schedules_enhanced cs
            JOIN subjects_enhanced s ON cs.subject_id = s.subject_id
            JOIN departments d ON s.department_id = d.department_id
            WHERE cs.day_of_week = ? 
            AND d.department_name = ? 
            AND s.academic_year = ?
        """, (day, department, year))
        day_classes = cursor.fetchone()[0]
        total_student_classes += day_classes
        print(f"   {day}: {day_classes} classes")
    
    print(f"\n📊 SUMMARY:")
    print(f"   Total classes in system: {total_sunday_classes * 7} (estimated)")
    print(f"   Student's total weekly classes: {total_student_classes}")
    print(f"   Reduction: {((total_sunday_classes * 7 - total_student_classes) / (total_sunday_classes * 7)) * 100:.1f}%")
    
    if total_student_classes <= 35:  # Max 5 classes per day * 7 days
        print("✅ Student class count is within reasonable limits (≤35 per week)")
    else:
        print("⚠️  Student has more than 35 classes per week")
    
    conn.close()
    return success

if __name__ == "__main__":
    test_student_schedule_filtering()
