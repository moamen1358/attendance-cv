import streamlit as st
import sqlite3
import app
import os
from datetime import datetime
import sys
import hashlib

# Add utils directory to path
sys.path.append('/home/invisa/Desktop/my_grad_streamlit')

# Update imports to use direct module imports without src prefix
from database_utils import execute_query, execute_query_df
from database_sync import sync_user_tables, register_user

# Import centralized database initialization
try:
    from db_init import initialize_database as init_centralized_db, check_database_integrity
except ImportError:
    from .db_init import initialize_database as init_centralized_db, check_database_integrity

def create_connection():
    """Create a connection to the database with absolute path"""
    db_path = os.path.abspath('attendance_system.db')
    print(f"Connecting to database at: {db_path}")
    conn = sqlite3.connect(db_path)
    return conn

def verify_credentials(username, password):
    """Verify credentials using users_enhanced table as primary authentication"""
    
    conn = sqlite3.connect('attendance_system.db')
    cursor = conn.cursor()
    
    try:
        # Check if users_enhanced table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users_enhanced'")
        if cursor.fetchone():
            # Hash the password using both methods for compatibility
            sha256_hash = hashlib.sha256(password.encode()).hexdigest()
            md5_hash = hashlib.md5(password.encode()).hexdigest()
            
            # Query users_enhanced table
            cursor.execute("""
                SELECT password_hash, role, full_name 
                FROM users_enhanced 
                WHERE username = ? AND status = 'active'
            """, (username,))
            result = cursor.fetchone()
            
            if result:
                stored_hash, role, full_name = result
                print(f"Found user {username} ({full_name}) in users_enhanced with role {role}")
                
                # Check both SHA256 and MD5 hashes, plus plain text for compatibility
                if (stored_hash == sha256_hash or 
                    stored_hash == md5_hash or 
                    stored_hash == password):  # Plain text fallback
                    
                    print(f"Authentication successful for {username} with role {role}")
                    
                    # Update last login timestamp
                    cursor.execute("""
                        UPDATE users_enhanced 
                        SET last_login = CURRENT_TIMESTAMP 
                        WHERE username = ?
                    """, (username,))
                    conn.commit()
                    
                    # Convert teacher role to professor for app routing consistency
                    if role == "teacher":
                        role = "professor"
                        print(f"Converting teacher role to professor for {username}")
                    
                    return True, role
                else:
                    print(f"Password verification failed for user {username}")
            else:
                print(f"User {username} not found in users_enhanced or account inactive")
        
        # Fallback to legacy tables if users_enhanced doesn't exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_accounts_enhanced'")
        if cursor.fetchone():
            cursor.execute("SELECT password, role FROM user_accounts_enhanced WHERE username = ?", (username,))
            result = cursor.fetchone()
            
            if result:
                stored_password, role = result
                if stored_password == password:
                    print(f"Legacy authentication successful for {username} with role {role}")
                    if role == "teacher":
                        role = "professor"
                    return True, role
        
        # Hard-coded fallback credentials for development
        if username == "admin" and password in ["admin", "admin123"]:
            return True, "admin"
        elif username == "teacher" and password in ["teacher", "teacher123"]:
            return True, "professor"
        elif username == "student" and password in ["student", "student123"]:
            return True, "student"
        
        print(f"No matching credentials found for {username}")
        return False, None
    
    except Exception as e:
        print(f"Database error during authentication: {e}")
        st.error(f"Database error: {e}")
        return False, None
    finally:
        conn.close()

def verify_credentials_enhanced(username, password):
    """Verify credentials using the enhanced database structure"""
    
    # PRIORITY CHECK FOR "admin" USERNAME (handles default admin user)
    if username == "admin" and password == "admin":
        print("Default admin login detected with default credentials")
        return True, "admin"
    
    conn = sqlite3.connect('attendance_system.db')
    cursor = conn.cursor()
    
    try:
        # Check the enhanced user_accounts table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_accounts_enhanced'")
        if cursor.fetchone():
            # Check password with hashing for enhanced table
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            cursor.execute("SELECT role, student_id, professor_id FROM user_accounts_enhanced WHERE username = ? AND password = ?", 
                         (username, hashed_password))
            result = cursor.fetchone()
            
            if result:
                role, student_id, professor_id = result
                print(f"Enhanced login successful for {username} with role {role}")
                return True, role
        
        # Fall back to old verify_credentials for backwards compatibility
        return verify_credentials(username, password)
    
    except Exception as e:
        st.error(f"Database error: {e}")
        return False, None
    finally:
        conn.close()

