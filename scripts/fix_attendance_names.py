import sqlite3
import os
import sys

# Get the project root directory
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_dir)

DATABASE_PATH = os.path.join(project_dir, 'attendance_system.db')

def diagnose_and_fix_attendance_table():
    """Diagnose and fix the attendance_records table schema issues"""
    print(f"Examining database at {os.path.abspath(DATABASE_PATH)}")
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # Step 1: Check if attendance_records table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='attendance_records'")
        if not cursor.fetchone():
            # Try attendance_log as an alternative
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='attendance_log'")
            if cursor.fetchone():
                # Use attendance_log as the source and create attendance_records view
                print("Found attendance_log but not attendance_records")
                cursor.execute("""
                    CREATE VIEW IF NOT EXISTS attendance_records AS
                    SELECT * FROM attendance_log
                """)
                print("Created attendance_records view pointing to attendance_log")
                table_name = 'attendance_log'
            else:
                # No attendance table found, create one from scratch
                print("No attendance table found. Creating attendance_records table.")
                cursor.execute("""
                CREATE TABLE attendance_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    student_name TEXT NOT NULL, 
                    timestamp TIMESTAMP NOT NULL,
                    confidence REAL DEFAULT 1.0,
                    device_id TEXT,
                    day_of_week TEXT
                )
                """)
                print("Created attendance_records table with required columns")
                table_name = 'attendance_records'
        else:
            table_name = 'attendance_records'
        
        # Step 2: Examine the schema of the attendance table
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = {col[1].lower(): col for col in cursor.fetchall()}
        print(f"Current columns in {table_name}: {list(columns.keys())}")
        
        # Step 3: Check if required columns exist and add them if needed
        changes_made = False
        
        # Check for username column - ADD THIS FIRST
        if 'username' not in columns:
            print(f"Missing 'username' column in {table_name}. Adding it...")
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN username TEXT")
            changes_made = True
            
            # Try to populate it from existing columns
            possible_name_cols = ['student_name', 'name', 'student', 'student_username']
            for col in possible_name_cols:
                if col in columns:
                    cursor.execute(f"UPDATE {table_name} SET username = {col}")
                    print(f"Populated 'username' column from '{col}' column")
                    break
            else:
                print("No suitable column found to populate 'username' column")
                cursor.execute(f"UPDATE {table_name} SET username = 'Unknown User'")
                print(f"Set default value for username column")
        
        # Check for name column - keep for compatibility
        if 'name' not in columns:
            print(f"Missing 'name' column in {table_name}. Adding it...")
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN name TEXT")
            changes_made = True
            
            # Populate from username if it exists
            if 'username' in columns:
                cursor.execute(f"UPDATE {table_name} SET name = username")
                print(f"Populated 'name' column from 'username' column")
        
        # Check for student_name column - also keep for compatibility
        if 'student_name' not in columns:
            print(f"Missing 'student_name' column in {table_name}. Adding it...")
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN student_name TEXT")
            changes_made = True
            
            # Populate from username column if it exists
            if 'username' in columns:
                cursor.execute(f"UPDATE {table_name} SET student_name = username")
                print(f"Populated 'student_name' column from 'username' column")
        
        # Step 4: Add indexes for better performance
        try:
            cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_username ON {table_name}(username)")
            print(f"Created index on {table_name}(username)")
            
            # Keep legacy indexes for compatibility
            cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_name ON {table_name}(name)")
            print(f"Created index on {table_name}(name)")
            
            if 'student_name' in columns or changes_made:
                cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_student_name ON {table_name}(student_name)")
                print(f"Created index on {table_name}(student_name)")
        except Exception as e:
            print(f"Error creating indexes: {e}")
        
        # Step 5: Create a comprehensive view for attendance data
        cursor.execute("DROP VIEW IF EXISTS attendance_unified_view")
        cursor.execute(f"""
        CREATE VIEW attendance_unified_view AS
        SELECT 
            id, 
            username,
            username AS name,
            username AS student_name,
            timestamp,
            COALESCE(confidence, 1.0) AS confidence,
            COALESCE(device_id, 'unknown') AS device_id,
            COALESCE(day_of_week, strftime('%w', timestamp)) AS day_of_week
        FROM {table_name}
        """)
        print("Created attendance_unified_view with standardized column names (using username)")
        
        conn.commit()
        
        # Verify the fix by running a query
        cursor.execute(f"SELECT username, name, student_name FROM {table_name} LIMIT 3")
        sample_data = cursor.fetchall()
        print("\nSample data after fix:")
        for row in sample_data:
            print(f"  username: {row[0]}, name: {row[1]}, student_name: {row[2]}")
        
        print("\nFix completed successfully! The warning should no longer appear.")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"Error fixing attendance table: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    diagnose_and_fix_attendance_table()
