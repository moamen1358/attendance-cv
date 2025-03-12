import sqlite3
import os
from datetime import datetime
import pandas as pd
from tabulate import tabulate

# Constants
DATABASE_PATH = 'attendance_system.db'

# Sample schedule data - updated with SEC 1 instead of WC1
SCHEDULE_DATA = [
    # Format: subject, day, start_time, end_time, type, section, teacher, room
    ('Advanced Mathematics', 'Monday', '9:00 AM', '11:00 AM', 'lec', 'SEC 1', 'Dr. Alexander Smith', 'Hall A'),
    ('Advanced Mathematics', 'Wednesday', '2:00 PM', '3:30 PM', 'sec', 'SEC 2', 'Prof. Linda Johnson', 'Room 201'),
    ('Computer Science', 'Tuesday', '10:00 AM', '12:00 PM', 'lec', 'SEC 1', 'Dr. Rebecca Williams', 'Hall B'),
    ('Computer Science', 'Thursday', '1:00 PM', '3:00 PM', 'lab', 'SEC 2', 'Dr. Rebecca Williams', 'Lab 101'),
    ('Physics', 'Monday', '1:00 PM', '3:00 PM', 'lec', 'SEC 1', 'Dr. Thomas Brown', 'Hall C'),
    ('Physics', 'Friday', '10:00 AM', '12:00 PM', 'sec', 'SEC 2', 'Prof. Sarah Davis', 'Lab 202'),
    ('Engineering', 'Tuesday', '2:00 PM', '4:00 PM', 'lec', 'SEC 1', 'Dr. Emily Martin', 'Hall D'),
    ('Engineering', 'Thursday', '9:00 AM', '11:00 AM', 'lab', 'SEC 2', 'Dr. Emily Martin', 'Workshop'),
    ('Statistics', 'Wednesday', '9:00 AM', '11:00 AM', 'lec', 'SEC 1', 'Prof. Michael Taylor', 'Hall E'),
    ('Statistics', 'Friday', '1:00 PM', '3:00 PM', 'sec', 'SEC 2', 'Prof. Michael Taylor', 'Room 303'),
]

# ... existing code ...

# The reset_class_schedule function and the main function remain the same
# They will now use the updated SCHEDULE_DATA list with SEC 1 instead of WC1

def get_db_connection():
    """Create a connection to the database"""
    return sqlite3.connect(DATABASE_PATH)

def reset_class_schedule():
    """Delete existing class schedule tables and create new ones"""
    print("\n🔄 Resetting class schedule tables...")
    
    if not os.path.exists(DATABASE_PATH):
        print(f"❌ Error: Database file '{DATABASE_PATH}' not found.")
        return False
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Start transaction
        cursor.execute("BEGIN TRANSACTION")
        
        # Check for existing class schedule tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND (name='class_schedules' OR name='control_4')")
        existing_tables = cursor.fetchall()
        
        # Drop the existing tables
        tables_dropped = 0
        for table in existing_tables:
            table_name = table[0]
            print(f"🗑️ Dropping table: {table_name}")
            cursor.execute(f"DROP TABLE {table_name}")
            tables_dropped += 1
            
        if tables_dropped > 0:
            print(f"✅ Dropped {tables_dropped} existing schedule tables")
        else:
            print("ℹ️ No existing schedule tables found")
        
        # Create new table with correct structure
        print("\n📦 Creating new class_schedules table...")
        cursor.execute("""
        CREATE TABLE class_schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            day TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            type TEXT NOT NULL,
            section TEXT,
            teacher TEXT,
            room TEXT,
            active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Create indices for better performance
        cursor.execute("CREATE INDEX idx_schedules_subject ON class_schedules(subject)")
        cursor.execute("CREATE INDEX idx_schedules_day ON class_schedules(day)")
        
        print("✅ Created new class_schedules table with all required columns")
        
        # Insert sample data
        print("\n📝 Inserting sample class schedule data...")
        
        sql = """
        INSERT INTO class_schedules (subject, day, start_time, end_time, type, section, teacher, room)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        cursor.executemany(sql, SCHEDULE_DATA)
        
        # Verify successful insertion
        cursor.execute("SELECT COUNT(*) FROM class_schedules")
        count = cursor.fetchone()[0]
        
        if count == len(SCHEDULE_DATA):
            print(f"✅ Successfully inserted {count} class records")
        else:
            print(f"⚠️ Only {count} of {len(SCHEDULE_DATA)} records were inserted")
            
        # Create a compatible view for backward compatibility
        cursor.execute("DROP VIEW IF EXISTS control_4")
        cursor.execute("""
        CREATE VIEW control_4 AS
        SELECT subject, type, day, start_time, end_time, section, teacher, room
        FROM class_schedules
        """)
        print("✅ Created control_4 view for compatibility")
        
        # Commit all changes
        cursor.execute("COMMIT")
        print("\n✅ Class schedule reset complete!")
        
        # Show the table structure
        cursor.execute("PRAGMA table_info(class_schedules)")
        columns = cursor.fetchall()
        columns_df = pd.DataFrame(columns, columns=['ID', 'Name', 'Type', 'NotNull', 'DefaultValue', 'PK'])
        
        print("\n=== New Table Structure ===")
        print(tabulate(columns_df[['ID', 'Name', 'Type']], headers='keys', tablefmt='pretty'))
        
        # Show sample of the data
        cursor.execute("""
        SELECT subject, day, start_time, end_time, type, section, teacher, room 
        FROM class_schedules 
        LIMIT 5
        """)
        rows = cursor.fetchall()
        sample_df = pd.DataFrame(rows, columns=['subject', 'day', 'start_time', 'end_time', 'type', 'section', 'teacher', 'room'])
        
        print("\n=== Sample Data ===")
        print(tabulate(sample_df, headers='keys', tablefmt='pretty', showindex=False))
        
        return True
    
    except Exception as e:
        print(f"❌ Error: {e}")
        cursor.execute("ROLLBACK")
        return False
        
    finally:
        conn.close()

def main():
    """Main function"""
    print("🔧 Class Schedule Database Reset Tool")
    print("This will delete any existing class schedule tables and create new ones with sample data")
    
    # Ask for confirmation
    confirm = input("\n⚠️ WARNING: This will delete all existing class schedule data. Continue? (yes/no): ")
    
    if confirm.lower() != 'yes':
        print("Operation cancelled.")
        return
    
    # Create backup first
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"attendance_system_backup_{timestamp}.db"
    
    try:
        # Create backup
        with sqlite3.connect(DATABASE_PATH) as src_conn:
            with sqlite3.connect(backup_file) as backup_conn:
                src_conn.backup(backup_conn)
        print(f"✅ Created database backup: {backup_file}")
    except Exception as e:
        print(f"❌ Failed to create backup: {e}")
        retry = input("Continue without backup? (yes/no): ")
        if retry.lower() != 'yes':
            print("Operation cancelled.")
            return
    
    # Reset the class schedule
    reset_class_schedule()
    
    print("\nDone! You can now use the class schedule with SEC 1 and SEC 2 sections.")

if __name__ == "__main__":
    main()
