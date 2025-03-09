import sqlite3
import os
import time
from datetime import datetime
import sys

# Add parent directory to path for importing time_format_utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.time_format_utils import convert_to_ampm_format, normalize_time_format

def enhance_database():
    """
    Enhance database tables with advanced features:
    1. Add proper indices for query optimization
    2. Add foreign key constraints for data integrity
    3. Create triggers for automatic updates
    4. Improve schema design with better constraints
    5. Add audit fields for tracking changes
    6. Convert time formats to AM/PM format
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
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"📋 Found {len(tables)} tables: {', '.join(tables)}")
        
        # Start a transaction for all changes
        cursor.execute("BEGIN TRANSACTION")
        
        # 1. Enhance attendance_log table
        enhance_attendance_log(cursor)
        
        # 2. Enhance class_attendance table
        enhance_class_attendance(cursor)
        
        # 3. Update class_attendance time format to AM/PM
        update_class_attendance_time_format(cursor)
        
        # 4. Enhance control_4 (schedule) table with AM/PM time format
        enhance_schedule_table(cursor)
        
        # 5. Enhance users table
        enhance_users_table(cursor)
        
        # 6. Create new metadata table
        create_metadata_table(cursor)
        
        # 7. Create new attendance_summary table for analytics
        create_attendance_summary_table(cursor)
        
        # 8. Create triggers for data consistency
        create_triggers(cursor)
        
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

def enhance_attendance_log(cursor):
    """Enhance the attendance_log table"""
    print("\n🔧 Enhancing attendance_log table...")
    
    # Check if column exists
    cursor.execute("PRAGMA table_info(attendance_log)")
    columns = {info[1] for info in cursor.fetchall()}
    
    # Add new columns without default values (to avoid "non-constant default" error)
    if 'created_at' not in columns:
        cursor.execute("ALTER TABLE attendance_log ADD COLUMN created_at TIMESTAMP")
        # Update the column with current timestamp after adding it
        cursor.execute("UPDATE attendance_log SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL")
        print("✅ Added created_at column to attendance_log")
    
    if 'location' not in columns:
        cursor.execute("ALTER TABLE attendance_log ADD COLUMN location TEXT")
        cursor.execute("UPDATE attendance_log SET location = 'main_campus' WHERE location IS NULL")
        print("✅ Added location column to attendance_log")
        
    if 'notes' not in columns:
        cursor.execute("ALTER TABLE attendance_log ADD COLUMN notes TEXT")
        print("✅ Added notes column to attendance_log")
    
    # Update day_of_week if it exists but might be NULL
    if 'day_of_week' in columns:
        cursor.execute("UPDATE attendance_log SET day_of_week = strftime('%A', timestamp) WHERE day_of_week IS NULL")
    
    # Add indices for performance optimization
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_attendance_log_name ON attendance_log(name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_attendance_log_timestamp ON attendance_log(timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_attendance_log_day ON attendance_log(day_of_week)")
    
    print("✅ Attendance log table enhanced with new columns and indices")

def enhance_class_attendance(cursor):
    """Enhance the class_attendance table"""
    print("\n🔧 Enhancing class_attendance table...")
    
    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='class_attendance'")
    if not cursor.fetchone():
        # Create the table if it doesn't exist
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
        # Set initial timestamps
        cursor.execute("UPDATE class_attendance SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL")
        print("✅ Created class_attendance table")
    else:
        # Table exists, add new columns without defaults
        cursor.execute("PRAGMA table_info(class_attendance)")
        columns = {info[1] for info in cursor.fetchall()}
        
        if 'attendance_time' not in columns:
            cursor.execute("ALTER TABLE class_attendance ADD COLUMN attendance_time TIMESTAMP")
            print("✅ Added attendance_time column to class_attendance")
            
        if 'detection_count' not in columns:
            cursor.execute("ALTER TABLE class_attendance ADD COLUMN detection_count INTEGER")
            cursor.execute("UPDATE class_attendance SET detection_count = 0 WHERE detection_count IS NULL")
            print("✅ Added detection_count column to class_attendance")
            
        if 'updated_at' not in columns:
            cursor.execute("ALTER TABLE class_attendance ADD COLUMN updated_at TIMESTAMP")
            cursor.execute("UPDATE class_attendance SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL")
            print("✅ Added updated_at column to class_attendance")
    
    # Add indices for performance optimization
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_class_attendance_student ON class_attendance(student_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_class_attendance_date ON class_attendance(class_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_class_attendance_subject ON class_attendance(subject)")
    
    print("✅ Added performance indices to class_attendance")

def enhance_schedule_table(cursor):
    """Enhance the control_4 (schedule) table with AM/PM time format"""
    print("\n🔧 Enhancing schedule table (control_4)...")
    
    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='control_4'")
    if cursor.fetchone():
        # Table exists, check its schema
        cursor.execute("PRAGMA table_info(control_4)")
        columns = {info[1] for info in cursor.fetchall()}
        
        # Create a new schedule table with better structure
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS schedule (
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
            created_at TIMESTAMP
        )
        """)
        
        # Add triggers for validation
        cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS check_schedule_type
        BEFORE INSERT ON schedule
        FOR EACH ROW
        WHEN NEW.type NOT IN ('lec', 'sec', 'lab')
        BEGIN
            SELECT RAISE(ABORT, 'Invalid type value. Must be lec, sec, or lab');
        END
        """)
        
        cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS check_schedule_day
        BEFORE INSERT ON schedule
        FOR EACH ROW
        WHEN NEW.day NOT IN ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')
        BEGIN
            SELECT RAISE(ABORT, 'Invalid day value');
        END
        """)
        
        # Add trigger to normalize time format to AM/PM
        cursor.execute("""
        DROP TRIGGER IF EXISTS normalize_schedule_time_format;
        """)
        
        cursor.execute("""
        CREATE TRIGGER normalize_schedule_time_format
        BEFORE INSERT ON schedule
        BEGIN
            -- Use a helper function for time normalization
            SELECT normalize_time_format(NEW.start_time) INTO NEW.start_time;
            SELECT normalize_time_format(NEW.end_time) INTO NEW.end_time;
        END;
        """)
        
        # Copy existing data with time format conversion
        copy_columns = list(columns.intersection({'subject', 'type', 'day'}))
        column_str = ', '.join(copy_columns)
        
        # Get existing data
        cursor.execute(f"SELECT {column_str}, start_time, end_time FROM control_4")
        rows = cursor.fetchall()
        
        # Insert data with converted times
        for row in rows:
            values = list(row)
            # Convert times to AM/PM format (they are at positions 3 and 4)
            values[3] = convert_to_ampm_format(values[3])  # start_time
            values[4] = convert_to_ampm_format(values[4])  # end_time
            
            # Add created_at timestamp
            values.append(datetime.now().isoformat())
            
            # Prepare placeholders for INSERT
            placeholders = ', '.join(['?'] * (len(values)))
            
            # Insert into schedule table with converted times
            cursor.execute(f"""
            INSERT OR IGNORE INTO schedule (
                {column_str}, start_time, end_time, created_at
            ) VALUES ({placeholders})
            """, values)
        
        # Create view for backward compatibility
        cursor.execute("DROP VIEW IF EXISTS control_4")
        cursor.execute("""
        CREATE VIEW control_4 AS
        SELECT subject, type, day, start_time, end_time
        FROM schedule WHERE active = 1
        """)
        
        print("✅ Created enhanced schedule table with AM/PM time format")
    else:
        # Create new schedule table
        cursor.execute("""
        CREATE TABLE schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            type TEXT NOT NULL,
            day TEXT NOT NULL,
            start_time TEXT NOT NULL,  -- Will store in AM/PM format
            end_time TEXT NOT NULL,    -- Will store in AM/PM format
            room TEXT,
            instructor TEXT,
            semester TEXT,
            active INTEGER DEFAULT 1,
            created_at TIMESTAMP
        )
        """)
        # Add triggers for validation
        cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS check_schedule_type
        BEFORE INSERT ON schedule
        FOR EACH ROW
        WHEN NEW.type NOT IN ('lec', 'sec', 'lab')
        BEGIN
            SELECT RAISE(ABORT, 'Invalid type value. Must be lec, sec, or lab');
        END
        """)
        
        cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS check_schedule_day
        BEFORE INSERT ON schedule
        FOR EACH ROW
        WHEN NEW.day NOT IN ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')
        BEGIN
            SELECT RAISE(ABORT, 'Invalid day value');
        END
        """)
        
        # Add trigger to normalize time format to AM/PM
        cursor.execute("""
        CREATE TRIGGER normalize_schedule_time_format
        BEFORE INSERT ON schedule
        FOR EACH ROW
        BEGIN
            -- Use the SQLite function we just added
            SELECT normalize_time_format(NEW.start_time) INTO NEW.start_time;
            SELECT normalize_time_format(NEW.end_time) INTO NEW.end_time;
        END;
        """)
        
        cursor.execute("UPDATE schedule SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL")
        print("✅ Created new schedule table with AM/PM time format support")
    
    # Add indices for performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_schedule_day ON schedule(day)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_schedule_subject ON schedule(subject)")
    
    print("✅ Added performance indices to schedule table")
    
    # Add a function to normalize time format in triggers
    cursor.execute("""
    CREATE TEMP FUNCTION normalize_time_format(time_str TEXT) 
    RETURNS TEXT
    BEGIN
        -- Check if already in AM/PM format
        IF time_str LIKE '%AM' OR time_str LIKE '%PM' THEN
            RETURN time_str;
        END IF;
        
        -- Try to convert from 24-hour format
        RETURN strftime('%I:%M %p', time_str, '2000-01-01');
    END;
    """)

