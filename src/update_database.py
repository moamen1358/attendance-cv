
import sqlite3
from datetime import datetime
import os

def update_database_schema():
    """
    Comprehensive database schema update to support improved attendance tracking
    
    This script performs the following updates:
    1. Adds day_of_week column to attendance_log for easier queries
    2. Creates class_attendance linking table between students and classes
    3. Populates the class_attendance table with historical data
    """
    print("Starting database schema update...")
    
    # Database path
    database_path = 'attendance_system.db'
    if not os.path.exists(database_path):
        print(f"Error: Database file '{database_path}' not found.")
        return False
    
    # Connect to the database
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    
    try:
        # 1. Add day_of_week column to attendance_log if it doesn't exist
        cursor.execute("PRAGMA table_info(attendance_log)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'day_of_week' not in columns:
            print("Adding day_of_week column to attendance_log...")
            cursor.execute("ALTER TABLE attendance_log ADD COLUMN day_of_week TEXT")
            cursor.execute("UPDATE attendance_log SET day_of_week = strftime('%A', timestamp)")
            print("✅ day_of_week column added and populated")
        else:
            print("✓ day_of_week column already exists in attendance_log")
        
        # 2. Add confidence column to attendance_log if it doesn't exist
        if 'confidence' not in columns:
            cursor.execute("ALTER TABLE attendance_log ADD COLUMN confidence REAL")
            print("✅ confidence column added to attendance_log")
        else:
            print("✓ confidence column already exists in attendance_log")
        
        # 3. Add device_id column to attendance_log if it doesn't exist
        if 'device_id' not in columns:
            cursor.execute("ALTER TABLE attendance_log ADD COLUMN device_id TEXT")
            print("✅ device_id column added to attendance_log")
        else:
            print("✓ device_id column already exists in attendance_log")
        
        # 4. Create class_attendance table
        print("Creating class_attendance table...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS class_attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT NOT NULL,
            class_date DATE NOT NULL,
            subject TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            attended BOOLEAN NOT NULL DEFAULT 0,
            UNIQUE(student_name, class_date, subject, start_time)
        )
        """)
        print("✅ class_attendance table created or already exists")
        
        # 5. Populate class_attendance from existing data
        print("Populating class_attendance table with historical data...")
        try:
            cursor.execute("""
            -- First get all scheduled classes for each day
            WITH scheduled_classes AS (
                SELECT 
                    s.subject,
                    s.start_time,
                    s.end_time,
                    s.day,
                    date(a.timestamp) as class_date,
                    a.name as student_name
                FROM 
                    control_4 s,
                    (SELECT DISTINCT name, date(timestamp) as timestamp FROM attendance_log) a
                WHERE 
                    strftime('%A', a.timestamp) = s.day
            )
            
            -- Insert records for scheduled classes, marking as attended if matching logs exist
            INSERT OR IGNORE INTO class_attendance 
                (student_name, class_date, subject, start_time, end_time, attended)
            SELECT 
                c.student_name,
                c.class_date,
                c.subject,
                c.start_time,
                c.end_time,
                EXISTS (
                    SELECT 1 FROM attendance_log a 
                    WHERE a.name = c.student_name 
                    AND date(a.timestamp) = c.class_date
                    AND time(a.timestamp) BETWEEN time(c.start_time) AND time(c.end_time)
                ) as attended
            FROM scheduled_classes c
            """)
            print("✅ class_attendance table populated with historical data")
        except Exception as e:
            print(f"⚠️ Error populating class_attendance: {e}")
            print("This may be normal if the control_4 table doesn't exist yet")
        
        # Commit all changes
        conn.commit()
        print("✅ All database updates completed successfully!")
        return True
    
    except Exception as e:
        print(f"❌ Error updating database schema: {e}")
        return False
    
    finally:
        conn.close()

if __name__ == "__main__":
    update_database_schema()
