import sqlite3
import os
import sys

# Add the project root to the path so we can import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def fix_attendance_schema():
    """
    Fix the attendance records schema to ensure standardized column names
    and create necessary views for compatibility.
    """
    db_path = 'attendance_system.db'
    print(f"Fixing attendance records schema in {os.path.abspath(db_path)}...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Step 1: Identify all attendance-related tables
        attendance_tables = []
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        for table in cursor.fetchall():
            table_name = table[0]
            if 'attendance' in table_name.lower():
                attendance_tables.append(table_name)
        
        if not attendance_tables:
            print("No attendance tables found. Creating standard attendance_records table...")
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
            attendance_tables = ['attendance_records']
        
        print(f"Found attendance tables: {attendance_tables}")
        
        # Step 2: Check all tables and fix schemas
        for table in attendance_tables:
            # Get columns in this table
            cursor.execute(f"PRAGMA table_info({table})")
            columns = {col[1].lower(): col[1] for col in cursor.fetchall()}
            print(f"Columns in {table}: {list(columns.keys())}")
            
            # Check for required standard columns
            has_name = 'name' in columns
            has_student_name = 'student_name' in columns
            has_timestamp = 'timestamp' in columns
            
            # Fix name column issue
            if not has_name and not has_student_name:
                print(f"No name or student_name column in {table}. Creating compatibility view...")
                # Find a suitable column for name
                name_candidates = ['student', 'student_username', 'username', 'user']
                name_col = None
                for candidate in name_candidates:
                    if candidate in columns:
                        name_col = candidate
                        break
                
                if name_col:
                    # Create a view with standard columns
                    view_name = f"{table}_std_view"
                    cursor.execute(f"DROP VIEW IF EXISTS {view_name}")
                    cursor.execute(f"""
                    CREATE VIEW {view_name} AS
                    SELECT 
                        id,
                        {name_col} AS name,
                        {name_col} AS student_name,
                        {list(columns.keys())[2] if len(columns) > 2 else 'NULL'} AS timestamp,
                        * 
                    FROM {table}
                    """)
                    print(f"Created view {view_name} with standard column names")
                else:
                    # If no suitable column found, add one to the table if possible
                    try:
                        cursor.execute(f"ALTER TABLE {table} ADD COLUMN name TEXT")
                        cursor.execute(f"UPDATE {table} SET name = 'Unknown'")
                        print(f"Added name column to {table}")
                    except:
                        print(f"Could not add name column to {table}")
            
            # Ensure the primary attendance table is attendance_records
            if table != 'attendance_records' and 'attendance_records' not in attendance_tables:
                # Create attendance_records as a view to this table
                cursor.execute("DROP VIEW IF EXISTS attendance_records")
                cursor.execute(f"""
                CREATE VIEW attendance_records AS 
                SELECT * FROM {table}
                """)
                print(f"Created attendance_records view pointing to {table}")
        
        # Step 3: Create a unified view that can be used by all code
        cursor.execute("DROP VIEW IF EXISTS unified_attendance")
        cursor.execute(f"""
        CREATE VIEW unified_attendance AS
        SELECT 
            id,
            COALESCE(name, student_name, 'Unknown') AS name,
            COALESCE(name, student_name, 'Unknown') AS student_name,
            COALESCE(timestamp, datetime, date_time, created_at, CURRENT_TIMESTAMP) AS timestamp,
            COALESCE(confidence, 1.0) AS confidence,
            COALESCE(device_id, 'unknown') AS device_id,
            COALESCE(day_of_week, strftime('%w', timestamp)) AS day_of_week
        FROM {attendance_tables[0]}
        """)
        print("Created unified_attendance view with standardized column names")
        
        conn.commit()
        print("Attendance schema fixes applied successfully")
        return True
    
    except Exception as e:
        print(f"Error fixing attendance schema: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    fix_attendance_schema()
    print("Run this script before starting the application to fix attendance schema issues.")
    print("Command: python scripts/fix_attendance_schema.py")
