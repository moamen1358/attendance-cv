import sqlite3
import streamlit as st
import pandas as pd

# Constants
DATABASE_PATH = 'attendance_system.db'

# Add import for database sync - using direct import
from database_sync import sync_user_tables

# Import centralized database initialization
try:
    from db_init import initialize_database, check_database_integrity
except ImportError:
    from .db_init import initialize_database, check_database_integrity

# Initialize database tables on import
initialize_database()

def get_db_connection():
    """Get a connection to the database"""
    return sqlite3.connect(DATABASE_PATH)

def get_table_names():
    """Get all table names in the database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tables

def fix_query_tables(query):
    """
    Fix table names in SQL queries to match what exists in the database
    Handles common mapping issues like class_attendance_records → class_attendance
    """
    tables = get_table_names()
    
    # Define mappings for incorrect table names to correct ones
    common_mappings = {
        'class_attendance_records': 'class_attendance',
        'attendance_log': 'attendance_records',
        'students': 'student_profiles',
        'professors': 'user_accounts',
        'user_accounts': 'user_accounts'  # This one is correct, included for completeness
    }
    
    # For each mapping, check if the table exists and replace if needed
    for wrong_name, correct_name in common_mappings.items():
        if wrong_name in query and wrong_name not in tables and correct_name in tables:
            # Replace all occurrences in the query, preserving case and whitespace
            query = query.replace(f" {wrong_name} ", f" {correct_name} ")
            query = query.replace(f" {wrong_name}\n", f" {correct_name}\n")
            query = query.replace(f" {wrong_name},", f" {correct_name},")
            query = query.replace(f"({wrong_name})", f"({correct_name})")
            query = query.replace(f"({wrong_name} ", f"({correct_name} ")
            
            # Handle beginning and end of query
            if query.startswith(f"{wrong_name} "):
                query = f"{correct_name} " + query[len(wrong_name)+1:]
            if query.endswith(f" {wrong_name}"):
                query = query[:-len(wrong_name)-1] + f" {correct_name}"
    
    return query

def execute_query(query, params=None):
    """
    Execute a query with table name auto-correction
    
    Args:
        query (str): SQL query string
        params (tuple, optional): Parameters for the query
    
    Returns:
        list: List of rows returned by the query
    """
    # Fix table names in the query
    fixed_query = fix_query_tables(query)
    
    # If the query was modified, show info message
    if fixed_query != query:
        print(f"Query modified for compatibility: {fixed_query}")
    
    # Execute the query
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if params:
            cursor.execute(fixed_query, params)
        else:
            cursor.execute(fixed_query)
        
        results = cursor.fetchall()
        return cursor  # Return cursor instead of results for flexibility
    except Exception as e:
        conn.close()
        raise e

def ensure_subjects_table_compatibility():
    """Ensure the subjects table has consistent column naming"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # DISABLED: Legacy table creation - using enhanced tables only
        # Check if subjects table exists
        # cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='subjects'")
        # if not cursor.fetchone():
        #     # Create the subjects table if it doesn't exist
        #     cursor.execute('''
        #     CREATE TABLE subjects (
        #         id INTEGER PRIMARY KEY AUTOINCREMENT,
        #         name TEXT NOT NULL,
        #         course_code TEXT,
        #         credit_hours INTEGER DEFAULT 3,
        #         description TEXT
        #     )
        #     ''')
        #     conn.commit()
        #     print("Created subjects table with standard schema")
        #     return True
        
        print("DISABLED: Legacy table operations - using enhanced tables only")
        return False
            
        # DISABLED: Legacy schema checks
        # Check current schema
        # cursor.execute("PRAGMA table_info(subjects)")
        # columns = {col[1].lower(): col[1] for col in cursor.fetchall()}
        
        # Check if both id and subject_id exist
        # has_id = 'id' in columns
        # has_subject_id = 'subject_id' in columns
        
        # Check if both name and subject_name exist
        has_name = 'name' in columns
        has_subject_name = 'subject_name' in columns
        
        # If we only have 'id' but not 'subject_id', add subject_id as alias
        if has_id and not has_subject_id:
            try:
                # Create a view that maps id to subject_id
                cursor.execute('''
                CREATE VIEW IF NOT EXISTS subjects_compatible AS 
                SELECT 
                    id as subject_id,
                    * 
                FROM subjects
                ''')
                conn.commit()
                print("Created compatibility view for subjects table: mapping id -> subject_id")
            except Exception as e:
                print(f"Error creating view: {e}")
                
        # If we only have 'name' but not 'subject_name', add subject_name as alias
        if has_name and not has_subject_name:
            try:
                # Update view to include name -> subject_name mapping
                cursor.execute('''
                DROP VIEW IF EXISTS subjects_compatible
                ''')
                cursor.execute('''
                CREATE VIEW subjects_compatible AS 
                SELECT 
                    id as subject_id,
                    name as subject_name,
                    * 
                FROM subjects
                ''')
                conn.commit()
                print("Updated compatibility view for subjects table: mapping name -> subject_name")
            except Exception as e:
                print(f"Error updating view: {e}")
        
        return True
    except Exception as e:
        print(f"Error ensuring subjects table compatibility: {e}")
        return False
    finally:
        conn.close()

