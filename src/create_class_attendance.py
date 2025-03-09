
import sqlite3
from datetime import datetime

def create_class_attendance_table():
    """Create a table that links attendance records to specific classes"""
    conn = sqlite3.connect('attendance_system.db')
    cursor = conn.cursor()
    
    # Create the table if it doesn't exist
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
    
    # Function to populate class_attendance table based on schedule and attendance logs
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
    
    -- Now insert records for each scheduled class, marking as attended if there's a matching log
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
    
    conn.commit()
    conn.close()
    print("Created and populated class_attendance table")

if __name__ == "__main__":
    create_class_attendance_table()
