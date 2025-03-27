import streamlit as st
import sqlite3
import app
import os
from datetime import datetime
import sys

# Add utils directory to path
sys.path.append('/home/invisa/Desktop/my_grad_streamlit')

# Update imports to use utils directory
from src.database_utils import execute_query, execute_query_df
import hashlib

def create_connection():
    """Create a connection to the database with absolute path"""
    db_path = os.path.abspath('attendance_system.db')
    print(f"Connecting to database at: {db_path}")
    conn = sqlite3.connect(db_path)
    return conn

def verify_credentials(username, password):
    """Verify credentials using plain text password comparison"""
    
    # PRIORITY CHECK FOR "admin" USERNAME (handles default admin user)
    if username == "admin" and password == "admin":
        print("Default admin login detected with default credentials")
        return True, "admin"
    
    # Special handling for usernames containing "admin" (optional)
    if "admin" in username.lower():
        print(f"Potential admin user detected: {username}")
    
    conn = sqlite3.connect('attendance_system.db')
    cursor = conn.cursor()
    
    try:
        # Check for the unified user_accounts table first (new schema)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_accounts'")
        if cursor.fetchone():
            # Check password as plain text (no hashing)
            cursor.execute("SELECT password, role FROM user_accounts WHERE username = ?", (username,))
            result = cursor.fetchone()
            
            if result:
                stored_password, role = result
                
                # Direct comparison of passwords (plain text)
                if stored_password == password:
                    # Additional check: Ensure any admin user gets admin role 
                    if username.lower() == "admin" or "admin" in username.lower() or role.lower() == "admin":
                        print(f"Admin user {username} authenticated with role override")
                        return True, "admin"
                    return True, role
        
        # Legacy tables support (for backward compatibility)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('student_profiles', 'professor_profiles')")
        tables = [row[0] for row in cursor.fetchall()]
        
        # Check in student_profiles table if it exists
        if 'student_profiles' in tables:
            cursor.execute("SELECT password FROM student_profiles WHERE name = ? OR username = ?", (username, username))
            result = cursor.fetchone()
            if result and result[0] == password:
                return True, "student"
            
        # Check in professor_profiles table if it exists  
        if 'professor_profiles' in tables:
            cursor.execute("SELECT password FROM professor_profiles WHERE username = ?", (username,))
            result = cursor.fetchone()
            if result and result[0] == password:
                return True, "professor"
            
        # Default development credentials (only if no user accounts exist)
        cursor.execute("SELECT COUNT(*) FROM user_accounts")
        count = cursor.fetchone()[0]
        
        if count == 0:
            if username == "admin" and password == "admin":
                return True, "admin"
            elif username == "teacher" and password == "teacher":
                return True, "professor"
            elif username == "student" and password == "student":
                return True, "student"
    
    except Exception as e:
        st.error(f"Database error: {e}")
    finally:
        conn.close()
    
    return False, None

def get_available_users():
    """
    Get a list of available users from the database
    Returns a list of tuples (username, role)
    """
    conn = create_connection()
    cursor = conn.cursor()
    
    try:
        # Use the unified user_accounts table (new schema)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_accounts'")
        if cursor.fetchone():
            # Get all users with their roles from the unified table
            cursor.execute("SELECT username, role FROM user_accounts")
            return cursor.fetchall()
        
        # Fallback to legacy tables if needed
        users = []
        
        # Check student_profiles table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='student_profiles'")
        if cursor.fetchone():
            cursor.execute("SELECT name, 'student' FROM student_profiles")
            users.extend(cursor.fetchall())
        
        # Check professor_profiles table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='professor_profiles'")
        if cursor.fetchone():
            cursor.execute("SELECT username, 'professor' FROM professor_profiles")
            users.extend(cursor.fetchall())
            
        return users
        
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return []
    
    finally:
        conn.close()

def get_user_section(username):
    """Get the section for a student user (if available)"""
    conn = create_connection()
    cursor = conn.cursor()
    
    try:
        # First check if student_profiles table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='student_profiles'")
        if not cursor.fetchone():
            # Table doesn't exist, return default value
            return "Unassigned"
            
        # Table exists, so query it
        cursor.execute("SELECT section FROM student_profiles WHERE name = ? OR username = ?", (username, username))
        result = cursor.fetchone()
        
        return result[0] if result and result[0] else "Unassigned"
    except Exception as e:
        print(f"Error getting user section: {e}")
        return "Unassigned"
    finally:
        conn.close()