def get_student_info_enhanced(username):
    """Get student information from enhanced database"""
    conn = sqlite3.connect('attendance_system.db')
    cursor = conn.cursor()
    
    try:
        # Try enhanced table first
        cursor.execute("""
            SELECT sp.name, sp.student_number, sp.academic_year, sp.current_semester, 
                   d.department_name, d.department_code
            FROM student_profiles_enhanced sp
            JOIN departments d ON sp.department_id = d.department_id
            WHERE sp.username = ?
        """, (username,))
        
        result = cursor.fetchone()
        if result:
            return {
                'name': result[0],
                'student_number': result[1],
                'academic_year': result[2],
                'current_semester': result[3],
                'department_name': result[4],
                'department_code': result[5]
            }
        
        # Fall back to old tables
        cursor.execute("SELECT name FROM student_profiles_enhanced WHERE username = ?", (username,))
        result = cursor.fetchone()
        if result:
            return {'name': result[0]}
        
        return None
        
    except Exception as e:
        print(f"Error getting student info: {e}")
        return None
    finally:
        conn.close()

def get_available_users():
    """
    Get a list of available users from the database
    Returns a list of tuples (username, role)
    """
    conn = create_connection()
    cursor = conn.cursor()
    
    try:
        # Check users_enhanced table first (primary user table)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users_enhanced'")
        if cursor.fetchone():
            cursor.execute("""
                SELECT username, role 
                FROM users_enhanced 
                WHERE status = 'active' 
                ORDER BY role, username
            """)
            users = cursor.fetchall()
            # Convert teacher to professor for consistency
            return [(user, 'professor' if role == 'teacher' else role) for user, role in users]
        
        # Fallback to legacy tables if users_enhanced doesn't exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_accounts_enhanced'")
        if cursor.fetchone():
            cursor.execute("SELECT username, role FROM user_accounts_enhanced ORDER BY role, username")
            users = cursor.fetchall()
            return [(user, 'professor' if role == 'teacher' else role) for user, role in users]
        
        # Last resort - empty list
        return []
        
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
        # First check if student_profiles_enhanced table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='student_profiles_enhanced'")
        if not cursor.fetchone():
            # Table doesn't exist, return default value
            return "Unassigned"
            
        # Table exists, so query it
        cursor.execute("SELECT section FROM student_profiles_enhanced WHERE name = ? OR username = ?", (username, username))
        result = cursor.fetchone()
        
        return result[0] if result and result[0] else "Unassigned"
    except Exception as e:
        print(f"Error getting user section: {e}")
        return "Unassigned"
    finally:
        conn.close()

