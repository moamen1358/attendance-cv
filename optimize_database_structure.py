import sqlite3
import os
import time
import shutil

# Constants
DATABASE_PATH = 'attendance_system.db'
BACKUP_PATH = f'attendance_system_backup_{int(time.time())}.db'

# Current and new table names mapping
TABLE_RENAMES = {
    'students': 'student_profiles',
    'users': 'user_accounts',
    'presidents_embeds': 'facial_recognition_data',
    'attendance_log': 'attendance_records',
    'control_4': 'class_schedules',
    'class_attendance': 'class_attendance_records'
}

def backup_database():
    """Create a backup of the database before making changes"""
    if os.path.exists(DATABASE_PATH):
        shutil.copy2(DATABASE_PATH, BACKUP_PATH)
        print(f"Database backup created: {BACKUP_PATH}")
        return True
    else:
        print(f"Database file not found: {DATABASE_PATH}")
        return False

def get_table_schema(conn, table_name):
    """Get CREATE TABLE statement for the specified table"""
    cursor = conn.cursor()
    cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'")
    result = cursor.fetchone()
    return result[0] if result else None

def get_table_indexes(conn, table_name):
    """Get CREATE INDEX statements for the specified table"""
    cursor = conn.cursor()
    cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name='{table_name}' AND sql IS NOT NULL")
    return [row[0] for row in cursor.fetchall()]

def list_tables(conn):
    """Get a list of all tables in the database"""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    return [row[0] for row in cursor.fetchall()]

def rename_tables():
    """Rename tables with more professional, descriptive names"""
    if not backup_database():
        return False
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Check which tables exist in the database
    existing_tables = list_tables(conn)
    print(f"Existing tables: {existing_tables}")
    
    # Process each table that needs to be renamed
    for old_name, new_name in TABLE_RENAMES.items():
        if old_name not in existing_tables:
            print(f"Table '{old_name}' does not exist in the database, skipping.")
            continue
        
        try:
            print(f"Renaming table '{old_name}' to '{new_name}'...")
            
            # Get the CREATE TABLE statement
            schema = get_table_schema(conn, old_name)
            if not schema:
                print(f"Could not get schema for table '{old_name}', skipping.")
                continue
            
            # Replace the table name in the schema
            new_schema = schema.replace(f"CREATE TABLE {old_name}", f"CREATE TABLE {new_name}")
            
            # Get associated indexes
            indexes = get_table_indexes(conn, old_name)
            new_indexes = []
            for idx in indexes:
                new_indexes.append(idx.replace(f"ON {old_name}", f"ON {new_name}"))
            
            # Backup current data
            cursor.execute(f"CREATE TABLE temp_backup AS SELECT * FROM {old_name}")
            
            # Drop old table
            cursor.execute(f"DROP TABLE {old_name}")
            
            # Create new table with updated schema
            cursor.execute(new_schema)
            
            # Copy data from backup to new table
            cursor.execute(f"INSERT INTO {new_name} SELECT * FROM temp_backup")
            
            # Drop the temporary backup table
            cursor.execute("DROP TABLE temp_backup")
            
            # Recreate indexes with new table name
            for idx in new_indexes:
                cursor.execute(idx)
            
            print(f"Successfully renamed '{old_name}' to '{new_name}'")
            
        except sqlite3.Error as e:
            print(f"Error renaming table '{old_name}': {e}")
            conn.close()
            return False
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    print("\nAll tables renamed successfully!")
    return True

def update_foreign_keys():
    """Add proper foreign key relationships"""
    # This should be done after renaming tables, so we'll use the new table names
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # First enable foreign key support
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Create new tables with proper foreign key constraints
        
        # 1. Create temporary attendance_records table with foreign key constraint
        print("Adding foreign key constraints to attendance_records...")
        cursor.execute("""
        CREATE TABLE temp_attendance_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            confidence REAL,
            device_id TEXT,
            day_of_week TEXT,
            student_id TEXT,
            FOREIGN KEY (name) REFERENCES student_profiles(name) ON DELETE CASCADE
        )
        """)
        
        # Copy data
        cursor.execute("""
        INSERT INTO temp_attendance_records 
        SELECT id, name, timestamp, confidence, device_id, day_of_week, student_id 
        FROM attendance_records
        """)
        
        # Replace table
        cursor.execute("DROP TABLE attendance_records")
        cursor.execute("ALTER TABLE temp_attendance_records RENAME TO attendance_records")
        
        # 2. Create temporary class_attendance_records table with foreign key constraints
        print("Adding foreign key constraints to class_attendance_records...")
        cursor.execute("""
        CREATE TABLE temp_class_attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT NOT NULL,
            class_date DATE NOT NULL,
            subject TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            attended BOOLEAN NOT NULL DEFAULT 0,
            FOREIGN KEY (student_name) REFERENCES student_profiles(name) ON DELETE CASCADE,
            FOREIGN KEY (subject, start_time, end_time) REFERENCES class_schedules(subject, start_time, end_time) ON DELETE CASCADE,
            UNIQUE(student_name, class_date, subject, start_time)
        )
        """)
        
        # Copy data
        cursor.execute("""
        INSERT INTO temp_class_attendance 
        SELECT id, student_name, class_date, subject, start_time, end_time, attended 
        FROM class_attendance_records
        """)
        
        # Replace table
        cursor.execute("DROP TABLE class_attendance_records")
        cursor.execute("ALTER TABLE temp_class_attendance RENAME TO class_attendance_records")
        
        # 3. Add foreign key for facial_recognition_data
        print("Adding foreign key constraints to facial_recognition_data...")
        cursor.execute("""
        CREATE TABLE temp_facial_recognition (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            facial_features TEXT NOT NULL,
            FOREIGN KEY (name) REFERENCES student_profiles(name) ON DELETE CASCADE
        )
        """)
        
        # Copy data
        cursor.execute("""
        INSERT INTO temp_facial_recognition
        SELECT id, name, facial_features
        FROM facial_recognition_data
        """)
        
        # Replace table
        cursor.execute("DROP TABLE facial_recognition_data")
        cursor.execute("ALTER TABLE temp_facial_recognition RENAME TO facial_recognition_data")
        
        conn.commit()
        print("Foreign key constraints added successfully.")
        
    except sqlite3.Error as e:
        print(f"Error adding foreign key constraints: {e}")
        conn.rollback()
    
    conn.close()
    return True

def main():
    print("=== Database Structure Optimization ===")
    print("\nThis script will rename tables to follow better naming conventions:")
    for old, new in TABLE_RENAMES.items():
        print(f"  • {old} → {new}")
    
    print("\nIt will also add proper foreign key relationships between tables.")
    
    confirm = input("\nDo you want to continue? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Operation cancelled.")
        return
    
    # Rename tables
    if rename_tables():
        # Add foreign key constraints
        update_foreign_keys()
        
        print("\n=== Database Optimization Complete ===")
        print("Important: You'll need to update your code to use the new table names.")
        print("The following mappings should be used:")
        
        for old, new in TABLE_RENAMES.items():
            print(f"  • Replace '{old}' with '{new}' in your code")
        
        print("\nA backup of your original database was created before changes.")

if __name__ == "__main__":
    main()