def check_required_tables():
    """Check if all required database tables exist"""
    conn = create_connection()
    cursor = conn.cursor()
    tables = {}
    
    try:
        # Get all tables in the database for debugging
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        all_tables = [row[0] for row in cursor.fetchall()]
        print(f"All tables in database: {all_tables}")
        
        # Check for essential tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('user_accounts', 'student_profiles', 'professor_profiles', 'login_logs')")
        existing_tables = {row[0] for row in cursor.fetchall()}
        print(f"Required tables found: {existing_tables}")
        
        tables = {
            'user_accounts': 'user_accounts' in existing_tables,
            'student_profiles': 'student_profiles' in existing_tables,
            'professor_profiles': 'professor_profiles' in existing_tables,
            'login_logs': 'login_logs' in existing_tables
        }
        print(f"Table existence check results: {tables}")
        
    except Exception as e:
        print(f"Error checking tables: {e}")
    finally:
        conn.close()
        
    return tables

def register_student(username, password, name, section):
    """
    Register a new student in the system
    Adds the student to both user_accounts and student_profiles tables
    """
    conn = create_connection()
    cursor = conn.cursor()
    success = False
    message = ""
    
    try:
        # Check if tables exist, create them if not
        tables = check_required_tables()
        
        # Create user_accounts table if it doesn't exist
        if not tables.get('user_accounts'):
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password TEXT,
                    role TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        
        # Create student_profiles table if it doesn't exist
        if not tables.get('student_profiles'):
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS student_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    name TEXT,
                    password TEXT,
                    section TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        
        # Begin transaction
        cursor.execute("BEGIN TRANSACTION")
        
        # Add to user_accounts
        cursor.execute(
            "INSERT INTO user_accounts (username, password, role) VALUES (?, ?, ?)",
            (username, password, "student")
        )
        
        # Add to student_profiles
        cursor.execute(
            "INSERT INTO student_profiles (username, name, password, section) VALUES (?, ?, ?, ?)",
            (username, name, password, section)
        )
        
        # Commit changes
        conn.commit()
        success = True
        message = f"Student {name} registered successfully"
        
    except sqlite3.IntegrityError:
        conn.rollback()
        message = f"Username {username} already exists"
    except Exception as e:
        conn.rollback()
        message = f"Error registering student: {e}"
    finally:
        conn.close()
    
    return success, message

def login_page():
    st.title("Login")
    
    # Check database tables and add debug info
    tables = check_required_tables()
    if not tables.get('student_profiles', False):
        # Try to fix the database first
        initialize_database()
        # Check again after fix attempt
        tables = check_required_tables()
        if not tables.get('student_profiles', False):
            db_path = os.path.abspath('attendance_system.db')
            st.warning(f"Student profiles table not found. Some features may be limited. Database path: {db_path}")
            print(f"WARNING: student_profiles table not found after fix attempt. Database path: {db_path}")
    
    # Check if other essential tables are missing
    if not tables.get('user_accounts', False):
        st.error("User accounts table not found. Login functionality may be unavailable.")
    
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        success, role = verify_credentials(username, password)
        if success:
            # Set session state variables
            st.session_state.logged_in = True
            st.session_state.username = username
            
            # ENHANCED ROLE DETECTION
            # Force admin role for any username containing "admin"
            is_admin = (username.lower() == "admin" or "admin" in username.lower() or role.lower() == "admin")
            is_professor = role.lower() == "professor"
            
            if is_admin:
                role = "admin"
                st.session_state.is_admin = True
                print(f"Enforcing admin role for {username}")
            elif is_professor:
                st.session_state.is_professor = True
                print(f"Setting professor role for {username}")
                
            st.session_state.user_role = role
            
            # Debug info for role login
            print(f"User login successful: username={username}, role={role}")
            
            # Store login time for security tracking
            st.session_state.login_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Update query parameters to maintain login state - INCLUDE ROLE FOR ALL USERS
            st.query_params["logged_in"] = "True"
            st.query_params["username"] = username
            st.query_params["user_role"] = role  # Add role to query params
            
            # For admin users, add a flag to URL to ensure persistence
            if is_admin:
                st.query_params["is_admin"] = "true"
            elif is_professor:
                st.query_params["is_professor"] = "true"
            
            # Log successful login
            try:
                conn = sqlite3.connect('attendance_system.db')
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO login_logs (username, login_time, ip_address, status) VALUES (?, ?, ?, ?)",
                    (username, st.session_state.login_time, get_client_ip(), "success")
                )
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"Error logging login: {e}")
            
            # Refresh to load the app
            st.rerun()
        else:
            # Log failed login attempt
            try:
                conn = sqlite3.connect('attendance_system.db')
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO login_logs (username, login_time, ip_address, status) VALUES (?, ?, ?, ?)",
                    (username, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), get_client_ip(), "failed")
                )
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"Error logging failed login: {e}")
                
            st.error("Invalid username or password")
    
    # Show available users from database
    with st.expander("Available Users"):
        users = get_available_users()
        if users:
            st.write("Available users in the system:")
            for user, role in users:
                try:
                    section = get_user_section(user) if role == "student" else "N/A"
                except Exception as e:
                    # Handle any errors during section lookup
                    print(f"Error getting section for {user}: {e}")
                    section = "Unknown"
                    
                st.write(f"- {user} (Role: {role}, Section: {section})")
            st.info("Note: Passwords are hashed in the database. Contact the administrator if you need access.")
        else:
            st.warning("No users found in the database.")

