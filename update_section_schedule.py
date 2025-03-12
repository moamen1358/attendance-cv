import sqlite3
import os
import pandas as pd
from tabulate import tabulate
from datetime import datetime, timedelta

# Constants
DATABASE_PATH = 'attendance_system.db'

# Updated schedule data with lectures for both sections
UPDATED_SCHEDULE_DATA = [
    # Advanced Mathematics
    ('Advanced Mathematics', 'Monday', '9:00 AM', '11:00 AM', 'lec', 'SEC 1', 'Dr. Alexander Smith', 'Hall A'),
    ('Advanced Mathematics', 'Tuesday', '9:00 AM', '11:00 AM', 'lec', 'SEC 2', 'Dr. Alexander Smith', 'Hall A'),
    ('Advanced Mathematics', 'Wednesday', '2:00 PM', '3:30 PM', 'sec', 'SEC 1', 'Prof. Linda Johnson', 'Room 201'),
    ('Advanced Mathematics', 'Friday', '2:00 PM', '3:30 PM', 'sec', 'SEC 2', 'Prof. Linda Johnson', 'Room 201'),
    
    # Computer Science
    ('Computer Science', 'Monday', '1:00 PM', '3:00 PM', 'lec', 'SEC 1', 'Dr. Rebecca Williams', 'Hall B'),
    ('Computer Science', 'Wednesday', '1:00 PM', '3:00 PM', 'lec', 'SEC 2', 'Dr. Rebecca Williams', 'Hall B'),
    ('Computer Science', 'Tuesday', '10:00 AM', '12:00 PM', 'lab', 'SEC 1', 'Dr. Rebecca Williams', 'Lab 101'),
    ('Computer Science', 'Thursday', '10:00 AM', '12:00 PM', 'lab', 'SEC 2', 'Dr. Rebecca Williams', 'Lab 101'),
    
    # Physics
    ('Physics', 'Tuesday', '2:00 PM', '4:00 PM', 'lec', 'SEC 1', 'Dr. Thomas Brown', 'Hall C'),
    ('Physics', 'Thursday', '2:00 PM', '4:00 PM', 'lec', 'SEC 2', 'Dr. Thomas Brown', 'Hall C'),
    ('Physics', 'Wednesday', '10:00 AM', '12:00 PM', 'sec', 'SEC 1', 'Prof. Sarah Davis', 'Lab 202'),
    ('Physics', 'Friday', '10:00 AM', '12:00 PM', 'sec', 'SEC 2', 'Prof. Sarah Davis', 'Lab 202'),
    
    # Engineering
    ('Engineering', 'Monday', '10:00 AM', '12:00 PM', 'lec', 'SEC 1', 'Dr. Emily Martin', 'Hall D'),
    ('Engineering', 'Wednesday', '10:00 AM', '12:00 PM', 'lec', 'SEC 2', 'Dr. Emily Martin', 'Hall D'),
    ('Engineering', 'Tuesday', '1:00 PM', '3:00 PM', 'lab', 'SEC 1', 'Dr. Emily Martin', 'Workshop'),
    ('Engineering', 'Thursday', '1:00 PM', '3:00 PM', 'lab', 'SEC 2', 'Dr. Emily Martin', 'Workshop'),
    
    # Statistics
    ('Statistics', 'Thursday', '9:00 AM', '11:00 AM', 'lec', 'SEC 1', 'Prof. Michael Taylor', 'Hall E'),
    ('Statistics', 'Friday', '9:00 AM', '11:00 AM', 'lec', 'SEC 2', 'Prof. Michael Taylor', 'Hall E'),
    ('Statistics', 'Monday', '3:00 PM', '5:00 PM', 'sec', 'SEC 1', 'Prof. Michael Taylor', 'Room 303'),
    ('Statistics', 'Wednesday', '3:00 PM', '5:00 PM', 'sec', 'SEC 2', 'Prof. Michael Taylor', 'Room 303'),
]

def get_db_connection():
    """Create a connection to the database"""
    return sqlite3.connect(DATABASE_PATH)

