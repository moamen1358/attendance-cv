import sqlite3
import os
import sys
from datetime import datetime, timedelta
import random

# Add project root to path
sys.path.append('/home/invisa/Desktop/my_grad_streamlit')

# Database path
DB_PATH = 'attendance_system.db'

def connect_db():
    """Create a connection to the database"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def drop_tables(cursor, confirm=True):
    """Drop existing tables if they exist"""
    if confirm:
        confirm = input("⚠️ WARNING: This will drop all existing tables. Continue? (y/n): ")
        if confirm.lower() != 'y':
            print("Operation cancelled by user.")
            return False

    print("Dropping existing tables...")
    
    # Disable foreign key constraints temporarily to avoid circular references
    cursor.execute("PRAGMA foreign_keys = OFF")
    
    # Get list of all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row[0] for row in cursor.fetchall()]
    
    # Drop each table
    for table in tables:
        try:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
            print(f"  Dropped table: {table}")
        except Exception as e:
            print(f"  Error dropping table {table}: {e}")
    
    # Re-enable foreign key constraints
    cursor.execute("PRAGMA foreign_keys = ON")
    
    print("All tables dropped successfully.")
    return True

def create_tables(cursor):
    """Create the database tables with proper schema"""
    print("Creating tables...")
    
    # Create user_accounts table (unified user table)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    print("  Created table: user_accounts")
    
    # Create student_profiles table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS student_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        student_id TEXT UNIQUE,
        password TEXT NOT NULL,
        section TEXT,
        email TEXT,
        phone TEXT,
        last_login TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    print("  Created table: student_profiles")
    
    # Create professor_profiles table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS professor_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        password TEXT NOT NULL,
        email TEXT,
        phone TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    print("  Created table: professor_profiles")
    
    # Create subjects table with correct schema
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,  # Ensure the column is named 'name'
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    print("  Created table: subjects")
    
    # Verify the schema was created properly
    cursor.execute("PRAGMA table_info(subjects)")
    columns = [info[1] for info in cursor.fetchall()]
    print(f"  Created table: subjects with columns: {columns}")
    
    # Create class_schedules table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS class_schedules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject TEXT NOT NULL,
        day TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        type TEXT,
        room TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    print("  Created table: class_schedules")
    
    # Create attendance_records table with proper name column
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS attendance_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_username TEXT NOT NULL,
        name TEXT, 
        subject_id INTEGER,
        timestamp TIMESTAMP NOT NULL,
        status TEXT,
        class_date TEXT
    )
    ''')
    print("  Created table: attendance_records")
    
    # Create class_attendance table for detailed attendance tracking
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS class_attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_name TEXT NOT NULL,
        class_date TEXT NOT NULL,
        subject TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        attended BOOLEAN NOT NULL DEFAULT 0,
        UNIQUE(student_name, class_date, subject, start_time)
    )
    ''')
    print("  Created table: class_attendance")
    
    # Create login_logs table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS login_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        login_time TIMESTAMP NOT NULL,
        ip_address TEXT,
        status TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    print("  Created table: login_logs")
    
    print("All tables created successfully.")

def insert_sample_data(cursor):
    """Insert sample data into the tables"""
    print("Inserting sample data...")
    
    # Insert users into user_accounts
    users = [
        ('admin', 'admin123', 'admin'),
        ('student', 'student123', 'student'),
        ('professor', 'professor123', 'professor'),
        ('student1', 'password123', 'student'),
        ('student2', 'password123', 'student'),
        ('teacher1', 'password123', 'professor')
    ]
    cursor.executemany("INSERT INTO user_accounts (username, password, role) VALUES (?, ?, ?)", users)
    print(f"  Inserted {len(users)} users into user_accounts")
    
    # Insert students into student_profiles
    students = [
        ('student', 'Default Student', 'STU001', 'student123', 'A', 'student@example.com', '123-456-7890'),
        ('student1', 'John Smith', 'STU002', 'password123', 'B', 'john@example.com', '123-456-7891'),
        ('student2', 'Jane Doe', 'STU003', 'password123', 'A', 'jane@example.com', '123-456-7892')
    ]
    cursor.executemany("INSERT INTO student_profiles (username, name, student_id, password, section, email, phone) VALUES (?, ?, ?, ?, ?, ?, ?)", students)
    print(f"  Inserted {len(students)} students into student_profiles")
    
    # Insert professors into professor_profiles
    professors = [
        ('professor', 'Default Professor', 'professor123', 'professor@example.com', '123-456-7893'),
        ('teacher1', 'Robert Brown', 'password123', 'robert@example.com', '123-456-7894')
    ]
    cursor.executemany("INSERT INTO professor_profiles (username, name, password, email, phone) VALUES (?, ?, ?, ?, ?)", professors)
    print(f"  Inserted {len(professors)} professors into professor_profiles")
    
    # Check subjects table schema before inserting
    cursor.execute("PRAGMA table_info(subjects)")
    subjects_columns = {info[1]:info[0] for info in cursor.fetchall()}
    print(f"  Detected subjects columns: {list(subjects_columns.keys())}")
    
    # Determine correct column name for the subject field
    subject_column = 'subject' if 'subject' in subjects_columns else 'name'
    
    # Insert subjects using the correct column name
    subjects = [
        ('Mathematics', 'Advanced Mathematics'),
        ('Physics', 'General Physics'),
        ('Computer Science', 'Introduction to Programming'),
        ('English', 'Advanced English'),
        ('History', 'World History')
    ]
    cursor.executemany(f"INSERT INTO subjects ({subject_column}, description) VALUES (?, ?)", subjects)
    print(f"  Inserted {len(subjects)} subjects into subjects table using column '{subject_column}'")
    
    # For class schedules, use the correct subject column reference
    days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    class_schedules = []
    
    for subject_name, _ in subjects:
        # Randomly assign days for each subject
        day = random.choice(days_of_week)
        start_hour = random.randint(8, 14)  
        start_time = f"{start_hour}:00 AM" if start_hour < 12 else f"{start_hour-12}:00 PM" if start_hour > 12 else "12:00 PM"
        end_hour = start_hour + 2
        end_time = f"{end_hour}:00 AM" if end_hour < 12 else f"{end_hour-12}:00 PM" if end_hour > 12 else "12:00 PM"
        
        class_type = random.choice(['lec', 'sec'])
        room = f"Room {random.randint(100, 500)}"
        
        class_schedules.append((subject_name, day, start_time, end_time, class_type, room))
    
    cursor.executemany("INSERT INTO class_schedules (subject, day, start_time, end_time, type, room) VALUES (?, ?, ?, ?, ?, ?)", class_schedules)
    print(f"  Inserted {len(class_schedules)} schedules into class_schedules")
    
    # Insert attendance records for the past week
    today = datetime.now().date()
    
    # Generate attendance for each student for past 7 days
    attendance_records = []
    class_attendance_records = []
    
    for day in range(7):
        date = today - timedelta(days=day)
        date_str = date.strftime('%Y-%m-%d')
        day_name = date.strftime('%A')
        
        # Find classes on this day
        cursor.execute("SELECT subject, start_time, end_time, type FROM class_schedules WHERE day = ?", (day_name,))
        day_classes = cursor.fetchall()
        
        # For each class, record attendance for each student
        for subject, start_time, end_time, class_type in day_classes:
            # Find subject_id
            cursor.execute("SELECT id FROM subjects WHERE name = ?", (subject,))
            subject_id = cursor.fetchone()[0]
            
            # For each student
            for student_username, student_name, student_id, _, _, _, _ in students:
                # Randomly determine if student attended (80% chance)
                attended = random.random() < 0.8
                
                if attended:
                    # Generate a timestamp within class hours
                    try:
                        # Parse start_time to determine timestamp
                        if "AM" in start_time or "PM" in start_time:
                            # 12-hour format
                            start_parts = start_time.replace(" AM", "").replace(" PM", "").split(":")
                            start_hour = int(start_parts[0])
                            if "PM" in start_time and start_hour < 12:
                                start_hour += 12
                            elif "AM" in start_time and start_hour == 12:
                                start_hour = 0
                        else:
                            # 24-hour format
                            start_parts = start_time.split(":")
                            start_hour = int(start_parts[0])
                        
                        # Random minute in the class
                        minute = random.randint(5, 55)
                        
                        # Create timestamp
                        attendance_time = datetime.combine(date, datetime.min.time().replace(hour=start_hour, minute=minute))
                        timestamp = attendance_time.strftime('%Y-%m-%d %H:%M:%S')
                        
                        # Add to attendance_records
                        attendance_records.append((student_username, student_name, subject_id, timestamp, "present", date_str))
                    except Exception as e:
                        print(f"Error generating timestamp for {start_time}: {e}")
                
                # Add to class_attendance for all students (marked as attended or not)
                class_attendance_records.append((student_name, date_str, subject, start_time, end_time, 1 if attended else 0))
    
    # Insert attendance records
    cursor.executemany("INSERT INTO attendance_records (student_username, name, subject_id, timestamp, status, class_date) VALUES (?, ?, ?, ?, ?, ?)", attendance_records)
    print(f"  Inserted {len(attendance_records)} records into attendance_records")
    
    # Insert class attendance records with unique constraint
    try:
        cursor.executemany("INSERT OR IGNORE INTO class_attendance (student_name, class_date, subject, start_time, end_time, attended) VALUES (?, ?, ?, ?, ?, ?)", class_attendance_records)
        print(f"  Inserted {cursor.rowcount} records into class_attendance")
    except sqlite3.IntegrityError as e:
        print(f"  Error inserting class_attendance records: {e}")
    
    # Insert some login logs
    login_logs = []
    for username, _, _ in users:
        for day in range(5):
            timestamp = (datetime.now() - timedelta(days=day)).strftime('%Y-%m-%d %H:%M:%S')
            status = "success" if random.random() < 0.9 else "failed"
            login_logs.append((username, timestamp, "127.0.0.1", status))
    
    cursor.executemany("INSERT INTO login_logs (username, login_time, ip_address, status) VALUES (?, ?, ?, ?)", login_logs)
    print(f"  Inserted {len(login_logs)} records into login_logs")
    
    print("All sample data inserted successfully.")

def verify_data(cursor):
    """Verify data was inserted correctly"""
    print("\nVerifying inserted data...")
    
    tables = [
        "user_accounts", 
        "student_profiles", 
        "professor_profiles", 
        "subjects", 
        "class_schedules", 
        "attendance_records", 
        "class_attendance", 
        "login_logs"
    ]
    
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  {table}: {count} records")
        except Exception as e:
            print(f"  Error checking {table}: {e}")
    
    print("Data verification complete.")

def main():
    print("\n=== Database Rebuild and Sample Data Generation ===\n")
    
    # Check if database already exists
    db_exists = os.path.exists(DB_PATH)
    if db_exists:
        print(f"Database already exists at: {os.path.abspath(DB_PATH)}")
    else:
        print(f"Creating new database at: {os.path.abspath(DB_PATH)}")
    
    # Connect to the database
    conn = connect_db()
    cursor = conn.cursor()
    
    # Drop tables if they exist
    if not drop_tables(cursor):
        conn.close()
        return
    
    # Create tables
    create_tables(cursor)
    
    # Insert sample data
    insert_sample_data(cursor)
    
    # Verify data
    verify_data(cursor)
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    print("\nDatabase rebuild completed successfully!")
    print(f"Database location: {os.path.abspath(DB_PATH)}")

if __name__ == "__main__":
    main()
