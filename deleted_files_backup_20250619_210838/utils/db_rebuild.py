
import sqlite3
import pandas as pd
import os
import streamlit as st
from datetime import datetime

# Constants
DATABASE_PATH = 'attendance_system.db'
BACKUP_DIR = 'database_backups'

def create_backup():
    """Create a backup of the current database"""
    # Ensure backup directory exists
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    
    # Create timestamped backup file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(BACKUP_DIR, f'attendance_system_{timestamp}.db')
    
    # Copy current database to backup
    try:
        # Make sure the source exists
        if not os.path.exists(DATABASE_PATH):
            return False, "No database file found to back up"
            
        # Create backup using SQLite's backup API
        src_conn = sqlite3.connect(DATABASE_PATH)
        dst_conn = sqlite3.connect(backup_path)
        src_conn.backup(dst_conn)
        src_conn.close()
        dst_conn.close()
        
        return True, backup_path
    except Exception as e:
        return False, str(e)

def extract_data():
    """Extract all important data from the existing database"""
    conn = sqlite3.connect(DATABASE_PATH)
    data = {}
    
    try:
        # Check which tables exist
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [table[0] for table in cursor.fetchall()]
        
        # Extract users (from multiple possible sources)
        # Users might be in user_accounts, student_profiles, professor_profiles
        users = []
        
        if 'user_accounts' in tables:
            df = pd.read_sql("SELECT * FROM user_accounts", conn)
            users.append(df)
        
        if 'student_profiles' in tables:
            df = pd.read_sql("SELECT * FROM student_profiles", conn)
            # Add role column
            df['role'] = 'student'
            users.append(df)
            
        if 'professor_profiles' in tables:
            df = pd.read_sql("SELECT * FROM professor_profiles", conn)
            # Add role column
            df['role'] = 'professor'
            users.append(df)
            
        if users:
            data['users'] = users
            
        # Extract subjects
        if 'subjects' in tables:
            data['subjects'] = pd.read_sql("SELECT * FROM subjects", conn)
            
        # Extract schedules
        if 'class_schedules' in tables:
            data['schedules'] = pd.read_sql("SELECT * FROM class_schedules", conn)
            
        # Extract teacher-subject assignments
        teacher_subjects = []
        if 'teacher_subjects' in tables:
            teacher_subjects.append(pd.read_sql("SELECT * FROM teacher_subjects", conn))
            
        if 'professor_subjects' in tables:
            teacher_subjects.append(pd.read_sql("SELECT * FROM professor_subjects", conn))
            
        if teacher_subjects:
            data['teacher_subjects'] = teacher_subjects
            
        # Extract attendance records
        attendance_tables = [t for t in tables if 'attend' in t.lower()]
        attendance_data = []
        
        for table in attendance_tables:
            try:
                df = pd.read_sql(f"SELECT * FROM {table}", conn)
                if not df.empty:
                    attendance_data.append({'table': table, 'data': df})
            except:
                pass
                
        if attendance_data:
            data['attendance'] = attendance_data
            
        # Extract facial recognition data
        facial_tables = [t for t in tables if 'facial' in t.lower() or 'embed' in t.lower()]
        facial_data = []
        
        for table in facial_tables:
            try:
                df = pd.read_sql(f"SELECT * FROM {table}", conn)
                if not df.empty:
                    facial_data.append({'table': table, 'data': df})
            except:
                pass
                
        if facial_data:
            data['facial'] = facial_data
            
        return True, data
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def create_optimized_schema():
    """Create a new optimized database schema"""
    # First, drop the existing database file if it exists
    if os.path.exists(DATABASE_PATH):
        os.remove(DATABASE_PATH)
        
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # Enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Create user_accounts table - unified table for all users
        cursor.execute('''
        CREATE TABLE user_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            name TEXT,
            email TEXT,
            department TEXT,           -- For professors
            section TEXT,              -- For students
            student_id TEXT,           -- For students
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create subjects table
        cursor.execute('''
        CREATE TABLE subjects (
            subject_id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_name TEXT NOT NULL UNIQUE,
            course_code TEXT,
            credit_hours INTEGER DEFAULT 3,
            description TEXT
        )
        ''')
        
        # Create teacher_subjects table (many-to-many relationship)
        cursor.execute('''
        CREATE TABLE teacher_subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_username TEXT NOT NULL,
            subject_id INTEGER NOT NULL,
            FOREIGN KEY (teacher_username) REFERENCES user_accounts(username),
            FOREIGN KEY (subject_id) REFERENCES subjects(subject_id),
            UNIQUE(teacher_username, subject_id)
        )
        ''')
        
        # Create class_schedules table
        cursor.execute('''
        CREATE TABLE class_schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER NOT NULL,
            subject TEXT NOT NULL,       -- Denormalized for convenience
            day TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            room TEXT,
            type TEXT DEFAULT 'lec',
            FOREIGN KEY (subject_id) REFERENCES subjects(subject_id)
        )
        ''')
        
        # Create attendance_records table
        cursor.execute('''
        CREATE TABLE attendance_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_username TEXT NOT NULL,
            subject_id INTEGER NOT NULL,
            class_date TEXT NOT NULL,
            status TEXT DEFAULT 'present',
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_username) REFERENCES user_accounts(username),
            FOREIGN KEY (subject_id) REFERENCES subjects(subject_id)
        )
        ''')
        
        # Create facial_recognition_data table
        cursor.execute('''
        CREATE TABLE facial_recognition_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            facial_features TEXT NOT NULL,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (username) REFERENCES user_accounts(username)
        )
        ''')
        
        # Create indexes for better performance
        cursor.execute("CREATE INDEX idx_user_role ON user_accounts(role)")
        cursor.execute("CREATE INDEX idx_user_username ON user_accounts(username)")
        cursor.execute("CREATE INDEX idx_teachersubj_teacher ON teacher_subjects(teacher_username)")
        cursor.execute("CREATE INDEX idx_teachersubj_subject ON teacher_subjects(subject_id)")
        cursor.execute("CREATE INDEX idx_schedules_subject ON class_schedules(subject_id)")
        cursor.execute("CREATE INDEX idx_attendance_student ON attendance_records(student_username)")
        cursor.execute("CREATE INDEX idx_attendance_subject ON attendance_records(subject_id)")
        cursor.execute("CREATE INDEX idx_attendance_date ON attendance_records(class_date)")
        
        conn.commit()
        return True, "Schema created successfully"
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

def migrate_data(data):
    """Migrate extracted data to the new schema"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    results = {
        'users': {'success': 0, 'failed': 0},
        'subjects': {'success': 0, 'failed': 0},
        'schedules': {'success': 0, 'failed': 0},
        'teacher_subjects': {'success': 0, 'failed': 0},
        'attendance': {'success': 0, 'failed': 0},
        'facial': {'success': 0, 'failed': 0}
    }
    
    try:
        # Migrate users
        if 'users' in data:
            for user_df_list in data['users']:
                for _, user in user_df_list.iterrows():
                    try:
                        # Map fields from various possible schemas
                        username = user.get('username', user.get('name', ''))
                        password = user.get('password', 'password123')  # Default if not found
                        role = user.get('role', 'student')
                        name = user.get('name', user.get('full_name', username))
                        email = user.get('email', '')
                        department = user.get('department', '')
                        section = user.get('section', '')
                        student_id = user.get('student_id', '')
                        
                        cursor.execute('''
                        INSERT OR IGNORE INTO user_accounts 
                        (username, password, role, name, email, department, section, student_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (username, password, role, name, email, department, section, student_id))
                        
                        if cursor.rowcount > 0:
                            results['users']['success'] += 1
                        else:
                            # Already exists, update instead
                            cursor.execute('''
                            UPDATE user_accounts SET
                            password = ?,
                            role = ?,
                            name = ?,
                            email = ?,
                            department = ?,
                            section = ?,
                            student_id = ?
                            WHERE username = ? AND (name IS NULL OR password IS NULL OR role IS NULL)
                            ''', (password, role, name, email, department, section, student_id, username))
                            results['users']['success'] += cursor.rowcount
                    except Exception as e:
                        print(f"Error migrating user {username}: {e}")
                        results['users']['failed'] += 1
        
        # Migrate subjects
        if 'subjects' in data:
            for _, subject in data['subjects'].iterrows():
                try:
                    # Map subject fields
                    subject_id = subject.get('subject_id', None)
                    subject_name = subject.get('subject_name', '')
                    course_code = subject.get('course_code', '')
                    credit_hours = subject.get('credit_hours', 3)
                    description = subject.get('description', '')
                    
                    if subject_id is not None:
                        cursor.execute('''
                        INSERT OR IGNORE INTO subjects 
                        (subject_id, subject_name, course_code, credit_hours, description)
                        VALUES (?, ?, ?, ?, ?)
                        ''', (subject_id, subject_name, course_code, credit_hours, description))
                    else:
                        cursor.execute('''
                        INSERT OR IGNORE INTO subjects 
                        (subject_name, course_code, credit_hours, description)
                        VALUES (?, ?, ?, ?)
                        ''', (subject_name, course_code, credit_hours, description))
                    
                    if cursor.rowcount > 0:
                        results['subjects']['success'] += 1
                    else:
                        results['subjects']['failed'] += 1
                except Exception as e:
                    print(f"Error migrating subject {subject_name}: {e}")
                    results['subjects']['failed'] += 1
        
        # Migrate schedules
        if 'schedules' in data:
            for _, schedule in data['schedules'].iterrows():
                try:
                    # Map schedule fields
                    subject_id = schedule.get('subject_id', None)
                    subject_name = schedule.get('subject', schedule.get('subject_name', ''))
                    
                    # If we only have subject name but not ID, look up the ID
                    if subject_id is None and subject_name:
                        cursor.execute('SELECT subject_id FROM subjects WHERE subject_name = ?', (subject_name,))
                        result = cursor.fetchone()
                        if result:
                            subject_id = result[0]
                    
                    if subject_id is not None:
                        day = schedule.get('day', '')
                        start_time = schedule.get('start_time', '')
                        end_time = schedule.get('end_time', '')
                        room = schedule.get('room', '')
                        class_type = schedule.get('type', 'lec')
                        
                        cursor.execute('''
                        INSERT INTO class_schedules 
                        (subject_id, subject, day, start_time, end_time, room, type)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (subject_id, subject_name, day, start_time, end_time, room, class_type))
                        
                        results['schedules']['success'] += 1
                    else:
                        results['schedules']['failed'] += 1
                except Exception as e:
                    print(f"Error migrating schedule: {e}")
                    results['schedules']['failed'] += 1
        
        # Migrate teacher-subject assignments
        if 'teacher_subjects' in data:
            for ts_df_list in data['teacher_subjects']:
                for _, assignment in ts_df_list.iterrows():
                    try:
                        # Map fields from different possible schemas
                        subject_id = assignment.get('subject_id', None)
                        
                        # Get teacher username from various possible field names
                        teacher_username = assignment.get('teacher_username', 
                                      assignment.get('teacher_name',
                                      assignment.get('username',
                                      assignment.get('professor_username', ''))))
                        
                        if subject_id is not None and teacher_username:
                            cursor.execute('''
                            INSERT OR IGNORE INTO teacher_subjects 
                            (teacher_username, subject_id)
                            VALUES (?, ?)
                            ''', (teacher_username, subject_id))
                            
                            if cursor.rowcount > 0:
                                results['teacher_subjects']['success'] += 1
                            else:
                                results['teacher_subjects']['failed'] += 1
                    except Exception as e:
                        print(f"Error migrating teacher-subject assignment: {e}")
                        results['teacher_subjects']['failed'] += 1
        
        # Migrate attendance records
        if 'attendance' in data:
            for attendance_item in data['attendance']:
                for _, record in attendance_item['data'].iterrows():
                    try:
                        # Map attendance fields - these will vary by table schema
                        student_username = record.get('student_name', 
                                           record.get('student_username',
                                           record.get('name', 
                                           record.get('username', ''))))
                        
                        subject_name = record.get('subject', '')
                        subject_id = record.get('subject_id', None)
                        
                        # Look up subject ID if needed
                        if subject_id is None and subject_name:
                            cursor.execute('SELECT subject_id FROM subjects WHERE subject_name = ?', (subject_name,))
                            result = cursor.fetchone()
                            if result:
                                subject_id = result[0]
                        
                        # Only proceed if we have both student and subject
                        if student_username and subject_id:
                            class_date = record.get('date', 
                                         record.get('class_date',
                                         record.get('timestamp', 
                                         datetime.now().strftime('%Y-%m-%d'))))
                            
                            # Extract just the date part if it has time
                            if len(class_date) > 10:
                                try:
                                    parsed_date = datetime.fromisoformat(class_date.replace('Z', '+00:00'))
                                    class_date = parsed_date.strftime('%Y-%m-%d')
                                except:
                                    pass  # Keep original if parsing fails
                                    
                            status = record.get('status', 
                                      record.get('attended', 
                                      record.get('present', 'present')))
                            
                            # Convert boolean to text if needed
                            if isinstance(status, bool):
                                status = 'present' if status else 'absent'
                                
                            timestamp = record.get('timestamp', 
                                        record.get('created_at',
                                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                            
                            cursor.execute('''
                            INSERT INTO attendance_records 
                            (student_username, subject_id, class_date, status, timestamp)
                            VALUES (?, ?, ?, ?, ?)
                            ''', (student_username, subject_id, class_date, status, timestamp))
                            
                            results['attendance']['success'] += 1
                        else:
                            results['attendance']['failed'] += 1
                    except Exception as e:
                        print(f"Error migrating attendance record: {e}")
                        results['attendance']['failed'] += 1
        
        # Migrate facial recognition data
        if 'facial' in data:
            for facial_item in data['facial']:
                for _, record in facial_item['data'].iterrows():
                    try:
                        username = record.get('username', 
                                   record.get('name', 
                                   record.get('student_name', '')))
                        
                        facial_features = record.get('facial_features', 
                                          record.get('embedding', 
                                          record.get('features', '{}')))
                        
                        if username and facial_features:
                            cursor.execute('''
                            INSERT OR IGNORE INTO facial_recognition_data 
                            (username, facial_features)
                            VALUES (?, ?)
                            ''', (username, facial_features))
                            
                            if cursor.rowcount > 0:
                                results['facial']['success'] += 1
                            else:
                                results['facial']['failed'] += 1
                    except Exception as e:
                        print(f"Error migrating facial data: {e}")
                        results['facial']['failed'] += 1
        
        conn.commit()
        return True, results
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

def rebuild_database():
    """Main function to rebuild the database with an optimized schema"""
    # Step 1: Create database backup
    backup_success, backup_result = create_backup()
    
    if not backup_success:
        return False, f"Backup failed: {backup_result}", None
    
    # Step 2: Extract data from current database
    extract_success, extracted_data = extract_data()
    
    if not extract_success:
        return False, f"Data extraction failed: {extracted_data}", None
    
    # Step 3: Create new schema
    schema_success, schema_result = create_optimized_schema()
    
    if not schema_success:
        return False, f"Schema creation failed: {schema_result}", None
    
    # Step 4: Migrate data to new schema
    migrate_success, migrate_result = migrate_data(extracted_data)
    
    if not migrate_success:
        return False, f"Migration failed: {migrate_result}", None
    
    return True, f"Database successfully rebuilt. Backup saved to {backup_result}", migrate_result

def show_rebuild_interface():
    """Streamlit interface for the database rebuild function"""
    st.title("Database Optimization Tool")
    st.write("This tool will rebuild your database with a streamlined schema, preserving all your data.")
    
    st.warning("""
    ⚠️ **CAUTION**:
    - This operation will DELETE your current database structure
    - A backup will be created automatically
    - All data will be migrated to the new structure
    - This process cannot be interrupted once started
    """)
    
    # Show database stats before rebuild
    st.subheader("Current Database Structure")
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Get table counts
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = cursor.fetchall()
    
    st.write(f"**Number of tables:** {len(tables)}")
    
    # Get row counts for each table
    table_stats = []
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            table_stats.append({"Table": table[0], "Rows": count})
        except:
            table_stats.append({"Table": table[0], "Rows": "ERROR"})
    
    conn.close()
    
    # Display table stats
    stats_df = pd.DataFrame(table_stats)
    st.dataframe(stats_df)
    
    # Checkbox to confirm understanding
    confirm = st.checkbox("I have backed up my data and understand the risks")
    
    # Execute rebuild button
    if confirm and st.button("Rebuild Database", type="primary"):
        with st.spinner("Rebuilding database... This may take several minutes..."):
            success, message, results = rebuild_database()
        
        if success:
            st.success(message)
            
            # Display migration results
            st.subheader("Migration Results")
            
            for category, stats in results.items():
                if stats['success'] > 0 or stats['failed'] > 0:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric(f"{category.title()}", f"{stats['success']} migrated")
                    with col2:
                        if stats['failed'] > 0:
                            st.metric("Failed", stats['failed'], delta=-stats['failed'], delta_color="inverse")
                    with col3:
                        total = stats['success'] + stats['failed']
                        if total > 0:
                            percentage = (stats['success'] / total) * 100
                            st.metric("Success Rate", f"{percentage:.1f}%")
            
            # Show new database structure
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            new_tables = cursor.fetchall()
            
            st.subheader("New Database Structure")
            st.write(f"**Number of tables:** {len(new_tables)}")
            
            for table in new_tables:
                st.write(f"- {table[0]}")
                
                # Show table structure
                with st.expander(f"Show {table[0]} structure"):
                    cursor.execute(f"PRAGMA table_info({table[0]})")
                    columns = cursor.fetchall()
                    column_info = [{"Column": col[1], "Type": col[2], "Not Null": bool(col[3]), "Primary Key": bool(col[5])} for col in columns]
                    st.dataframe(pd.DataFrame(column_info))
                    
                    # Show row count
                    cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                    count = cursor.fetchone()[0]
                    st.write(f"**Row count:** {count}")
            
            conn.close()
            
            st.info("All application code will now use these tables. No code changes required.")
        else:
            st.error(message)

if __name__ == "__main__":
    show_rebuild_interface()