def ensure_professor_assignments_table():
    """DISABLED: Legacy table creation - using enhanced tables only"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # DISABLED: Legacy table operations
        # First ensure subjects table has compatible column naming
        # ensure_subjects_table_compatibility()
        
        # cursor.execute("""
        # CREATE TABLE IF NOT EXISTS professor_subject_assignments (
        #     id INTEGER PRIMARY KEY AUTOINCREMENT,
        #     professor_username TEXT NOT NULL,
        #     subject_id INTEGER NOT NULL,
        #     assigned_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        #     UNIQUE(professor_username, subject_id)
        # )
        # """)
        
        # DISABLED: Legacy view creation
        # Create a compatibility view for the assignments table
        # cursor.execute("""
        # CREATE VIEW IF NOT EXISTS professor_assignments_view AS
        # SELECT 
        #     psa.id, 
        #     psa.professor_username, 
        #     psa.subject_id,
        #     s.name AS subject_name, 
        #     psa.assigned_date
        # FROM professor_subject_assignments psa
        # LEFT JOIN subjects s ON psa.subject_id = s.id
        # """)
        
        # conn.commit()
        print("DISABLED: Legacy table/view creation - using enhanced tables only")
        return False
    except Exception as e:
        print(f"Error in legacy table operations (disabled): {e}")
        return False
    finally:
        conn.close()

def execute_query_df(query, params=None):
    """
    Execute a SQL query and return the result as a pandas DataFrame.
    """
    # Ensure compatibility tables/views exist if needed
    if 'professor_subject_assignments' in query:
        ensure_professor_assignments_table()
    
    # Check if query involves subjects table and modify if needed
    if 'subjects s' in query and 's.subject_id' in query:
        # Replace references to s.subject_id with s.id if using the subjects table
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        try:
            # Check if subject_id column exists
            cursor.execute("PRAGMA table_info(subjects)")
            columns = [col[1] for col in cursor.fetchall()]
            
            # If no subject_id column but id exists, modify the query
            if 'id' in columns and 'subject_id' not in columns:
                query = query.replace('s.subject_id', 's.id')
        except Exception as e:
            print(f"Error checking subjects schema: {e}")
        finally:
            conn.close()
    
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        fixed_query = query.strip()
        print(f"[DEBUG] Executing query: {fixed_query}")
        print(f"[DEBUG] With params: {params}")
        df = pd.read_sql_query(fixed_query, conn, params=params)
        print(f"[DEBUG] Query result: {len(df)} rows, columns: {df.columns.tolist()}")
        return df
    except Exception as e:
        print(f"[ERROR] executing query: {e}")
        print(f"[ERROR] Query was: {query}")
        print(f"[ERROR] Params were: {params}")
        # Don't suppress the error - let it be visible
        import traceback
        traceback.print_exc()
        # Return empty DataFrame with same column structure if possible
        return pd.DataFrame()
    finally:
        conn.close()