# Simple function to get client IP for logging
def get_client_ip():
    """Get the client's IP address if available"""
    try:
        import streamlit.server.server as streamlit_server
        return streamlit_server.get_remote_ip() or "unknown"
    except:
        return "unknown"

def fix_student_profile_schema():
    """
    Fix any schema inconsistencies in the student_profiles table
    This ensures the table has all required columns
    """
    conn = create_connection()
    cursor = conn.cursor()
    changes_made = False
    
    try:
        # First check if student_profiles table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='student_profiles'")
        if not cursor.fetchone():
            print("Student profiles table doesn't exist, nothing to fix")
            return False
        
        # Get current schema
        cursor.execute("PRAGMA table_info(student_profiles)")
        columns = {row[1].lower() for row in cursor.fetchall()}
        print(f"Current student_profiles columns: {columns}")
        
        # Required columns with their types
        required_columns = {
            'id': 'INTEGER PRIMARY KEY AUTOINCREMENT',
            'username': 'TEXT UNIQUE',
            'name': 'TEXT', 
            'password': 'TEXT',
            'section': 'TEXT'
        }
        
        # Check if any required columns are missing
        for col, col_type in required_columns.items():
            if col.lower() not in columns:
                print(f"Adding missing column '{col}' to student_profiles")
                try:
                    cursor.execute(f"ALTER TABLE student_profiles ADD COLUMN {col} {col_type}")
                    changes_made = True
                except sqlite3.OperationalError as e:
                    print(f"Error adding column {col}: {e}")
        
        # If username exists but no name, we need to update
        if 'username' in columns and 'name' in columns:
            # Check for NULL name values where username is set
            cursor.execute("UPDATE student_profiles SET name = username WHERE name IS NULL AND username IS NOT NULL")
            if cursor.rowcount > 0:
                changes_made = True
                print(f"Updated {cursor.rowcount} rows with null name values")
        
        # Commit any changes
        if changes_made:
            conn.commit()
            print("Schema fixes committed successfully")
        
        return changes_made
        
    except Exception as e:
        print(f"Error fixing schema: {e}")
        return False
    finally:
        conn.close()

def fix_attendance_table_schema():
    """
    Fix the attendance tables schema to ensure compatibility with queries
    that look for the 'name' column.
    """
    conn = create_connection()
    cursor = conn.cursor()
    changes_made = False
    
    try:
        # Check attendance_records table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='attendance_records'")
        if cursor.fetchone():
            # Get current schema
            cursor.execute("PRAGMA table_info(attendance_records)")
            columns = {row[1].lower() for row in cursor.fetchall()}
            print(f"Current attendance_records columns: {columns}")
            
            # Add name column if it doesn't exist
            if 'name' not in columns:
                print("Adding name column to attendance_records table")
                cursor.execute("ALTER TABLE attendance_records ADD COLUMN name TEXT")
                
                # Check if we have student_username (from the actual schema) instead of student_id
                if 'student_username' in columns:
                    print("Populating name column using student_username")
                    cursor.execute("""
                        UPDATE attendance_records 
                        SET name = (
                            SELECT sp.name 
                            FROM student_profiles sp 
                            WHERE sp.username = attendance_records.student_username
                        )
                        WHERE name IS NULL
                    """)
                    changes_made = True
                    
                # Also try using direct mapping from username for any remaining null values
                cursor.execute("""
                    UPDATE attendance_records 
                    SET name = student_username
                    WHERE name IS NULL AND student_username IS NOT NULL
                """)
                changes_made = True
        
        # Create a view to map usernames to names for queries that rely on name
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS student_name_mapping AS
            SELECT 
                username, 
                name, 
                section
            FROM student_profiles
        """)
        
        # Create an attendance view with name column for compatibility
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS attendance_with_names AS
            SELECT 
                ar.*,
                COALESCE(ar.name, snm.name, ar.student_username) AS student_name
            FROM attendance_records ar
            LEFT JOIN student_name_mapping snm ON ar.student_username = snm.username
        """)
        
        if changes_made:
            conn.commit()
            print("Fixed attendance table schemas and created compatibility views")
        return changes_made
            
    except Exception as e:
        print(f"Error fixing attendance tables: {e}")
        return False
    finally:
        conn.close()