def enhance_users_table(cursor):
    """Enhance the users table"""
    print("\n🔧 Enhancing users table...")
    
    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if cursor.fetchone():
        # Table exists, add columns one by one
        cursor.execute("PRAGMA table_info(users)")
        columns = {info[1] for info in cursor.fetchall()}
        
        if 'role' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN role TEXT")
            cursor.execute("UPDATE users SET role = 'student' WHERE role IS NULL")
            print("✅ Added role column to users")
            
        if 'full_name' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN full_name TEXT")
            print("✅ Added full_name column to users")
            
        if 'email' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")
            print("✅ Added email column to users")
            
        if 'created_at' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN created_at TIMESTAMP")
            cursor.execute("UPDATE users SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL")
            print("✅ Added created_at column to users")
            
        if 'last_login' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN last_login TIMESTAMP")
            print("✅ Added last_login column to users")
            
        if 'active' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN active INTEGER")
            cursor.execute("UPDATE users SET active = 1 WHERE active IS NULL")
            print("✅ Added active column to users")
        
        # Add role validation trigger
        cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS check_user_role
        BEFORE INSERT ON users
        FOR EACH ROW
        WHEN NEW.role NOT IN ('student', 'admin', 'teacher')
        BEGIN
            SELECT RAISE(ABORT, 'Invalid role. Must be student, admin, or teacher');
        END
        """)
        
        print("✅ Enhanced users table with new columns")
    else:
        # Create new users table
        cursor.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'student',
            full_name TEXT,
            email TEXT UNIQUE,
            created_at TIMESTAMP,
            last_login TIMESTAMP,
            active INTEGER DEFAULT 1
        )
        """)
        
        # Add role validation trigger
        cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS check_user_role
        BEFORE INSERT ON users
        FOR EACH ROW
        WHEN NEW.role NOT IN ('student', 'admin', 'teacher')
        BEGIN
            SELECT RAISE(ABORT, 'Invalid role. Must be student, admin, or teacher');
        END
        """)
        
        # Create default admin user if table is empty
        cursor.execute("""
        INSERT INTO users (username, password, role, full_name, created_at)
        VALUES ('admin', 'admin123', 'admin', 'System Administrator', CURRENT_TIMESTAMP)
        """)
        print("✅ Created new users table with default admin user")
    
    # Add indices for faster lookups
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)")
    
    print("✅ Added performance indices to users table")

def create_metadata_table(cursor):
    """Create a metadata table for system configuration"""
    print("\n🔧 Creating metadata table...")
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS system_metadata (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        description TEXT,
        updated_at TIMESTAMP
    )
    """)
    
    # Set timestamp after creation
    cursor.execute("UPDATE system_metadata SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL")
    
    # Insert some initial metadata
    metadata = [
        ('db_version', '1.0', 'Database schema version'),
        ('app_version', '1.0', 'Application version'),
        ('last_full_update', datetime.now().isoformat(), 'Last time the database was fully updated'),
        ('attendance_threshold', '0.6', 'Threshold for face recognition confidence'),
        ('auto_refresh_interval', '30', 'Default auto-refresh interval in seconds')
    ]
    
    for item in metadata:
        # Use separate insert and update to avoid CURRENT_TIMESTAMP issues
        cursor.execute("""
        INSERT OR IGNORE INTO system_metadata (key, value, description)
        VALUES (?, ?, ?)
        """, item)
        cursor.execute("""
        UPDATE system_metadata SET value = ?, description = ?, updated_at = CURRENT_TIMESTAMP
        WHERE key = ? AND (value != ? OR description != ?)
        """, (item[1], item[2], item[0], item[1], item[2]))
    
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
        updated_at TIMESTAMP,
        UNIQUE(student_name, date)
    )
    """)
    
    # Set timestamp after creation
    cursor.execute("UPDATE attendance_summary SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL")
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_summary_student ON attendance_summary(student_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_summary_date ON attendance_summary(date)")
    
    # Populate with existing data - try/catch to handle potential errors with control_4
    try:
        # Populate with existing data
        cursor.execute("""
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
                FROM attendance_log al 
                WHERE al.name = ca.student_name AND date(al.timestamp) = ca.class_date
            ) as detection_count,
            CURRENT_TIMESTAMP as updated_at
        FROM class_attendance ca
        GROUP BY ca.student_name, ca.class_date
        """)
        
        # Update first and last detection times
        cursor.execute("""
        WITH detection_times AS (
            SELECT 
                name as student_name,
                date(timestamp) as date,
                MIN(timestamp) as first_detection,
                MAX(timestamp) as last_detection
            FROM attendance_log
            GROUP BY name, date(timestamp)
        )
        
        UPDATE attendance_summary
        SET 
            first_detection_time = (
                SELECT first_detection 
                FROM detection_times dt
                WHERE dt.student_name = attendance_summary.student_name
                AND dt.date = attendance_summary.date
            ),
            last_detection_time = (
                SELECT last_detection
                FROM detection_times dt
                WHERE dt.student_name = attendance_summary.student_name
                AND dt.date = attendance_summary.date
            )
        WHERE EXISTS (
            SELECT 1 
            FROM detection_times dt
            WHERE dt.student_name = attendance_summary.student_name
            AND dt.date = attendance_summary.date
        )
        """)
        print("✅ Populated attendance_summary table with historical data")
    except Exception as e:
        print(f"⚠️ Could not populate attendance_summary with historical data: {e}")
        print("This may be normal if class_attendance table is empty")
    
    print("✅ Created attendance summary table")

def create_triggers(cursor):
    """Create triggers for data consistency"""
    print("\n🔧 Creating database triggers...")
    
    # Drop existing triggers first to avoid errors when recreating
    cursor.execute("DROP TRIGGER IF EXISTS trg_attendance_log_insert")
    cursor.execute("DROP TRIGGER IF EXISTS trg_class_attendance_update")
    cursor.execute("DROP TRIGGER IF EXISTS trg_user_login")
    
    # Trigger to update attendance summary when new attendance logs are added
    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS trg_attendance_log_insert
    AFTER INSERT ON attendance_log
    BEGIN
        -- Update class_attendance if within class time
        UPDATE class_attendance
        SET 
            attended = 1,
            attendance_time = COALESCE(attendance_time, NEW.timestamp),
            detection_count = detection_count + 1,
            updated_at = CURRENT_TIMESTAMP
        WHERE 
            student_name = NEW.name
            AND class_date = date(NEW.timestamp)
            AND time(NEW.timestamp) BETWEEN time(start_time) AND time(end_time);
            
        -- Update or insert summary record (with separate insert and update)
        INSERT OR IGNORE INTO attendance_summary 
            (student_name, date, detection_count, first_detection_time, last_detection_time, updated_at)
        VALUES 
            (NEW.name, date(NEW.timestamp), 1, NEW.timestamp, NEW.timestamp, CURRENT_TIMESTAMP);
            
        -- Update existing record with new values
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
    
    # Trigger to update attendance summary when class attendance is updated
    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS trg_class_attendance_update
    AFTER UPDATE ON class_attendance
    WHEN NEW.attended <> OLD.attended
    BEGIN
        -- Recalculate attendance summary
        UPDATE attendance_summary
        SET 
            attended_classes = (
                SELECT SUM(attended) 
                FROM class_attendance 
                WHERE student_name = NEW.student_name AND class_date = NEW.class_date
            ),
            attendance_rate = (
                SELECT (SUM(attended) * 100.0 / COUNT(*))
                FROM class_attendance 
                WHERE student_name = NEW.student_name AND class_date = NEW.class_date
            ),
            updated_at = CURRENT_TIMESTAMP
        WHERE 
            student_name = NEW.student_name 
            AND date = NEW.class_date;
    END;
    """)
    
    # Trigger to update user's last login timestamp
    cursor.execute("""
    CREATE TRIGGER IF NOT EXISTS trg_user_login
    AFTER UPDATE ON users
    WHEN NEW.last_login IS NOT OLD.last_login
    BEGIN
        -- Update system metadata for auditing
        INSERT OR IGNORE INTO system_metadata (key, value, description)
        VALUES (
            'last_login_' || NEW.username, 
            NEW.last_login, 
            'Last login timestamp for ' || NEW.username
        );
        
        UPDATE system_metadata 
        SET 
            value = NEW.last_login,
            updated_at = CURRENT_TIMESTAMP
        WHERE key = 'last_login_' || NEW.username;
    END;
    """)
    
    print("✅ Created database triggers for data consistency")

