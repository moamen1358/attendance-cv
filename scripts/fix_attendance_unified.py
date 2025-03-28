import sqlite3
import os
import sys
import streamlit as st  # For displaying progress if run in a Streamlit app

# Add the project root to the path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Database path
DB_PATH = os.path.join(project_root, 'attendance_system.db')

def fix_attendance_table_schema():
    """Comprehensive fix for attendance records table schema issues"""
    print(f"Analyzing database: {os.path.abspath(DB_PATH)}")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Step 1: Detect existing attendance tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        all_tables = [row[0] for row in cursor.fetchall()]
        attendance_tables = [t for t in all_tables if 'attend' in t.lower()]
        
        print(f"Found {len(attendance_tables)} attendance-related tables: {attendance_tables}")
        
        # If no attendance tables found, create a standard one
        if not attendance_tables:
            cursor.execute("""
            CREATE TABLE attendance_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,                -- Student name (standard column)
                student_name TEXT,                 -- Alternative name column
                timestamp TIMESTAMP NOT NULL,      -- When attendance was recorded
                class_date DATE,                   -- Date of the class
                subject TEXT,                      -- Subject name
                confidence REAL DEFAULT 1.0,       -- Face recognition confidence
                device_id TEXT,                    -- Device used for attendance
                day_of_week TEXT                   -- Day of week
            )
            """)
            attendance_tables = ['attendance_records']
            print("Created standard attendance_records table")
        
        # Step 2: Check each table for required columns
        for table in attendance_tables:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = {row[1].lower(): row for row in cursor.fetchall()}
            print(f"Table {table} columns: {list(columns.keys())}")
            
            # Check for name column
            if 'name' not in columns and 'student_name' not in columns:
                name_candidates = ['student', 'student_username', 'username']
                found_alternative = False
                
                # Look for alternative name columns
                for alt_name in name_candidates:
                    if alt_name in columns:
                        # Create a view that maps the alternative column to name
                        cursor.execute(f"""
                        CREATE VIEW IF NOT EXISTS {table}_name_view AS
                        SELECT *, {alt_name} AS name
                        FROM {table}
                        """)
                        print(f"Created view {table}_name_view mapping {alt_name} to name")
                        found_alternative = True
                        break
                
                if not found_alternative:
                    # Add a name column if we can't find a suitable alternative
                    try:
                        cursor.execute(f"ALTER TABLE {table} ADD COLUMN name TEXT")
                        print(f"Added name column to {table}")
                        
                        # Try to populate it from the first text column
                        text_columns = [col for col, info in columns.items() 
                                       if info[2].upper() in ('TEXT', 'VARCHAR', 'CHAR', 'STRING')]
                        if text_columns and text_columns[0] != 'name':
                            cursor.execute(f"UPDATE {table} SET name = {text_columns[0]}")
                            print(f"Populated name column from {text_columns[0]}")
                    except Exception as e:
                        print(f"Could not add name column: {e}")
            
            # Check for timestamp column
            if 'timestamp' not in columns:
                time_candidates = ['date_time', 'datetime', 'time', 'created_at', 'date']
                found_alternative = False
                
                # Look for alternative timestamp columns
                for alt_time in time_candidates:
                    if alt_time in columns:
                        # Create a view that maps the alternative column to timestamp
                        cursor.execute(f"""
                        CREATE VIEW IF NOT EXISTS {table}_time_view AS
                        SELECT *, {alt_time} AS timestamp 
                        FROM {table}
                        """)
                        print(f"Created view {table}_time_view mapping {alt_time} to timestamp")
                        found_alternative = True
                        break
                
                if not found_alternative:
                    # Add a timestamp column if we can't find a suitable alternative
                    try:
                        cursor.execute(f"ALTER TABLE {table} ADD COLUMN timestamp TIMESTAMP")
                        cursor.execute(f"UPDATE {table} SET timestamp = CURRENT_TIMESTAMP")
                        print(f"Added timestamp column to {table}")
                    except Exception as e:
                        print(f"Could not add timestamp column: {e}")
        
        # Step 3: Create unified view for consistently accessing attendance data
        cursor.execute("DROP VIEW IF EXISTS attendance_unified")
        
        # Find the most suitable table to use as the base for the view
        base_table = 'attendance_records' if 'attendance_records' in attendance_tables else attendance_tables[0]
        
        # Get columns from the base table
        cursor.execute(f"PRAGMA table_info({base_table})")
        base_columns = {row[1].lower(): row[1] for row in cursor.fetchall()}
        
        # Build SQL for the unified view
        select_parts = []
        
        # ID column
        select_parts.append("id")
        
        # Name column with fallbacks
        if 'name' in base_columns:
            select_parts.append("name AS student_name")
        elif 'student_name' in base_columns:
            select_parts.append("student_name AS name")
        else:
            # Use the first column as name if no better option
            first_col = list(base_columns.values())[0]
            select_parts.append(f"{first_col} AS name")
            select_parts.append(f"{first_col} AS student_name")
        
        # Timestamp column with fallbacks
        if 'timestamp' in base_columns:
            select_parts.append("timestamp")
        elif 'date_time' in base_columns:
            select_parts.append("date_time AS timestamp")
        else:
            select_parts.append("CURRENT_TIMESTAMP AS timestamp")
        
        # Other common columns with fallbacks
        select_parts.append("COALESCE(confidence, 1.0) AS confidence")
        select_parts.append("COALESCE(device_id, 'unknown') AS device_id")
        select_parts.append("COALESCE(day_of_week, strftime('%w', timestamp)) AS day_of_week")
        
        # Create the unified view
        create_view_sql = f"""
        CREATE VIEW attendance_unified AS
        SELECT {', '.join(select_parts)}
        FROM {base_table}
        """
        
        cursor.execute(create_view_sql)
        print(f"Created attendance_unified view based on {base_table}")
        
        # Create standard view if it doesn't exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='view' AND name='attendance_records_view'")
        if not cursor.fetchone():
            # If attendance_records exists as a table, create a simple pass-through view
            if 'attendance_records' in attendance_tables:
                cursor.execute("""
                CREATE VIEW attendance_records_view AS
                SELECT * FROM attendance_records
                """)
            else:
                # Otherwise create a view that points to our unified view
                cursor.execute("""
                CREATE VIEW attendance_records_view AS
                SELECT * FROM attendance_unified
                """)
            print("Created attendance_records_view for compatibility")
        
        # Step 4: Add indices if they don't exist
        try:
            cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{base_table}_name ON {base_table}(name)")
            cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{base_table}_timestamp ON {base_table}(timestamp)")
            print(f"Added indices to {base_table} for performance")
        except Exception as e:
            print(f"Could not add indices: {e}")
        
        conn.commit()
        print("All attendance schema fixes have been applied successfully!")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"Error fixing attendance schema: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    fix_attendance_table_schema()
    
    print("\n-----------------------------------------")
    print("Attendance schema fixes have been applied.")
    print("You can now run the application without the schema error.")
    print("-----------------------------------------")
