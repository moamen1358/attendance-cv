import sqlite3
import streamlit as st
import pandas as pd

# Constants
DATABASE_PATH = 'attendance_system.db'

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
        # Check if subjects table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='subjects'")
        if not cursor.fetchone():
            # Create the subjects table if it doesn't exist
            cursor.execute('''
            CREATE TABLE subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                course_code TEXT,
                credit_hours INTEGER DEFAULT 3,
                description TEXT
            )
            ''')
            conn.commit()
            print("Created subjects table with standard schema")
            return True
            
        # Check current schema
        cursor.execute("PRAGMA table_info(subjects)")
        columns = {col[1].lower(): col[1] for col in cursor.fetchall()}
        
        # Check if both id and subject_id exist
        has_id = 'id' in columns
        has_subject_id = 'subject_id' in columns
        
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
    """Create the professor_subject_assignments table if it doesn't exist"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # First ensure subjects table has compatible column naming
        ensure_subjects_table_compatibility()
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS professor_subject_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            professor_username TEXT NOT NULL,
            subject_id INTEGER NOT NULL,
            assigned_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(professor_username, subject_id)
        )
        """)
        
        # Create a compatibility view for the assignments table
        cursor.execute("""
        CREATE VIEW IF NOT EXISTS professor_assignments_view AS
        SELECT 
            psa.id, 
            psa.professor_username, 
            psa.subject_id,
            s.name AS subject_name, 
            psa.assigned_date
        FROM professor_subject_assignments psa
        LEFT JOIN subjects s ON psa.subject_id = s.id
        """)
        
        conn.commit()
        print("Ensured professor_subject_assignments table exists")
        return True
    except Exception as e:
        print(f"Error creating professor_subject_assignments table: {e}")
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
        print(f"Executing query: {fixed_query}")  # Added debug log
        df = pd.read_sql_query(fixed_query, conn, params=params)
        print(f"Query result columns: {df.columns.tolist()}")  # Log the columns of the result
        return df
    except Exception as e:
        print(f"Error executing query: {query}, Error: {e}")
        # Return empty DataFrame with appropriate columns if a SELECT query fails
        if query.strip().upper().startswith("SELECT"):
            # Try to extract column names from the SELECT part
            try:
                # Extract columns or return empty DataFrame with minimal structure
                return pd.DataFrame()
            except:
                return pd.DataFrame()
        raise
    finally:
        conn.close()