def update_class_schedule():
    """Update class schedule to include lectures for both sections"""
    print("\n🔄 Updating class schedule...")
    
    if not os.path.exists(DATABASE_PATH):
        print(f"❌ Error: Database file '{DATABASE_PATH}' not found.")
        return False
    
    # Backup database first
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"attendance_system_backup_{timestamp}.db"
        
        with sqlite3.connect(DATABASE_PATH) as src_conn:
            with sqlite3.connect(backup_file) as backup_conn:
                src_conn.backup(backup_conn)
        
        print(f"✅ Created database backup: {backup_file}")
    except Exception as e:
        print(f"❌ Failed to create backup: {e}")
        retry = input("Continue without backup? (yes/no): ")
        if retry.lower() != 'yes':
            print("Operation cancelled.")
            return False
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # First check if we have the class_schedules table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='class_schedules'")
        if not cursor.fetchone():
            print("❌ Table 'class_schedules' not found!")
            return False
        
        # Start transaction
        cursor.execute("BEGIN TRANSACTION")
        
        # Clear existing schedule data
        cursor.execute("DELETE FROM class_schedules")
        print("🗑️ Cleared existing class schedule data")
        
        # Insert new schedule data with lectures for both sections
        sql = """
        INSERT INTO class_schedules (subject, day, start_time, end_time, type, section, teacher, room)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        cursor.executemany(sql, UPDATED_SCHEDULE_DATA)
        
        # Verify successful insertion
        cursor.execute("SELECT COUNT(*) FROM class_schedules")
        count = cursor.fetchone()[0]
        
        if count == len(UPDATED_SCHEDULE_DATA):
            print(f"✅ Successfully inserted {count} class records")
        else:
            print(f"⚠️ Only {count} of {len(UPDATED_SCHEDULE_DATA)} records were inserted")
        
        # Commit changes
        cursor.execute("COMMIT")
        print("✅ Class schedule updated successfully!")
        
        # Show updated data
        print("\n=== Updated Class Schedule ===")
        
        # Group by subject and section
        cursor.execute("""
        SELECT subject, section, type, COUNT(*) as count
        FROM class_schedules
        GROUP BY subject, section, type
        ORDER BY subject, section, type
        """)
        
        summary = cursor.fetchall()
        summary_df = pd.DataFrame(summary, columns=['Subject', 'Section', 'Type', 'Count'])
        print(tabulate(summary_df, headers='keys', tablefmt='pretty', showindex=False))
        
        # Show detailed schedule
        print("\n=== Detailed Schedule ===")
        cursor.execute("""
        SELECT subject, day, start_time, end_time, type, section, teacher
        FROM class_schedules
        ORDER BY subject, section, day
        """)
        
        rows = cursor.fetchall()
        schedule_df = pd.DataFrame(rows, columns=['Subject', 'Day', 'Start Time', 'End Time', 'Type', 'Section', 'Teacher'])
        print(tabulate(schedule_df, headers='keys', tablefmt='pretty', showindex=False))
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating class schedule: {e}")
        cursor.execute("ROLLBACK")
        return False
        
    finally:
        conn.close()

def verify_schedule():
    """Verify that each section has its own lectures and other sessions"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if both sections have lectures for each subject
        cursor.execute("""
        SELECT subject, 
               SUM(CASE WHEN section = 'SEC 1' AND type = 'lec' THEN 1 ELSE 0 END) as sec1_lec,
               SUM(CASE WHEN section = 'SEC 2' AND type = 'lec' THEN 1 ELSE 0 END) as sec2_lec
        FROM class_schedules
        GROUP BY subject
        """)
        
        lecture_counts = cursor.fetchall()
        lecture_df = pd.DataFrame(lecture_counts, columns=['Subject', 'SEC 1 Lectures', 'SEC 2 Lectures'])
        
        print("\n=== Lecture Distribution by Section ===")
        print(tabulate(lecture_df, headers='keys', tablefmt='pretty', showindex=False))
        
        # Verify all subjects have lectures for both sections
        all_valid = True
        for subject, sec1_lec, sec2_lec in lecture_counts:
            if sec1_lec < 1:
                print(f"⚠️ {subject} is missing lectures for SEC 1")
                all_valid = False
            if sec2_lec < 1:
                print(f"⚠️ {subject} is missing lectures for SEC 2")
                all_valid = False
        
        if all_valid:
            print("✅ All subjects have lectures for both sections")
        
        # Check for schedule conflicts
        cursor.execute("""
        SELECT a.day, a.section, a.start_time, a.end_time, a.subject, b.subject
        FROM class_schedules a
        JOIN class_schedules b ON 
            a.day = b.day AND 
            a.section = b.section AND
            a.subject <> b.subject AND
            (
                (a.start_time <= b.start_time AND a.end_time > b.start_time) OR
                (a.start_time < b.end_time AND a.end_time >= b.end_time) OR
                (a.start_time >= b.start_time AND a.end_time <= b.end_time)
            )
        GROUP BY a.day, a.section, a.start_time, a.subject, b.subject
        """)
        
        conflicts = cursor.fetchall()
        if conflicts:
            print("\n⚠️ Schedule conflicts detected:")
            for day, section, start, end, subject1, subject2 in conflicts:
                print(f"  - {day} {start}-{end} {section}: {subject1} conflicts with {subject2}")
        else:
            print("✅ No schedule conflicts detected")
        
        return all_valid and not conflicts
    
    except Exception as e:
        print(f"❌ Error verifying schedule: {e}")
        return False
        
    finally:
        conn.close()

def main():
    """Main function"""
    print("🔧 Class Schedule Section Update Tool")
    print("This will update the class schedule to have lectures for both SEC 1 and SEC 2 sections")
    
    # Ask for confirmation
    confirm = input("\n⚠️ WARNING: This will replace all existing class schedule data. Continue? (yes/no): ")
    
    if confirm.lower() != 'yes':
        print("Operation cancelled.")
        return
    
    # Update the schedule
    success = update_class_schedule()
    
    if success:
        print("\n🔍 Verifying updated schedule...")
        verify_schedule()
        
    print("\nDone! Class schedule has been updated with lectures for both sections.")

if __name__ == "__main__":
    main()
