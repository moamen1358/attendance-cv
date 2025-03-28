import sqlite3
import os
import sys

# Add the project root to the path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.append(project_root)

# Database path
DATABASE_PATH = os.path.join(project_root, 'attendance_system.db')
print(f"Using database at: {os.path.abspath(DATABASE_PATH)}")

def repair_attendance_tables():
    """
    Comprehensive repair for attendance tables to fix schema issues
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        print("Starting attendance tables repair...")
        
        # Identify all attendance-related tables
        attendance_tables = []
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        for table in cursor.fetchall():
            table_name = table[0]
            if any(keyword in table_name.lower() for keyword in ['attend', 'record', 'log']):
                attendance_tables.append(table_name)
        
        print(f"Found {len(attendance_tables)} attendance-related tables: {attendance_tables}")
        
        # If no attendance tables found, create a standard one
        if not attendance_tables:
            cursor.execute("""
            CREATE TABLE attendance_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                name TEXT NOT NULL,
                student_name TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                confidence REAL DEFAULT 1.0,
                device_id TEXT,
                day_of_week TEXT
            )
            """)
            conn.commit()
            attendance_tables = ['attendance_records']
            print("Created standard attendance_records table")
        
        # Fix each attendance table
        for table_name in attendance_tables:
            print(f"Repairing table: {table_name}")
            
            # Get current columns
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = {col[1].lower(): col for col in cursor.fetchall()}
            print(f"Current columns: {list(columns.keys())}")
            
            # Check and fix username column - PRIORITIZE THIS
            if 'username' not in columns:
                print(f"Adding 'username' column to {table_name}")
                try:
                    cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN username TEXT")
                    
                    # Try to populate it from another suitable column
                    name_sources = ['student_username', 'student_name', 'name', 'student', 'user', 'person']
                    for source in name_sources:
                        if source in columns and source != 'username':
                            cursor.execute(f"UPDATE {table_name} SET username = {source} WHERE username IS NULL")
                            print(f"Populated 'username' from '{source}' column")
                            break
                    
                    # Set default value for any remaining nulls
                    cursor.execute(f"UPDATE {table_name} SET username = 'Unknown User' WHERE username IS NULL")
                    conn.commit()
                except Exception as e:
                    print(f"Error adding username column: {e}")
                    conn.rollback()
            
            # Check and fix name column - still keep for compatibility
            if 'name' not in columns:
                print(f"Adding 'name' column to {table_name}")
                try:
                    cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN name TEXT")
                    
                    # If username column exists, use it to populate name
                    if 'username' in columns:
                        cursor.execute(f"UPDATE {table_name} SET name = username WHERE name IS NULL")
                        print(f"Populated 'name' from 'username' column")
                    else:
                        # Try other sources
                        name_sources = ['student_name', 'student', 'student_username']
                        for source in name_sources:
                            if source in columns and source != 'name':
                                cursor.execute(f"UPDATE {table_name} SET name = {source} WHERE name IS NULL")
                                print(f"Populated 'name' from '{source}' column")
                                break
                    
                    # Set default value for any remaining nulls
                    cursor.execute(f"UPDATE {table_name} SET name = 'Unknown User' WHERE name IS NULL")
                    conn.commit()
                except Exception as e:
                    print(f"Error adding name column: {e}")
                    conn.rollback()
            
            # Check and fix student_name column - also keep for compatibility
            if 'student_name' not in columns:
                print(f"Adding 'student_name' column to {table_name}")
                try:
                    cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN student_name TEXT")
                    
                    # If username column exists, use it to populate student_name
                    if 'username' in columns:
                        cursor.execute(f"UPDATE {table_name} SET student_name = username WHERE student_name IS NULL")
                        print(f"Populated 'student_name' from 'username' column")
                    elif 'name' in columns:
                        cursor.execute(f"UPDATE {table_name} SET student_name = name WHERE student_name IS NULL")
                        print(f"Populated 'student_name' from 'name' column")
                    
                    # Set default value for any remaining nulls
                    cursor.execute(f"UPDATE {table_name} SET student_name = 'Unknown User' WHERE student_name IS NULL")
                    conn.commit()
                except Exception as e:
                    print(f"Error adding student_name column: {e}")
                    conn.rollback()
            
            # Check and fix timestamp column
            if 'timestamp' not in columns:
                print(f"Adding 'timestamp' column to {table_name}")
                try:
                    cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN timestamp TIMESTAMP")
                    
                    # Try to populate it from another suitable column
                    time_sources = ['date_time', 'datetime', 'time', 'created_at', 'date']
                    for source in time_sources:
                        if source in columns and source != 'timestamp':
                            cursor.execute(f"UPDATE {table_name} SET timestamp = {source} WHERE timestamp IS NULL")
                            print(f"Populated 'timestamp' from '{source}' column")
                            break
                    
                    # Set default value for any remaining nulls
                    cursor.execute(f"UPDATE {table_name} SET timestamp = CURRENT_TIMESTAMP WHERE timestamp IS NULL")
                    conn.commit()
                except Exception as e:
                    print(f"Error adding timestamp column: {e}")
                    conn.rollback()
            
            # Create indices for better performance
            try:
                # Add username index first - this is now the primary identifier
                cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_username ON {table_name}(username)")
                
                # Keep other indices for compatibility
                cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_name ON {table_name}(name)")
                cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_student_name ON {table_name}(student_name)")
                cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_timestamp ON {table_name}(timestamp)")
                conn.commit()
                print(f"Created indices on {table_name}")
            except Exception as e:
                print(f"Error creating indices: {e}")
        
        # Create views for compatibility
        print("Creating compatibility views...")
        
        # Create view for attendance_records if not the primary table
        if 'attendance_records' not in attendance_tables:
            main_table = attendance_tables[0]
            cursor.execute("DROP VIEW IF EXISTS attendance_records")
            cursor.execute(f"""
            CREATE VIEW attendance_records AS
            SELECT * FROM {main_table}
            """)
            print(f"Created attendance_records view pointing to {main_table}")
        
        # Create view for attendance_log if not the primary table and not already a view
        cursor.execute("SELECT name FROM sqlite_master WHERE type IN ('table', 'view') AND name='attendance_log'")
        if not cursor.fetchone():
            main_table = 'attendance_records' if 'attendance_records' in attendance_tables else attendance_tables[0]
            cursor.execute(f"""
            CREATE VIEW attendance_log AS
            SELECT * FROM {main_table}
            """)
            print(f"Created attendance_log view pointing to {main_table}")
        
        # Create a unified view that ensures consistent column access
        # Modified to use username as primary identifier
        unified_view_sql = """
        CREATE VIEW IF NOT EXISTS unified_attendance AS
        SELECT 
            id,
            username,  -- Primary identifier is now username
            username AS name,  -- Map username to name for compatibility
            username AS student_name,  -- Map username to student_name for compatibility
            timestamp,
            COALESCE(confidence, 1.0) AS confidence,
            COALESCE(device_id, 'unknown') AS device_id,
            COALESCE(day_of_week, strftime('%w', timestamp)) AS day_of_week
        FROM attendance_records
        """
        cursor.execute("DROP VIEW IF EXISTS unified_attendance")
        cursor.execute(unified_view_sql)
        print("Created unified_attendance view using username as primary identifier")
        
        conn.commit()
        print("Attendance tables repair completed successfully!")
        return True
    
    except Exception as e:
        print(f"Error repairing attendance tables: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    repair_attendance_tables()
    print("\nTo run this fix automatically when your app starts, add this code to your main.py or app.py:")
    print("""
    try:
        from scripts.repair_attendance_tables import repair_attendance_tables
        repair_attendance_tables()
        print("Attendance tables repair completed")
    except Exception as e:
        print(f"Error running attendance repair: {e}")
    """)