def get_professors_list():
    """
    Get a list of professors with their usernames and names.
    Handles the case when professor_profiles table doesn't exist.
    
    Returns:
        DataFrame with 'username' and 'name' columns
    """
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        # Check if professor_profiles table exists
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='professor_profiles'")
        has_profiles_table = cursor.fetchone() is not None
        
        if has_profiles_table:
            # Join user_accounts and professor_profiles
            query = """
                SELECT u.username, COALESCE(p.name, u.username) as name
                FROM user_accounts u
                LEFT JOIN professor_profiles p ON u.username = p.username
                WHERE u.role = 'professor'
                ORDER BY name
            """
        else:
            # Just get usernames and use them as names
            query = """
                SELECT username, username as name
                FROM user_accounts
                WHERE role = 'professor'
                ORDER BY username
            """
        
        df = pd.read_sql_query(query, conn)
        print(f"Found {len(df)} professors")
        return df
    except Exception as e:
        print(f"Error getting professors list: {e}")
        # Return empty DataFrame with expected columns
        return pd.DataFrame(columns=['username', 'name'])
    finally:
        conn.close()

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
    """
    Sync assignments between professor_subject_assignments and teacher_subjects tables
    to ensure professors can see their assigned subjects regardless of which table is used.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # First ensure subjects table has all required columns
        ensure_subjects_table_schema()
        
        # Then ensure both assignment tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='professor_subject_assignments'")
        if not cursor.fetchone():
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS professor_subject_assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                professor_username TEXT NOT NULL,
                subject_id INTEGER NOT NULL,
                assigned_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(professor_username, subject_id)
            )
            """)
            print("Created professor_subject_assignments table")
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='teacher_subjects'")
        if not cursor.fetchone():
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS teacher_subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id INTEGER,
                teacher_name TEXT,
                UNIQUE(subject_id, teacher_name)
            )
            """)
            print("Created teacher_subjects table")
        
        # Then sync data from professor_subject_assignments to teacher_subjects
        cursor.execute("""
        INSERT OR IGNORE INTO teacher_subjects (subject_id, teacher_name)
        SELECT subject_id, professor_username 
        FROM professor_subject_assignments
        WHERE subject_id IS NOT NULL AND professor_username IS NOT NULL
        """)
        
        # And sync data from teacher_subjects to professor_subject_assignments
        cursor.execute("""
        INSERT OR IGNORE INTO professor_subject_assignments (professor_username, subject_id)
        SELECT teacher_name, subject_id 
        FROM teacher_subjects
        WHERE subject_id IS NOT NULL AND teacher_name IS NOT NULL
        """)
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error syncing teacher subject assignments: {e}")
        conn.rollback()
        return False
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
            CREATE TABLE subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                course_code TEXT,
                credit_hours INTEGER DEFAULT 3,
                description TEXT
            )
            ''')
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
        # Check for possible student table names
        possible_names = ['student_profiles', 'students', 'student']
        actual_table_name = None
        
        for name in possible_names:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{name}'")
            if cursor.fetchone():
                actual_table_name = name
                print(f"Found student table with name: {actual_table_name}")
                break
        
        if not actual_table_name:
            # No student table exists - create it with standard name
            print("Creating student_profiles table since none exists")
            cursor.execute("""
            CREATE TABLE student_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                name TEXT,
                student_id TEXT,
                section TEXT,
                email TEXT,
                phone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            conn.commit()
            print("Created student_profiles table")
            return True
            
        # If table name is not 'student_profiles', create a view for compatibility
        if actual_table_name != 'student_profiles':
            # Check the columns in the actual table
            cursor.execute(f"PRAGMA table_info({actual_table_name})")
            columns = [col[1] for col in cursor.fetchall()]
            
            # Create column mappings based on available columns
            column_mappings = []
            
            # Handle username/student_name variations
            if 'username' in columns:
                column_mappings.append('username')
            elif 'student_username' in columns:
                column_mappings.append('student_username AS username')
            elif 'name' in columns and 'student_name' not in columns:
                column_mappings.append('name AS username')
            else:
                column_mappings.append('NULL AS username')
                
            # Handle name column variations
            if 'name' in columns:
                column_mappings.append('name')
            elif 'student_name' in columns:
                column_mappings.append('student_name AS name')
            elif 'fullname' in columns:
                column_mappings.append('fullname AS name')
            else:
                column_mappings.append('username AS name')
                
            # Handle section column variations
            if 'section' in columns:
                column_mappings.append('section')
            else:
                column_mappings.append('NULL AS section')
                
            # Handle student_id column variations
            if 'student_id' in columns:
                column_mappings.append('student_id')
            elif 'id' in columns and actual_table_name == 'students':
                column_mappings.append('id AS student_id')
            else:
                column_mappings.append('NULL AS student_id')
            
            # Create a compatibility view
            try:
                cursor.execute("DROP VIEW IF EXISTS student_profiles_view")
                cursor.execute(f"""
                CREATE VIEW student_profiles_view AS 
                SELECT {', '.join(column_mappings)} FROM {actual_table_name}
                """)
                conn.commit()
                print(f"Created student_profiles_view as compatibility layer over {actual_table_name}")
            except Exception as e:
                print(f"Error creating student profiles view: {e}")
                
        return True
    except Exception as e:
        print(f"Error ensuring student profiles compatibility: {e}")
        return False
    finally:
        conn.close()