def update_class_attendance_time_format(cursor):
    """Update class_attendance table to use AM/PM time format"""
    print("\n🔧 Updating time formats in class_attendance table...")
    
    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='class_attendance'")
    if not cursor.fetchone():
        print("⚠️ class_attendance table doesn't exist, skipping time format update")
        return
    
    try:
        # Fetch all records with time values
        cursor.execute("SELECT id, start_time, end_time FROM class_attendance")
        rows = cursor.fetchall()
        
        # Convert times and update records
        for row_id, start_time, end_time in rows:
            am_pm_start = convert_to_ampm_format(start_time)
            am_pm_end = convert_to_ampm_format(end_time)
            
            # Only update if the format changed
            if am_pm_start != start_time or am_pm_end != end_time:
                cursor.execute(
                    "UPDATE class_attendance SET start_time = ?, end_time = ? WHERE id = ?",
                    (am_pm_start, am_pm_end, row_id)
                )
        
        # Add trigger to normalize time format on insert/update
        cursor.execute("DROP TRIGGER IF EXISTS normalize_class_attendance_time_format")
        cursor.execute("""
        CREATE TRIGGER normalize_class_attendance_time_format
        BEFORE INSERT ON class_attendance
        FOR EACH ROW
        BEGIN
            SELECT normalize_time_format(NEW.start_time) INTO NEW.start_time;
            SELECT normalize_time_format(NEW.end_time) INTO NEW.end_time;
        END;
        """)
        
        print("✅ Updated class_attendance table to use AM/PM time format")
    except Exception as e:
        print(f"⚠️ Error updating time formats: {e}")

if __name__ == "__main__":
    enhance_database()