def get_professors_list():
    """Get list of professors with proper synchronization"""
    # First sync tables to ensure consistency
    sync_user_tables()
    
    conn = sqlite3.connect('attendance_system.db')
    query = """
    SELECT username, COALESCE(name, username) as name
    FROM user_accounts_enhanced ua
    LEFT JOIN professor_profiles pp ON ua.username = pp.username
    WHERE ua.role = 'professor'
    ORDER BY name
    """
    
    try:
        df = pd.read_sql(query, conn)
    except:
        # Fallback query if join fails
        query = "SELECT username, username as name FROM user_accounts_enhanced WHERE role = 'professor'"
        df = pd.read_sql(query, conn)
    finally:
        conn.close()
    
    return df

def get_students_list():
    """Get list of students with proper synchronization"""
    # First sync tables to ensure consistency
    sync_user_tables()
    
    conn = sqlite3.connect('attendance_system.db')
    query = """
    SELECT username, COALESCE(name, username) as name, section
    FROM user_accounts_enhanced ua
    LEFT JOIN student_profiles_enhanced sp ON ua.username = sp.username
    WHERE ua.role = 'student'
    ORDER BY name
    """
    
    try:
        df = pd.read_sql(query, conn)
    except:
        # Fallback query if join fails
        query = "SELECT username, username as name, '' as section FROM user_accounts_enhanced WHERE role = 'student'"
        df = pd.read_sql(query, conn)
    finally:
        conn.close()
    
    return df

def get_subjects_list(with_id=True):
    """
    Get a list of subjects with schema detection for different column names
    
    Args:
        with_id (bool): If True, include ID column in results
    
    Returns:
        DataFrame with subject information
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if subjects table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='subjects'")
        if not cursor.fetchone():
            print("Subjects table does not exist")
            return pd.DataFrame()
        
        # Get schema information
        cursor.execute("PRAGMA table_info(subjects)")
        columns = {col[1]: col[0] for col in cursor.fetchall()}
        
        # Determine column names to use
        id_col = 'subject_id' if 'subject_id' in columns else 'id' if 'id' in columns else None
        name_col = 'subject_name' if 'subject_name' in columns else 'name' if 'name' in columns else None
        
        if not name_col:
            print("Could not find name column in subjects table")
            return pd.DataFrame()
        
        # Create query based on available columns
        if with_id and id_col:
            query = f"SELECT {id_col} AS subject_id, {name_col} AS subject_name FROM subjects ORDER BY {name_col}"
        else:
            query = f"SELECT {name_col} AS subject_name FROM subjects ORDER BY {name_col}"
        
        df = pd.read_sql_query(query, conn)
        print(f"Found {len(df)} subjects")
        return df
    
    except Exception as e:
        print(f"Error getting subjects list: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def sync_teacher_subject_assignments():
    """Sync professor/teacher subject assignments across tables"""
    conn = sqlite3.connect('attendance_system.db')
    cursor = conn.cursor()
    
    try:
        # DISABLED: Legacy table creation - using enhanced tables only
        # Make sure tables exist
        # cursor.execute("""
        # CREATE TABLE IF NOT EXISTS professor_subject_assignments (
        #     id INTEGER PRIMARY KEY AUTOINCREMENT,
        #     professor_username TEXT NOT NULL,
        #     subject_id INTEGER NOT NULL,
        #     assigned_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        #     UNIQUE(professor_username, subject_id)
        # )
        # """)
        
        # cursor.execute("""
        # CREATE TABLE IF NOT EXISTS teacher_subjects (
        #     id INTEGER PRIMARY KEY AUTOINCREMENT,
        #     subject_id INTEGER,
        #     teacher_name TEXT,
        #     UNIQUE(subject_id, teacher_name)
        # )
        # """)
        
        # DISABLED: Legacy synchronization
        # Sync from teacher_subjects to professor_subject_assignments
        # cursor.execute("""
        # INSERT OR IGNORE INTO professor_subject_assignments (professor_username, subject_id)
        # SELECT teacher_name, subject_id FROM teacher_subjects
        # """)
        
        # Sync from professor_subject_assignments to teacher_subjects
        # cursor.execute("""
        # INSERT OR IGNORE INTO teacher_subjects (teacher_name, subject_id)
        # SELECT professor_username, subject_id FROM professor_subject_assignments
        # """)
        
        # conn.commit()
        print("DISABLED: Legacy table synchronization - using enhanced tables only")
    except Exception as e:
        print(f"Error in legacy operations (disabled): {e}")
        # conn.rollback()
    finally:
        conn.close()