def check_required_tables():
    """Check if all required database tables exist - Updated for enhanced tables"""
    conn = create_connection()
    cursor = conn.cursor()
    tables = {}
    
    try:
        # Get all tables in the database for debugging
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        all_tables = [row[0] for row in cursor.fetchall()]
        print(f"All tables in database: {all_tables}")
        
        # Check for enhanced tables (new structure)
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name IN (
                'user_accounts_enhanced', 
                'student_profiles_enhanced', 
                'professor_profiles', 
                'login_logs'
            )
        """)
        existing_tables = {row[0] for row in cursor.fetchall()}
        print(f"Enhanced tables found: {existing_tables}")
        
        # Update table existence mapping to use enhanced tables
        tables = {
            'user_accounts': 'user_accounts_enhanced' in existing_tables,
            'student_profiles': 'student_profiles_enhanced' in existing_tables,
            'professor_profiles': 'professor_profiles' in existing_tables,
            'login_logs': 'login_logs' in existing_tables
        }
        print(f"Enhanced table existence check results: {tables}")
        
    except Exception as e:
        print(f"Error checking tables: {e}")
    finally:
        conn.close()
        
    return tables

# Replace the existing register_student function with this improved version
def register_student(username, password, name, section):
    """
    Register a new student in the system using the unified registration function
    Adds the student to both user_accounts and student_profiles tables
    """
    profile_data = {
        'name': name,
        'student_id': username,  # Using username as student ID by default
        'section': section
    }
    
    success = register_user(username, password, 'student', profile_data)
    message = "Student registered successfully!" if success else "Failed to register student"
    
    return success, message

# Add function to ensure all tables are in sync at login
def ensure_database_consistency():
    """Ensure database tables are in sync before login"""
    try:
        changes = sync_user_tables()
        if changes > 0:
            print(f"Database synchronized. {changes} changes made.")
        return True
    except Exception as e:
        print(f"Error ensuring database consistency: {e}")
        return False

# Modify login_page function to call the sync first
def login_page():
    # Apply consistent styling for login page - wide layout
    st.markdown("""
    <style>
    /* Wide layout for login page */
    .main .block-container {
        max-width: 100% !important;
        width: 100% !important;
        padding: 40px 80px !important;
    }
    
    /* Hide sidebar on login page */
    [data-testid="stSidebar"] {
        display: none !important;
    }
    
    /* Force full width layout */
    .reportview-container .main .block-container,
    .appview-container .main .block-container,
    div[data-testid="stAppViewContainer"] > section[data-testid="stAppViewContainer"] > div,
    div[data-testid="stAppViewContainer"] > section > div {
        max-width: 100% !important;
        padding-left: 80px !important;
        padding-right: 80px !important;
        width: 100% !important;
    }
    
    /* Title styling */
    .stTitle h1 {
        color: #2c3e50;
        font-size: 2.5rem;
        font-weight: 600;
        margin-bottom: 40px;
        padding-bottom: 20px;
        border-bottom: 2px solid #3498db;
    }
    
    /* Input container styling */
    .stTextInput {
        margin-bottom: 20px;
    }
    
    /* Input field styling - wide but controlled */
    .stTextInput > div > div > input {
        width: 100% !important;
        height: 50px !important;
        border-radius: 8px !important;
        border: 2px solid #bdc3c7 !important;
        padding: 0 15px !important;
        font-size: 16px !important;
        background-color: #ffffff !important;
        color: #000000 !important;
        box-sizing: border-box !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #3498db !important;
        outline: none !important;
        box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1) !important;
        color: #000000 !important;
    }
    
    /* Ensure placeholder text is visible */
    .stTextInput > div > div > input::placeholder {
        color: #666666 !important;
    }
    
    /* Input labels */
    .stTextInput > label {
        font-weight: 500 !important;
        color: #2c3e50 !important;
        margin-bottom: 8px !important;
        display: block !important;
    }
    
    /* Login button styling - wide */
    .stButton {
        margin-top: 30px;
    }
    
    .stButton > button {
        width: 100% !important;
        height: 50px !important;
        background-color: #3498db !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        cursor: pointer !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        background-color: #2980b9 !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 12px rgba(52, 152, 219, 0.3) !important;
    }
    
    .stButton > button:active {
        transform: translateY(0px) !important;
    }
    
    /* Expander styling for user list */
    .streamlit-expanderHeader {
        background-color: #ecf0f1 !important;
        border-radius: 8px !important;
        border: 1px solid #bdc3c7 !important;
        margin-top: 30px !important;
    }
    
    /* Error/success message styling */
    .stAlert {
        margin-top: 20px !important;
        border-radius: 8px !important;
    }
    
    /* Ensure wide layout consistency */
    .element-container,
    [data-testid="stVerticalBlock"] {
        max-width: 100% !important;
        width: 100% !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("🇪🇬 Egyptian University Attendance System")
    
    # Display sample Egyptian credentials
    with st.expander("📋 Sample Login Credentials", expanded=False):
        st.markdown("""
        ### 🔐 Test Accounts (Egyptian Sample Data)
        
        **👨‍💼 Administrator:**
        - Username: `admin` | Password: `admin`
        - Username: `dean` | Password: `dean`
        
        **👨‍🏫 Teachers/Professors:**
        - Username: `emp2024001` | Password: `emp2024001`
        - Username: `emp2024002` | Password: `emp2024002`
        - Username: `emp2024003` | Password: `emp2024003`
        
        **👨‍🎓 Students:**
        - Username: `2024001` | Password: `2024001`
        - Username: `2024002` | Password: `2024002`
        - Username: `2024003` | Password: `2024003`
        
        *Note: All passwords are set to match the username for easy testing*
        *Egyptian university data includes authentic names and departments*
        """)
    
    # Sync tables before proceeding
    ensure_database_consistency()
    
    # Check database tables and add debug info
    tables = check_required_tables()
    if not tables.get('student_profiles', False):
        # Try to fix the database first
        initialize_database()
        # Check again after fix attempt
        tables = check_required_tables()
        if not tables.get('student_profiles', False):
            db_path = os.path.abspath('attendance_system.db')
            st.warning(f"Student profiles table not found (looking for student_profiles_enhanced). Some features may be limited. Database path: {db_path}")
            print(f"WARNING: student_profiles_enhanced table not found after fix attempt. Database path: {db_path}")
    
    # Check if other essential tables are missing
    if not tables.get('user_accounts', False):
        st.error("User accounts table not found (looking for user_accounts_enhanced). Login functionality may be unavailable.")
    
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
        # Try to get IP from headers if available
        return "127.0.0.1"  # Default for local development
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
                            FROM student_profiles_enhanced sp 
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
    
    # Call centralized database initialization
    try:
        success = init_centralized_db()
        if success:
            print("✅ Centralized database initialization successful")
            
            # Check database integrity
            if check_database_integrity():
                print("✅ Database integrity check passed")
            else:
                print("⚠️ Database integrity check failed")
            
            # Make sure session state is updated
            st.session_state.database_initialized = True
            return True
        else:
            print("❌ Centralized database initialization failed")
            return False
    except Exception as e:
        print(f"❌ Error calling centralized database initialization: {e}")
        return False

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