#!/usr/bin/env python3
"""
Schedule Constraint Enforcer
Ensures the 5-classes-per-day rule is maintained when adding new schedules.
"""

import sqlite3

def create_schedule_constraints():
    """Create database constraints and helper functions to enforce schedule limits."""
    
    conn = sqlite3.connect('attendance_system.db')
    cursor = conn.cursor()
    
    try:
        print("🔒 CREATING SCHEDULE CONSTRAINTS")
        print("=" * 50)
        
        # Create a trigger to prevent inserting more than 5 classes per day
        print("Creating trigger to enforce max 5 classes per day...")
        
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS enforce_max_classes_per_day
            BEFORE INSERT ON class_schedules_enhanced
            BEGIN
                SELECT CASE
                    WHEN (
                        SELECT COUNT(*)
                        FROM class_schedules_enhanced cs
                        JOIN subjects_enhanced s ON cs.subject_id = s.subject_id
                        JOIN subjects_enhanced new_s ON NEW.subject_id = new_s.subject_id
                        WHERE s.department_id = new_s.department_id
                        AND s.academic_year = new_s.academic_year
                        AND cs.day_of_week = NEW.day_of_week
                    ) >= 5
                    THEN RAISE(ABORT, 'Cannot add more than 5 classes per day for same department/year')
                END;
            END;
        """)
        
        print("✅ Trigger created successfully!")
        
        # Create a helper function to check schedule capacity
        print("Creating helper view for schedule monitoring...")
        
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS daily_schedule_capacity AS
            SELECT 
                d.department_name,
                d.department_id,
                s.academic_year,
                cs.day_of_week,
                COUNT(*) as current_classes,
                (5 - COUNT(*)) as remaining_capacity
            FROM class_schedules_enhanced cs
            JOIN subjects_enhanced s ON cs.subject_id = s.subject_id
            JOIN departments d ON s.department_id = d.department_id
            GROUP BY d.department_id, s.academic_year, cs.day_of_week
            ORDER BY d.department_name, s.academic_year, cs.day_of_week;
        """)
        
        print("✅ Monitoring view created successfully!")
        
        # Test the constraint
        print("\n🧪 TESTING CONSTRAINT:")
        
        # Try to get a sample department/year/day that already has 5 classes
        cursor.execute("""
            SELECT d.department_id, s.academic_year, cs.day_of_week, s.subject_id
            FROM class_schedules_enhanced cs
            JOIN subjects_enhanced s ON cs.subject_id = s.subject_id
            JOIN departments d ON s.department_id = d.department_id
            GROUP BY d.department_id, s.academic_year, cs.day_of_week
            HAVING COUNT(*) = 5
            LIMIT 1
        """)
        
        test_data = cursor.fetchone()
        
        if test_data:
            dept_id, year, day, sample_subject_id = test_data
            
            print(f"Testing constraint with department_id={dept_id}, year={year}, day={day}")
            
            try:
                # Try to insert a 6th class (should fail)
                cursor.execute("""
                    INSERT INTO class_schedules_enhanced
                    (subject_id, day_of_week, start_time, end_time, room, professor_name)
                    VALUES (?, ?, '18:00', '19:30', 'Test Room', 'Test Professor')
                """, (sample_subject_id, day))
                
                print("❌ Constraint failed - insertion should have been blocked!")
                cursor.execute("DELETE FROM class_schedules_enhanced WHERE start_time = '18:00' AND end_time = '19:30'")
                
            except sqlite3.IntegrityError as e:
                if "Cannot add more than 5 classes per day" in str(e):
                    print("✅ Constraint working correctly - 6th class blocked!")
                else:
                    print(f"⚠️  Unexpected constraint error: {e}")
            except Exception as e:
                print(f"⚠️  Test error: {e}")
        
        conn.commit()
        
        # Show current capacity status
        print(f"\n📊 CURRENT SCHEDULE CAPACITY:")
        cursor.execute("""
            SELECT department_name, academic_year, day_of_week, 
                   current_classes, remaining_capacity
            FROM daily_schedule_capacity
            ORDER BY department_name, academic_year, 
            CASE day_of_week 
                WHEN 'Monday' THEN 1 WHEN 'Tuesday' THEN 2 WHEN 'Wednesday' THEN 3 
                WHEN 'Thursday' THEN 4 WHEN 'Friday' THEN 5 WHEN 'Saturday' THEN 6 
                WHEN 'Sunday' THEN 7 
            END
            LIMIT 21
        """)
        
        capacity_data = cursor.fetchall()
        current_dept = None
        
        for dept, year, day, current, remaining in capacity_data:
            if dept != current_dept:
                print(f"\n{dept}:")
                current_dept = dept
            
            status = "🟢 Available" if remaining > 0 else "🔴 Full"
            print(f"  Year {year} {day}: {current}/5 classes - {status}")
        
        print(f"\n✅ CONSTRAINT SYSTEM READY!")
        print("   • Maximum 5 classes per day enforced")
        print("   • Database trigger prevents violations")
        print("   • Monitoring view available for capacity checks")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

def add_schedule_safely(subject_id, day_of_week, start_time, end_time, room, professor_name):
    """Safely add a schedule entry with constraint checking."""
    
    conn = sqlite3.connect('attendance_system.db')
    cursor = conn.cursor()
    
    try:
        # Check capacity first
        cursor.execute("""
            SELECT d.department_name, s.academic_year, 
                   COUNT(*) as current_classes
            FROM class_schedules_enhanced cs
            JOIN subjects_enhanced s ON cs.subject_id = s.subject_id
            JOIN departments d ON s.department_id = d.department_id
            JOIN subjects_enhanced new_s ON new_s.subject_id = ?
            WHERE s.department_id = new_s.department_id
            AND s.academic_year = new_s.academic_year
            AND cs.day_of_week = ?
        """, (subject_id, day_of_week))
        
        result = cursor.fetchone()
        if result and result[2] >= 5:
            return False, f"Cannot add: {result[0]} Year {result[1]} {day_of_week} already has 5 classes"
        
        # Safe to insert
        cursor.execute("""
            INSERT INTO class_schedules_enhanced
            (subject_id, day_of_week, start_time, end_time, room, professor_name)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (subject_id, day_of_week, start_time, end_time, room, professor_name))
        
        conn.commit()
        return True, "Schedule added successfully"
        
    except Exception as e:
        conn.rollback()
        return False, f"Error: {e}"
    finally:
        conn.close()

if __name__ == "__main__":
    create_schedule_constraints()