def get_teacher_subjects(username):
    """
    Get a list of subjects assigned to a teacher with improved schema detection.
    
    Args:
        username (str): Username of the teacher
        
    Returns:
        list: List of subject names assigned to the teacher
    """
    if not username:
        return []
        
    # First sync assignments between tables
    sync_teacher_subject_assignments()
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    subjects = []
    
    try:
        # Check subjects table schema to understand column names
        cursor.execute("PRAGMA table_info(subjects)")
        subject_columns = {col[1].lower(): col[1] for col in cursor.fetchall()}
        
        # Determine which column names to use
        id_col = subject_columns.get('subject_id', subject_columns.get('id', 'id'))
        name_col = subject_columns.get('subject_name', subject_columns.get('name', 'name'))
        
        # First try professor_subject_assignments table
        cursor.execute(f"""
            SELECT s.{name_col}
            FROM subjects s
            JOIN professor_subject_assignments psa ON s.{id_col} = psa.subject_id
            WHERE psa.professor_username = ?
            ORDER BY s.{name_col}
        """, (username,))
        subjects = [row[0] for row in cursor.fetchall()]
        
        # If no subjects found, try teacher_subjects table
        if not subjects:
            cursor.execute(f"""
                SELECT s.{name_col}
                FROM subjects s
                JOIN teacher_subjects ts ON s.{id_col} = ts.subject_id
                WHERE ts.teacher_name = ?
                ORDER BY s.{name_col}
            """, (username,))
            subjects = [row[0] for row in cursor.fetchall()]
        
        print(f"Found {len(subjects)} subjects for teacher {username}")
    except Exception as e:
        print(f"Error retrieving teacher subjects: {e}")
    finally:
        conn.close()
    
    return subjects

