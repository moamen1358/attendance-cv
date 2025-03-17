import sqlite3
from database_utils import execute_query, execute_query_df
import os
import time
from datetime import datetime
import sys

# Add parent directory to path for importing time_format_utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.time_format_utils import convert_to_ampm_format, normalize_time_format

# Updated table name mappings (old_name -> new_name)
TABLE_MAPPINGS = {
    'students': 'student_profiles',
    'users': 'user_accounts',
    'presidents_embeds': 'facial_recognition_data',
    'attendance_log': 'attendance_records',
    'control_4': 'class_schedules',
    'class_attendance': 'class_attendance_records'
}

def enhance_database():
    """
    Enhance database tables with advanced features:
    1. Add proper indices for query optimization
    2. Add foreign key constraints for data integrity
    3. Create triggers for automatic updates
    4. Improve schema design with better constraints
    5. Add audit fields for tracking changes
    6. Convert time formats to AM/PM format
    7. Update all table names to modern naming convention
    """
    print("🔄 Starting database enhancement...")
    
    # Database path
    database_path = 'attendance_system.db'
    if not os.path.exists(database_path):
        print(f"❌ Error: Database file '{database_path}' not found.")
        return False
    
    # Connect to database with foreign key support
    conn = sqlite3.connect(database_path)
    conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
    
    try:
        # Backup the database first
        backup_path = f"attendance_system_backup_{int(time.time())}.db"
        print(f"📦 Creating backup at {backup_path}")
        
        backup_conn = sqlite3.connect(backup_path)
        conn.backup(backup_conn)
        backup_conn.close()
        print("✅ Backup created successfully")
        
        cursor = conn.cursor()
        
        # Check existing tables
        execute_query("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"📋 Found {len(tables)} tables: {', '.join(tables)}")
        
        # Check which tables need to be renamed
        rename_needed = {}
        for old_name, new_name in TABLE_MAPPINGS.items():
            if old_name in tables and new_name not in tables:
                rename_needed[old_name] = new_name
                print(f"🔄 Will rename {old_name} to {new_name}")
            elif old_name in tables and new_name in tables:
                print(f"⚠️ Both {old_name} and {new_name} exist. Will merge data.")
            elif new_name in tables:
                print(f"✅ Table {new_name} already exists")
            elif old_name not in tables and new_name not in tables:
                print(f"❌ Neither {old_name} nor {new_name} exists")
        
        # Start a transaction for all changes
        cursor.execute("BEGIN TRANSACTION")
        
        # 1. Rename tables if needed
        for old_name, new_name in rename_needed.items():
            rename_table(cursor, old_name, new_name)
        
        # 2. Enhance attendance records table
        enhance_attendance_records(cursor)
        
        # 3. Enhance class_attendance table
        enhance_class_attendance_records(cursor)
        
        # 4. Update class_attendance time format to AM/PM
        update_class_attendance_time_format(cursor)
        
        # 5. Enhance schedule table with AM/PM time format
        enhance_schedule_table(cursor)
        
        # 6. Enhance user_accounts table
        enhance_user_accounts_table(cursor)
        
        # 7. Create new metadata table
        create_metadata_table(cursor)
        
        # 8. Create new attendance_summary table for analytics
        create_attendance_summary_table(cursor)
        
        # 9. Create triggers for data consistency
        create_triggers(cursor)
        
        # 10. Update table references in views
        update_views(cursor)
        
        # Commit all changes
        cursor.execute("COMMIT")
        print("✅ All database enhancements completed successfully!")
        return True
    
    except Exception as e:
        print(f"❌ Error enhancing database: {str(e)}")
        cursor.execute("ROLLBACK")
        return False
    
    finally:
        conn.close()

def rename_table(cursor, old_name, new_name):
    """Rename a table and copy its indexes"""
    print(f"\n🔄 Renaming {old_name} to {new_name}...")
    
    # Create the new table with the same structure
    cursor.execute(f"CREATE TABLE {new_name} AS SELECT * FROM {old_name}")
    
    # Get indexes from the old table
    execute_query(f"PRAGMA index_list({old_name})")
    indexes = cursor.fetchall()
    
    # Recreate indexes on the new table
    for index_info in indexes:
        index_name = index_info[1]
        is_unique = index_info[2]
        
        # Get index columns
        execute_query(f"PRAGMA index_info({index_name})")
        columns = cursor.fetchall()
        column_names = [col[2] for col in columns]
        
        # Create index on new table
        unique_str = "UNIQUE" if is_unique else ""
        column_str = ", ".join(column_names)
        new_index_name = index_name.replace(old_name, new_name)
        cursor.execute(f"CREATE {unique_str} INDEX {new_index_name} ON {new_name}({column_str})")
    
    # Drop the old table
    cursor.execute(f"DROP TABLE {old_name}")
    
    print(f"✅ Renamed {old_name} to {new_name} and recreated indexes")

def enhance_attendance_records(cursor):
    """Enhance the attendance_records table"""
    print("\n🔧 Enhancing attendance_records table...")
    
    # Find the correct table name
    execute_query("SELECT name FROM sqlite_master WHERE type='table' AND (name='attendance_records' OR name='attendance_log')")
    result = cursor.fetchone()
    if not result:
        print("❌ Attendance records table not found")
        return
    
    table_name = result[0]
    
    # Check if column exists
    execute_query(f"PRAGMA table_info({table_name})")
    columns = {info[1] for info in cursor.fetchall()}
    
    # Add new columns without default values (to avoid "non-constant default" error)
    if 'created_at' not in columns:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN created_at TIMESTAMP")
        # Update the column with current timestamp after adding it
        cursor.execute(f"UPDATE {table_name} SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL")
        print(f"✅ Added created_at column to {table_name}")
    
    if 'location' not in columns:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN location TEXT")
        cursor.execute(f"UPDATE {table_name} SET location = 'main_campus' WHERE location IS NULL")
        print(f"✅ Added location column to {table_name}")
        
    if 'notes' not in columns:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN notes TEXT")
        print(f"✅ Added notes column to {table_name}")
    
    # Update day_of_week if it exists but might be NULL
    if 'day_of_week' in columns:
        cursor.execute(f"UPDATE {table_name} SET day_of_week = strftime('%A', timestamp) WHERE day_of_week IS NULL")
    
    # Add indices for performance optimization
    cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_name ON {table_name}(name)")
    cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_timestamp ON {table_name}(timestamp)")
    cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_day ON {table_name}(day_of_week)")
    
    print(f"✅ {table_name} table enhanced with new columns and indices")

def enhance_class_attendance_records(cursor):
    """Enhance the class_attendance table"""
    print("\n🔧 Enhancing class attendance records table...")
    
    # Find the correct table name
    execute_query("SELECT name FROM sqlite_master WHERE type='table' AND (name='class_attendance_records' OR name='class_attendance')")
    result = cursor.fetchone()
    if not result:
        # Create the table if it doesn't exist
        print("⚠️ Class attendance table not found, creating it...")
        cursor.execute("""
        CREATE TABLE class_attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT NOT NULL,
            class_date DATE NOT NULL,
            subject TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            attended BOOLEAN NOT NULL DEFAULT 0,
            attendance_time TIMESTAMP,
            detection_count INTEGER DEFAULT 0,
            updated_at TIMESTAMP,
            UNIQUE(student_name, class_date, subject, start_time)
        )
        """)
        return
    
    table_name = result[0]
    
    # Check if columns exist
    execute_query(f"PRAGMA table_info({table_name})")
    columns = {info[1] for info in cursor.fetchall()}
    
    if 'attendance_time' not in columns:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN attendance_time TIMESTAMP")
        print(f"✅ Added attendance_time column to {table_name}")
        
    if 'detection_count' not in columns:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN detection_count INTEGER")
        cursor.execute(f"UPDATE {table_name} SET detection_count = 0 WHERE detection_count IS NULL")
        print(f"✅ Added detection_count column to {table_name}")
        
    if 'updated_at' not in columns:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN updated_at TIMESTAMP")
        cursor.execute(f"UPDATE {table_name} SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL")
        print(f"✅ Added updated_at column to {table_name}")
    
    # Add indices for performance optimization
    cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_student ON {table_name}(student_name)")
    cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_date ON {table_name}(class_date)")
    cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_subject ON {table_name}(subject)")
    
    print(f"✅ Added performance indices to {table_name}")

def enhance_schedule_table(cursor):
    """Enhance the schedule table with AM/PM time format"""
    print("\n🔧 Enhancing schedule table...")
    
    # Find the correct table name
    execute_query("SELECT name FROM sqlite_master WHERE type='table' AND (name='class_schedules' OR name='control_4')")
    result = cursor.fetchone()
    if not result:
        # Create a new schedule table
        print("⚠️ Schedule table not found, creating it...")
        cursor.execute("""
        CREATE TABLE class_schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            type TEXT NOT NULL,
            day TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            room TEXT,
            instructor TEXT,
            semester TEXT,
            active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        return
    
    table_name = result[0]
    
    # Get column info
    execute_query(f"PRAGMA table_info({table_name})")
    columns = {info[1] for info in cursor.fetchall()}
    
    # Add columns if they don't exist
    if 'room' not in columns:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN room TEXT")
        print(f"✅ Added room column to {table_name}")
        
    if 'instructor' not in columns:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN instructor TEXT")
        print(f"✅ Added instructor column to {table_name}")
        
    if 'semester' not in columns:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN semester TEXT")
        print(f"✅ Added semester column to {table_name}")
        
    if 'active' not in columns:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN active INTEGER DEFAULT 1")
        cursor.execute(f"UPDATE {table_name} SET active = 1 WHERE active IS NULL")
        print(f"✅ Added active column to {table_name}")
        
    if 'created_at' not in columns:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN created_at TIMESTAMP")
        cursor.execute(f"UPDATE {table_name} SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL")
        print(f"✅ Added created_at column to {table_name}")
    
    # Convert time columns to AM/PM format
    print("🔄 Converting time formats to AM/PM...")
    execute_query(f"SELECT id, start_time, end_time FROM {table_name}")
    rows = cursor.fetchall()
    
    for row_id, start_time, end_time in rows:
        am_pm_start = convert_to_ampm_format(start_time)
        am_pm_end = convert_to_ampm_format(end_time)
        
        # Only update if needed
        if am_pm_start != start_time or am_pm_end != end_time:
            cursor.execute(
                f"UPDATE {table_name} SET start_time = ?, end_time = ? WHERE id = ?",
                (am_pm_start, am_pm_end, row_id)
            )
    
    # Add indices for performance
    cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_day ON {table_name}(day)")
    cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_subject ON {table_name}(subject)")
    
    print(f"✅ Enhanced {table_name} with time formats and new columns")

def enhance_user_accounts_table(cursor):
    """Enhance the user_accounts table"""
    print("\n🔧 Enhancing user accounts table...")
    
    # Find the correct table name
    execute_query("SELECT name FROM sqlite_master WHERE type='table' AND (name='user_accounts' OR name='users')")
    result = cursor.fetchone()
    if not result:
        # Create new user_accounts table
        print("⚠️ User accounts table not found, creating it...")
        cursor.execute("""
        CREATE TABLE user_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'student',
            full_name TEXT,
            email TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            active INTEGER DEFAULT 1
        )
        """)
        return
    
    table_name = result[0]
    
    # Get column info
    execute_query(f"PRAGMA table_info({table_name})")
    columns = {info[1] for info in cursor.fetchall()}
    
    # Add needed columns
    if 'role' not in columns:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN role TEXT DEFAULT 'student'")
        cursor.execute(f"UPDATE {table_name} SET role = 'student' WHERE role IS NULL")
        print(f"✅ Added role column to {table_name}")
        
    if 'full_name' not in columns:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN full_name TEXT")
        print(f"✅ Added full_name column to {table_name}")
        
    if 'email' not in columns:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN email TEXT")
        print(f"✅ Added email column to {table_name}")
        
    if 'created_at' not in columns:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN created_at TIMESTAMP")
        cursor.execute(f"UPDATE {table_name} SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL")
        print(f"✅ Added created_at column to {table_name}")
        
    if 'last_login' not in columns:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN last_login TIMESTAMP")
        print(f"✅ Added last_login column to {table_name}")
        
    if 'active' not in columns:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN active INTEGER DEFAULT 1")
        cursor.execute(f"UPDATE {table_name} SET active = 1 WHERE active IS NULL")
        print(f"✅ Added active column to {table_name}")
    
    # Add indices for faster lookups
    cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_role ON {table_name}(role)")
    
    print(f"✅ Enhanced {table_name} table with additional columns and indices")

def update_class_attendance_time_format(cursor):
    """Update class_attendance time format to AM/PM"""
    print("\n🔧 Updating time formats in class attendance records...")
    
    # Find the correct table name
    execute_query("SELECT name FROM sqlite_master WHERE type='table' AND (name='class_attendance_records' OR name='class_attendance')")
    result = cursor.fetchone()
    if not result:
        print("⚠️ Class attendance table not found, skipping time format update")
        return
    
    table_name = result[0]
    
    try:
        # Fetch records with time values
        execute_query(f"SELECT id, start_time, end_time FROM {table_name}")
        rows = cursor.fetchall()
        
        updated_count = 0
        for row_id, start_time, end_time in rows:
            am_pm_start = convert_to_ampm_format(start_time)
            am_pm_end = convert_to_ampm_format(end_time)
            
            # Only update if needed
            if am_pm_start != start_time or am_pm_end != end_time:
                cursor.execute(
                    f"UPDATE {table_name} SET start_time = ?, end_time = ? WHERE id = ?",
                    (am_pm_start, am_pm_end, row_id)
                )
                updated_count += 1
        
        print(f"✅ Updated {updated_count} records in {table_name} to use AM/PM time format")
    except Exception as e:
        print(f"⚠️ Error updating time formats: {e}")

def create_metadata_table(cursor):
    """Create a metadata table for system configuration"""
    print("\n🔧 Creating metadata table...")
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS system_metadata (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        description TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Insert initial metadata
    metadata = [
        ('db_version', '1.1', 'Database schema version'),
        ('app_version', '1.0', 'Application version'),
        ('last_full_update', datetime.now().isoformat(), 'Last time the database was fully updated'),
        ('attendance_threshold', '0.6', 'Threshold for face recognition confidence'),
        ('auto_refresh_interval', '30', 'Default auto-refresh interval in seconds'),
        ('tables_renamed', 'true', 'Whether tables have been renamed to new naming convention')
    ]
    
    for item in metadata:
        # Insert or update
        cursor.execute("""
        INSERT OR REPLACE INTO system_metadata (key, value, description, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """, item)
    
    print("✅ Created metadata table with initial settings")

def create_attendance_summary_table(cursor):
    """Create a summary table for attendance analytics"""
    print("\n🔧 Creating attendance summary table...")
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attendance_summary (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_name TEXT NOT NULL,
        date DATE NOT NULL,
        total_classes INTEGER DEFAULT 0,
        attended_classes INTEGER DEFAULT 0,
        attendance_rate REAL DEFAULT 0,
        first_detection_time TIMESTAMP,
        last_detection_time TIMESTAMP,
        detection_count INTEGER DEFAULT 0,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(student_name, date)
    )
    """)
    
    # Add indices for performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_summary_student ON attendance_summary(student_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_summary_date ON attendance_summary(date)")
    
    # Find attendance record table name
    execute_query("SELECT name FROM sqlite_master WHERE type='table' AND (name='attendance_records' OR name='attendance_log')")
    attendance_table = cursor.fetchone()[0] if cursor.fetchone() else None
    
    # Find class attendance table name
    execute_query("SELECT name FROM sqlite_master WHERE type='table' AND (name='class_attendance_records' OR name='class_attendance')")
    class_table = cursor.fetchone()[0] if cursor.fetchone() else None
    
    if attendance_table and class_table:
        # Try to populate summary table from existing data
        try:
            # This query is designed to work with either old or new table names
            cursor.execute(f"""
            INSERT OR IGNORE INTO attendance_summary 
                (student_name, date, total_classes, attended_classes, attendance_rate, detection_count, updated_at)
            SELECT 
                ca.student_name,
                ca.class_date,
                COUNT(*) as total_classes,
                SUM(ca.attended) as attended_classes,
                CASE 
                    WHEN COUNT(*) > 0 THEN (SUM(ca.attended) * 100.0 / COUNT(*)) 
                    ELSE 0 
                END as attendance_rate,
                (
                    SELECT COUNT(*) 
                    FROM {attendance_table} al 
                    WHERE al.name = ca.student_name AND date(al.timestamp) = ca.class_date
                ) as detection_count,
                CURRENT_TIMESTAMP as updated_at
            FROM {class_table} ca
            GROUP BY ca.student_name, ca.class_date
            """)
            print("✅ Populated attendance summary with historical data")
        except Exception as e:
            print(f"⚠️ Could not populate summary: {e}")
    
    print("✅ Created attendance summary table")

def create_triggers(cursor):
    """Create triggers for data consistency"""
    print("\n🔧 Creating database triggers...")
    
    # Find table names
    execute_query("SELECT name FROM sqlite_master WHERE type='table' AND (name='attendance_records' OR name='attendance_log')")
    attendance_table = cursor.fetchone()
    attendance_table = attendance_table[0] if attendance_table else None
    
    execute_query("SELECT name FROM sqlite_master WHERE type='table' AND (name='class_attendance_records' OR name='class_attendance')")
    class_table = cursor.fetchone()
    class_table = class_table[0] if class_table else None
    
    execute_query("SELECT name FROM sqlite_master WHERE type='table' AND (name='user_accounts' OR name='users')")
    user_table = cursor.fetchone()
    user_table = user_table[0] if user_table else None
    
    if not attendance_table or not class_table or not user_table:
        print("⚠️ Cannot create triggers: one or more required tables are missing")
        return
    
    # Drop existing triggers to avoid conflicts
    cursor.execute(f"DROP TRIGGER IF EXISTS trg_{attendance_table}_insert")
    cursor.execute(f"DROP TRIGGER IF EXISTS trg_{class_table}_update")
    cursor.execute(f"DROP TRIGGER IF EXISTS trg_{user_table}_login")
    
    # Update attendance summary when new attendance is logged
    cursor.execute(f"""
    CREATE TRIGGER IF NOT EXISTS trg_{attendance_table}_insert
    AFTER INSERT ON {attendance_table}
    BEGIN
        -- Update class attendance records
        UPDATE {class_table}
        SET 
            attended = 1,
            attendance_time = COALESCE(attendance_time, NEW.timestamp),
            detection_count = detection_count + 1,
            updated_at = CURRENT_TIMESTAMP
        WHERE 
            student_name = NEW.name
            AND class_date = date(NEW.timestamp)
            AND time(NEW.timestamp) BETWEEN time(start_time) AND time(end_time);
            
        -- Update attendance summary
        INSERT OR IGNORE INTO attendance_summary 
            (student_name, date, detection_count, first_detection_time, last_detection_time)
        VALUES 
            (NEW.name, date(NEW.timestamp), 1, NEW.timestamp, NEW.timestamp);
            
        UPDATE attendance_summary
        SET 
            detection_count = detection_count + 1,
            first_detection_time = MIN(COALESCE(first_detection_time, NEW.timestamp), NEW.timestamp),
            last_detection_time = MAX(COALESCE(last_detection_time, NEW.timestamp), NEW.timestamp),
            updated_at = CURRENT_TIMESTAMP
        WHERE 
            student_name = NEW.name 
            AND date = date(NEW.timestamp);
    END;
    """)
    
    # Update attendance summary when class attendance changes
    cursor.execute(f"""
    CREATE TRIGGER IF NOT EXISTS trg_{class_table}_update
    AFTER UPDATE ON {class_table}
    WHEN NEW.attended <> OLD.attended
    BEGIN
        -- Update attendance summary
        UPDATE attendance_summary
        SET 
            attended_classes = (
                SELECT SUM(attended) 
                FROM {class_table}
                WHERE student_name = NEW.student_name AND class_date = NEW.class_date
            ),
            total_classes = (
                SELECT COUNT(*) 
                FROM {class_table}
                WHERE student_name = NEW.student_name AND class_date = NEW.class_date
            ),
            attendance_rate = (
                SELECT (SUM(attended) * 100.0 / COUNT(*))
                FROM {class_table}
                WHERE student_name = NEW.student_name AND class_date = NEW.class_date
            ),
            updated_at = CURRENT_TIMESTAMP
        WHERE 
            student_name = NEW.student_name 
            AND date = NEW.class_date;
    END;
    """)
    
    # Update when user logs in
    cursor.execute(f"""
    CREATE TRIGGER IF NOT EXISTS trg_{user_table}_login
    AFTER UPDATE ON {user_table}
    WHEN NEW.last_login IS NOT OLD.last_login
    BEGIN
        -- Update system metadata for auditing
        INSERT OR IGNORE INTO system_metadata (key, value, description, updated_at)
        VALUES (
            'last_login_' || NEW.username, 
            NEW.last_login, 
            'Last login timestamp for ' || NEW.username,
            CURRENT_TIMESTAMP
        );
        
        UPDATE system_metadata 
        SET 
            value = NEW.last_login,
            updated_at = CURRENT_TIMESTAMP
        WHERE key = 'last_login_' || NEW.username;
    END;
    """)
    
    print("✅ Created database triggers for data consistency")

def update_views(cursor):
    """Update any existing views to use new table names"""
    print("\n🔧 Updating database views...")
    
    # Check which tables exist (old or new names)
    table_exists = {}
    for old_name, new_name in TABLE_MAPPINGS.items():
        execute_query(f"SELECT 1 FROM sqlite_master WHERE type='table' AND name='{old_name}'")
        old_exists = bool(cursor.fetchone())
        
        execute_query(f"SELECT 1 FROM sqlite_master WHERE type='table' AND name='{new_name}'")
        new_exists = bool(cursor.fetchone())
        
        # Determine which name to use (prefer new name)
        table_exists[old_name] = old_name if old_exists and not new_exists else new_name if new_exists else None
    
    # Update the control_4 view if needed
    if table_exists.get('control_4') == 'class_schedules' or table_exists.get('class_schedules'):
        schedule_table = table_exists.get('control_4', 'class_schedules')
        
        # Drop and recreate the view
        cursor.execute("DROP VIEW IF EXISTS control_4")
        cursor.execute(f"""
        CREATE VIEW control_4 AS
        SELECT subject, type, day, start_time, end_time
        FROM {schedule_table} WHERE active = 1
        """)
        print("✅ Updated control_4 view to use new table name")
    
    # Create other compatibility views if needed
    for old_name, new_name in TABLE_MAPPINGS.items():
        if old_name != 'control_4' and table_exists.get(old_name) == new_name:
            cursor.execute(f"DROP VIEW IF EXISTS {old_name}")
            cursor.execute(f"CREATE VIEW {old_name} AS SELECT * FROM {new_name}")
            print(f"✅ Created compatibility view {old_name} -> {new_name}")
    
    print("✅ Updated views for backwards compatibility")

if __name__ == "__main__":
    enhance_database()
