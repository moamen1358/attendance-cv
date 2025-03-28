import sqlite3
import sys
import os

# Add the project root to the path so we can import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def fix_attendance_records_schema():
    """
    Fix the attendance_records table if it has inconsistent column naming
    """
    db_path = 'attendance_system.db'
    print(f"Checking attendance_records schema in {os.path.abspath(db_path)}...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check which table exists - attendance_records or attendance_log
        attendance_table = None
        for table_name in ['attendance_records', 'attendance_log']:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            if cursor.fetchone():
                attendance_table = table_name
                print(f"Found attendance table: {attendance_table}")
                break
        
        if not attendance_table:
            print("No attendance records table found. Creating attendance_records table...")
            cursor.execute("""
            CREATE TABLE attendance_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                confidence REAL DEFAULT 1.0,
                device_id TEXT,
                day_of_week TEXT
            )
            """)
            print("Created attendance_records table with standard schema")
            return True
        
        # Check the columns in the table
        cursor.execute(f"PRAGMA table_info({attendance_table})")
        columns = {col[1].lower(): col[1] for col in cursor.fetchall()}
        print(f"Current columns: {columns}")
        
        # Check if name column exists
        has_name_column = 'name' in columns
        has_student_name = 'student_name' in columns
        has_student_username = 'student_username' in columns
        
        # If we don't have a standard column for student name, fix it
        if not has_name_column and not has_student_name:
            if has_student_username:
                # Rename student_username to name or create a view
                print("Found student_username but no name column. Creating a view...")
                cursor.execute(f"""
                CREATE VIEW IF NOT EXISTS {attendance_table}_view AS 
                SELECT student_username AS name, * FROM {attendance_table}
                """)
                print(f"Created view {attendance_table}_view that maps student_username to name")
            else:
                # We need to add a name column
                print("No standard student name column found. Adding name column...")
                cursor.execute(f"ALTER TABLE {attendance_table} ADD COLUMN name TEXT")
                print(f"Added name column to {attendance_table}")
            
            conn.commit()
        
        # Check if we have timestamp column
        has_timestamp = 'timestamp' in columns
        has_date_time = 'date_time' in columns
        
        if not has_timestamp and has_date_time:
            print("Found date_time but no timestamp column. Creating a view...")
            cursor.execute(f"""
            CREATE VIEW IF NOT EXISTS {attendance_table}_time_view AS 
            SELECT date_time AS timestamp, * FROM {attendance_table}
            """)
            print(f"Created view {attendance_table}_time_view that maps date_time to timestamp")
            conn.commit()
            
        print("Attendance records schema check completed")
        return True
        
    except Exception as e:
        print(f"Error fixing attendance records schema: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    fix_attendance_records_schema()