def ensure_subjects_table_schema():
    """Ensure the subjects table has all necessary columns"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if subjects table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='subjects'")
        if not cursor.fetchone():
            # Create the subjects table if it doesn't exist
            cursor.execute('''
            # CREATE TABLE subjects (
            #     id INTEGER PRIMARY KEY AUTOINCREMENT,
            #     name TEXT NOT NULL,
            #     course_code TEXT,
            #     credit_hours INTEGER DEFAULT 3,
            #     description TEXT
            # )
            # ''')
            conn.commit()
            print("Created subjects table with standard schema")
            return True
        
        # Check current columns
        cursor.execute("PRAGMA table_info(subjects)")
        columns = {col[1].lower(): True for col in cursor.fetchall()}
        
        # Add missing columns if needed
        if 'course_code' not in columns:
            cursor.execute("ALTER TABLE subjects ADD COLUMN course_code TEXT")
            print("Added missing course_code column")
            
        if 'credit_hours' not in columns:
            cursor.execute("ALTER TABLE subjects ADD COLUMN credit_hours INTEGER DEFAULT 3")
            print("Added missing credit_hours column")
            
        if 'description' not in columns:
            cursor.execute("ALTER TABLE subjects ADD COLUMN description TEXT")
            print("Added missing description column")
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error ensuring subjects table schema: {e}")
        return False
    finally:
        conn.close()

def ensure_student_profiles_compatibility():
    """
    Ensure student profiles table is accessible regardless of naming convention.
    It handles cases where the table might be named 'students', 'student_profiles', or other variations.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        print("Starting ensure_student_profiles_compatibility() function - ULTRA-aggressive version")
        
        # ULTRA FORCE CREATE:
        # First check if ANY student table exists in the database
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND (name='student_profiles_enhanced' OR name='students')")
        existing_table = cursor.fetchone()
        
        if existing_table:
            # A student table exists, create views to it
            source_table = existing_table[0]
            print(f"Found existing student table: {source_table}")
            
            # Always create view to the source table
            if source_table != 'student_profiles':
                cursor.execute("DROP VIEW IF EXISTS student_profiles")
                cursor.execute(f"CREATE VIEW student_profiles AS SELECT * FROM {source_table}")
                conn.commit()
                print(f"Created student_profiles view pointing to {source_table}")
        else:
            # DISABLED: Legacy table creation - using enhanced tables only
            # No student table exists at all, create it directly
            # cursor.execute("""
            # CREATE TABLE student_profiles (
            #     id INTEGER PRIMARY KEY AUTOINCREMENT,
            #     username TEXT UNIQUE,
            #     name TEXT,
            #     student_id TEXT,
            #     section TEXT,
            #     email TEXT,
            #     phone TEXT,
            #     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            # )
            # """)
            # conn.commit()
            print("DISABLED: Legacy table creation - using enhanced tables only")
            
            # Add a default user record
            try:
                import streamlit as st
                username = st.session_state.get('username', 'default_user')
                cursor.execute("""
                INSERT OR IGNORE INTO student_profiles (username, name, student_id, section) VALUES (?, ?, ?, ?)
                """, (username, username, username, 'Default'))
                conn.commit()
                print(f"Added current user {username} to student_profiles")
            except Exception as e:
                # Fallback to hardcoded default user
                cursor.execute("""
                INSERT OR IGNORE INTO student_profiles (username, name, student_id, section) VALUES (?, ?, ?, ?)
                """, ('default_user', 'Default User', 'S12345', 'Default'))
                conn.commit()
                print("Added default user to student_profiles")
        
        # Always create the view for maximum compatibility
        cursor.execute("DROP VIEW IF EXISTS student_profiles_view")
        cursor.execute("CREATE VIEW student_profiles_view AS SELECT * FROM student_profiles_enhanced")
        conn.commit()
        print("Created student_profiles_view")
            
        # Verify table exists after all operations
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='student_profiles'")
        if cursor.fetchone():
            print("SUCCESS: student_profiles table exists!")
            return True
        else:
            # DISABLED: Legacy table creation - using enhanced tables only
            # One last attempt - create the table directly
            # cursor.execute("""
            # CREATE TABLE student_profiles (
            #     id INTEGER PRIMARY KEY,
            #     username TEXT,
            #     name TEXT,
            #     student_id TEXT,
            #     section TEXT
            # )
            # """)
            # cursor.execute("INSERT INTO student_profiles (username, name) VALUES ('emergency', 'Emergency User')")
            # conn.commit()
            print("DISABLED: Legacy table creation - using enhanced tables only")
            return False
                
    except Exception as e:
        print(f"Critical error in student profiles compatibility: {e}")
        return False
    finally:
        conn.close()