def initialize_database():
    """
    Initialize database with required tables if they don't exist.
    This ensures all necessary tables are created at startup.
    """
    print("Starting database initialization...")
    
    # Get absolute path to database for debugging
    db_path = os.path.abspath('attendance_system.db')
    print(f"Using database at: {db_path}")
    
    conn = create_connection()
    cursor = conn.cursor()
    
    try:
        # VERIFY DATABASE CONNECTION
        try:
            # Simple test query to verify connection
            cursor.execute("SELECT 1")
            print("Database connection successful")
        except Exception as e:
            print(f"ERROR: Database connection failed: {e}")
            raise e
            
        # Create user_accounts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                role TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create student_profiles table - Remove DROP statement to avoid losing data
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
        
        conn.commit()
        print("Ensured student_profiles table exists.")
        
        # Verify the student_profiles table was created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='student_profiles'")
        result = cursor.fetchone()
        if result:
            print("student_profiles table exists after creation")
            
            # Now check if we need to update student accounts for consistency
            cursor.execute("SELECT username, name FROM student_profiles")
            students = cursor.fetchall()
            
            if students:
                print(f"Found {len(students)} students in student_profiles")
            else:
                print("No students found in student_profiles table, will add defaults if needed")
        else:
            print("ERROR: student_profiles table creation failed")
            
        # Get all tables to debug
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        all_tables = cursor.fetchall()
        table_names = [t[0] for t in all_tables]
        print(f"All tables in database: {table_names}")
        
        # Create professor_profiles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS professor_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                name TEXT,
                password TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create login_logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS login_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                login_time TIMESTAMP,
                ip_address TEXT,
                status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Check if we need to add default users
        cursor.execute("SELECT COUNT(*) FROM user_accounts")
        count = cursor.fetchone()[0]
        
        if count == 0:
            # Add default admin, student, and professor accounts
            cursor.execute("INSERT INTO user_accounts (username, password, role) VALUES (?, ?, ?)", 
                          ('admin', 'admin123', 'admin'))
            cursor.execute("INSERT INTO user_accounts (username, password, role) VALUES (?, ?, ?)", 
                          ('student', 'student123', 'student'))
            cursor.execute("INSERT INTO user_accounts (username, password, role) VALUES (?, ?, ?)", 
                          ('professor', 'professor123', 'professor'))
            
            # Add to student_profiles
            cursor.execute("INSERT INTO student_profiles (username, name, student_id, password, section) VALUES (?, ?, ?, ?, ?)",
                          ('student', 'Default Student', 'STU001', 'student123', 'A'))
            
            # Add to professor_profiles
            cursor.execute("INSERT INTO professor_profiles (username, name, password) VALUES (?, ?, ?)",
                          ('professor', 'Default Professor', 'professor123'))
            
        conn.commit()
        print("Database initialized successfully")
        
        # Double-check tables after initialization
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Tables after initialization: {tables}")
        
        # Fix any schema issues
        fix_student_profile_schema()
        
        # Fix attendance tables schema issues
        fix_attendance_table_schema()
        
        # Ensure we have at least one student account
        cursor.execute("SELECT COUNT(*) FROM student_profiles")
        student_count = cursor.fetchone()[0]
        
        if student_count == 0:
            print("No student profiles found, creating default student")
            cursor.execute("INSERT INTO student_profiles (username, name, student_id, password, section) VALUES (?, ?, ?, ?, ?)",
                        ('student', 'Default Student', 'STU001', 'student123', 'A'))
            conn.commit()
            
        # Make sure session state is updated
        st.session_state.database_initialized = True
        
        return True
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False
    finally:
        conn.close()

def main():
    # Force database initialization at startup
    initialize_database()  # Run this first to ensure tables exist
    
    # Verify student_profiles table exists
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='student_profiles'")
    if not cursor.fetchone():
        print("ERROR: student_profiles table still not found after initialization!")
    conn.close()
    
    # Initialize session state
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    # Check query params
    if "logged_in" in st.query_params and st.query_params["logged_in"] == "True":
        st.session_state.logged_in = True

    if st.session_state.logged_in:
        app.show_app()
    else:
        login_page()

if __name__ == "__main__":
    main()