def get_attendance_records_schema():
    """
    Get the actual column names in the attendance_records table
    to handle different naming conventions.
    
    Returns:
        dict: Mapping of standard column names to actual column names
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # Check which tables exist - try all known attendance table names
        tables_to_check = ['attendance_records', 'attendance_log', 'attendance', 'student_attendance']
        table_name = None
        
        for check_table in tables_to_check:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{check_table}'")
            if cursor.fetchone():
                table_name = check_table
                print(f"Found attendance table: {table_name}")
                break
        
        if not table_name:
            # LEGACY: No attendance table found, create it with standard schema (DISABLED)
            print("LEGACY: No attendance records table found - using centralized initialization")
            # cursor.execute("""
            # CREATE TABLE attendance_records (
            #     id INTEGER PRIMARY KEY AUTOINCREMENT,
            #     username TEXT NOT NULL,  -- Changed primary column to username
            #     name TEXT,               -- Keep name as secondary column 
            #     student_name TEXT,       -- Keep student_name for compatibility
            #     timestamp TIMESTAMP NOT NULL,
            #     confidence REAL DEFAULT 1.0,
            #     device_id TEXT,
            #     day_of_week TEXT
            # )
            # """)
            conn.commit()
            table_name = 'attendance_records'
        
        # Get column info
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [col[1].lower() for col in cursor.fetchall()]
        print(f"Found columns in {table_name}: {columns}")
        
        # Create mapping for standard column names to actual column names
        mapping = {}
        
        # Map student name column - MODIFIED: prioritize username over other columns
        # First check for username explicitly, then check other name columns
        student_name_options = ['username', 'student_username', 'user', 'student_name', 'name', 'student']
        found_name_col = False
        
        for option in student_name_options:
            if option in columns:
                mapping['student_name'] = option
                found_name_col = True
                print(f"Mapped student_name to '{option}' column")
                break
        
        if not found_name_col:
            # No suitable column found - add username column
            print("No username or name column found in attendance table. Adding columns...")
            try:
                # Add username column as primary
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN username TEXT")
                
                # Also add name columns for compatibility
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN name TEXT")
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN student_name TEXT")
                conn.commit()
                
                # Try to extract name from first text column
                cursor.execute(f"PRAGMA table_info({table_name})")
                all_columns = cursor.fetchall()
                text_columns = [col[1] for col in all_columns 
                               if col[2].upper() in ('TEXT', 'VARCHAR', 'CHAR') 
                               and col[1].lower() not in ('id', 'timestamp', 'device_id')]
                
                if text_columns:
                    first_text_col = text_columns[0]
                    cursor.execute(f"UPDATE {table_name} SET username = {first_text_col}")
                    cursor.execute(f"UPDATE {table_name} SET name = username")
                    cursor.execute(f"UPDATE {table_name} SET student_name = username")
                    conn.commit()
                    print(f"Populated username columns from {first_text_col}")
                else:
                    # Default to 'Unknown User'
                    cursor.execute(f"UPDATE {table_name} SET username = 'Unknown User'")
                    cursor.execute(f"UPDATE {table_name} SET name = username")
                    cursor.execute(f"UPDATE {table_name} SET student_name = username")
                    conn.commit() 
                    print("Set default username values")
                
                # Use username column for mapping
                mapping['student_name'] = 'username'
                
                # Create indexes for the new columns
                cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_username ON {table_name}(username)")
                conn.commit()
                
            except sqlite3.OperationalError as e:
                print(f"Could not add columns: {e}")
                # Create a view with required columns
                try:
                    view_name = f"{table_name}_username_view"
                    cursor.execute(f"DROP VIEW IF EXISTS {view_name}")
                    
                    # Use first non-id column as name source
                    name_col = columns[1] if len(columns) > 1 else columns[0]
                    cursor.execute(f"""
                    CREATE VIEW {view_name} AS
                    SELECT 
                        id,
                        {name_col} AS username,
                        {name_col} AS name,
                        {name_col} AS student_name,
                        *
                    FROM {table_name}
                    """)
                    conn.commit()
                    print(f"Created view {view_name} with username mapping")
                    mapping['student_name'] = 'username'  # The view has the username column
                except Exception as view_error:
                    print(f"Error creating username view: {view_error}")
                    mapping['student_name'] = columns[0]  # Use first column as last resort
        
        # Map timestamp column - check all possible variations
        time_options = ['timestamp', 'date_time', 'datetime', 'time', 'created_at', 'date']
        found_time_col = False
        
        for option in time_options:
            if option in columns:
                mapping['timestamp'] = option
                found_time_col = True
                print(f"Mapped timestamp to '{option}' column")
                break
        
        if not found_time_col:
            print("No timestamp column found. Adding timestamp column...")
            try:
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN timestamp TIMESTAMP")
                cursor.execute(f"UPDATE {table_name} SET timestamp = CURRENT_TIMESTAMP")
                conn.commit()
                mapping['timestamp'] = 'timestamp'
                print(f"Added timestamp column to {table_name}")
            except Exception as e:
                print(f"Error adding timestamp: {e}")
                mapping['timestamp'] = 'timestamp'  # Default fallback
        
        print(f"Final mapping: {mapping}")
        return mapping
        
    except Exception as e:
        print(f"Error getting attendance schema: {e}")
        # Return default mappings if anything fails - MODIFIED to use username
        return {'student_name': 'username', 'timestamp': 'timestamp'}
    finally:
        conn.close()
