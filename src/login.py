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
from global_css_handler import apply_global_css

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
    
    # Special case for default admin
    if username == "admin" and password == "admin":
        print("Default admin login detected")
        return True, "admin"
    
    conn = sqlite3.connect('attendance_system.db')
    cursor = conn.cursor()
    
    try:
        # Check if users_enhanced table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users_enhanced'")
        if cursor.fetchone():
            # Check both the direct username match (for students) and the password hash
            if username == password:
                # If username equals password, create the hash from that
                input_password_hash = hashlib.sha256(password.encode()).hexdigest()
            else:
                # Otherwise, use the provided password
                input_password_hash = hashlib.sha256(password.encode()).hexdigest()
            
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
                
                # Compare the hashed input password with the stored hash
                if stored_hash == input_password_hash:
                    print(f"✅ Authentication successful for {username} with role {role}")
                    
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
                    print(f"❌ Password hash mismatch")
            else:
                print(f"❌ User {username} not found in users_enhanced or account inactive")
        
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
        if username == "teacher" and password in ["teacher", "teacher123"]:
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
        # Get user info and linked student info
        cursor.execute("""
            SELECT u.full_name, s.roll_number, s.year, s.department, s.name, s.email, s.phone
            FROM users_enhanced u
            LEFT JOIN students_enhanced s ON u.username = LOWER(REPLACE(REPLACE(REPLACE(s.name, ' ', '_'), '.', ''), '-', '_'))
            WHERE u.username = ? AND u.role = 'student'
        """, (username,))
        
        result = cursor.fetchone()
        if result:
            return {
                'name': result[4] if result[4] else result[0],  # Use student name or full_name
                'roll_number': result[1],
                'academic_year': result[2],
                'department': result[3],
                'email': result[5],
                'phone': result[6]
            }
        
        # Fall back - just get user info
        cursor.execute("SELECT full_name FROM users_enhanced WHERE username = ? AND role = 'student'", (username,))
        result = cursor.fetchone()
        if result:
            return {'name': result[0]}
        
        return None
        
    except Exception as e:
        print(f"Error getting student info: {e}")
        return None
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
                'users_enhanced', 
                'student_profiles_enhanced', 
                'professor_profiles', 
                'login_logs'
            )
        """)
        existing_tables = {row[0] for row in cursor.fetchall()}
        print(f"Enhanced tables found: {existing_tables}")
        
        # Update table existence mapping to use enhanced tables
        tables = {
            'user_accounts': 'users_enhanced' in existing_tables,
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
    # Apply modern, professional styling for login page that matches the provided image
    st.markdown("""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');
    
    /* Global styling */
    * {
        font-family: 'Roboto', sans-serif !important;
        box-sizing: border-box;
    }
    
    html, body {
        margin: 0 !important;
        padding: 0 !important;
        height: 100% !important;
        background-color: #f5f5f5 !important;
    }
    
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Main container styling */
    .main .block-container {
        max-width: 100% !important;
        width: 100% !important;
        padding: 0 !important;
        margin: 0 !important;
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    
    /* Hide sidebar */
    [data-testid="stSidebar"] {
        display: none !important;
    }
    
    /* Main background */
    .stApp {
        background-color: #f7f9fc !important;
        min-height: 100vh;
        margin: 0;
        padding: 0;
        overflow-x: hidden;
    }
    
    /* Login container */
    .login-container {
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 100vh;
        padding: 0;
        margin: 0;
    }
    
    /* Login card - exact match with image */
    .login-card {
        background-color: white;
        width: 80%;
        max-width: 900px;
        margin: 0 auto;
        border-radius: 10px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        padding: 40px;
        position: relative;
    }
    
    /* Login form area */
    .login-form-area {
        display: flex;
        flex-direction: column;
    }
    
    /* Login header */
    .login-header {
        margin-bottom: 30px;
    }
    
    .login-title {
        font-size: 24px;
        font-weight: 700;
        color: #000;
        margin: 0;
    }
    
    /* Input styling - exact match with image */
    .stTextInput {
        margin-bottom: 25px;
    }
    
    .stTextInput > label {
        font-weight: 500 !important;
        color: #333 !important;
        font-size: 14px !important;
        margin-bottom: 8px !important;
        display: block !important;
    }
    
    .stTextInput > div > div > input {
        width: 100% !important;
        height: 50px !important;
        border-radius: 8px !important;
        border: 1px solid #e0e0e0 !important;
        padding: 0 15px !important;
        font-size: 15px !important;
        background-color: white !important;
        color: #333 !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #4a6cf7 !important;
        box-shadow: 0 0 0 2px rgba(74, 108, 247, 0.1) !important;
    }
    
    /* Button styling - exact match with image */
    .stButton > button {
        width: 100% !important;
        height: 50px !important;
        background-color: #4a6cf7 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-size: 16px !important;
        font-weight: 500 !important;
        cursor: pointer !important;
        transition: all 0.3s !important;
    }
    
    .stButton > button:hover {
        background-color: #3a5bd8 !important;
    }
    
    /* Two-column layout */
    .login-columns {
        display: flex;
        flex-direction: row;
    }
    
    .left-column {
        flex: 1;
        padding-right: 30px;
    }
    
    .right-column {
        flex: 1;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    
    .right-column img {
        width: 100%;
        max-width: 350px;
        border-radius: 10px;
    }
    
    /* Footer links */
    .footer-links {
        display: flex;
        justify-content: space-between;
        margin-top: 20px;
    }
    
    .footer-link {
        color: #333;
        text-decoration: none;
        font-size: 14px;
    }
    
    .footer-link:hover {
        color: #4a6cf7;
        text-decoration: underline;
    }
    
    /* Responsive adjustments */
    @media (max-width: 768px) {
        .login-card {
            width: 95%;
            padding: 30px;
        }
        
        .login-columns {
            flex-direction: column;
        }
        
        .left-column {
            padding-right: 0;
            margin-bottom: 30px;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <style>
    /* Full page background */
    .stApp {
        background: url('https://images.unsplash.com/photo-1517842645767-c639042777db?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80');
        background-size: cover;
        background-position: center;
        min-height: 100vh;
        margin: 0;
        padding: 0;
        overflow-x: hidden;
    }
    
    /* Login container */
    .login-container {
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 100vh;
        padding: 0;
        margin: 0;
    
    }
    
    /* Login card - match exactly with image */
    .login-card {
        background-color: transparent;
        width: 100%;
        max-width: 1080px;
        margin: 0 auto;
        position: relative;
        padding: 0;
        box-shadow: none;
    }
    
    /* Header styling - match exactly with image */
    .login-header {
        text-align: left;
        margin-bottom: 15px;
        margin-left: 95px;
        margin-top: 30px;
    }
    
    .login-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #000000;
        margin-bottom: 5px;
    }
    
    /* Logo styling */
    .logo {
        position: absolute;
        top: 30px;
        left: 30px;
    }
    
    /* Navigation */
    .nav-buttons {
        position: absolute;
        top: 30px;
        right: 30px;
        display: flex;
        gap: 10px;
    }
    
    .nav-btn {
        background-color: rgba(255, 255, 255, 0.9);
        color: #333;
        border-radius: 20px;
        padding: 8px 16px;
        font-size: 14px;
        font-weight: 500;
        text-decoration: none;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    
    .signup-btn {
        background-color: #e2bdff;
        color: #333;
    }
    
    /* Form area */
    .login-form-area {
        width: 50%;
        float: left;
        padding-left: 30px;
    }
    
    /* Right side image area */
    .right-image-area {
        width: 50%;
        float: right;
        text-align: center;
    }
    
    .right-image-area img {
        width: 80%;
        max-width: 350px;
        border-radius: 100%;
        box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.1);
        margin-top: 50px;
        height: 100%;
        object-fit: cover;
    }
    
    /* Input styling - match exactly with image */
    .stTextInput {
        margin-bottom: 20px;
    }
    
    .stTextInput > label {
        font-weight: 500 !important;
        color: #333333 !important;
        font-size: 14px !important;
        margin-bottom: 8px !important;
        display: block !important;
        opacity: 0.9 !important;
    }
    
    .stTextInput > div > div > input {
        width: 100% !important;
        height: 45px !important;
        border-radius: 10px !important;
        border: 1px solid #DDDDDD !important;
        padding: 0 15px !important;
        font-size: 15px !important;
        background-color: #FFFFFF !important;
        color: #333333 !important;
        box-sizing: border-box !important;
        transition: all 0.3s ease !important;
        font-weight: 400 !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #AAAAAA !important;
        outline: none !important;
        box-shadow: 0 0 3px rgba(0, 0, 0, 0.1) !important;
        background-color: #FFFFFF !important;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: #CCCCCC !important;
        font-weight: 400 !important;
    }
    
    /* Label styling */
    .input-label {
        color: rgba(255, 255, 255, 0.7) !important;
        font-size: 0.9rem;
        margin-bottom: 5px;
        display: flex;
        align-items: center;
    }
    
    .input-label-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        background-color: #e2bdff;
        border-radius: 50%;
        margin-right: 8px;
    }
    
    /* Login button styling - match exactly with image */
    .stButton {
        margin-top: 15px;
        margin-bottom: 15px;
        display: inline-block;
    }
    
    .stButton > button {
        width: auto !important;
        min-width: 120px !important;
        height: 40px !important;
        background: #e6f2f5 !important;
        color: #333333 !important;
        border-radius: 5px !important;
        border: none !important;
        font-size: 15px !important;
        font-weight: 500 !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1) !important;
        padding: 0 30px !important;
    }
    
    .stButton > button:hover {
        background: #d6e8ec !important;
    }
    
    .stButton > button:active {
        transform: translateY(1px) !important;
    }
    
    /* Remember me checkbox */
    .remember-me {
        display: flex;
        align-items: center;
        margin-top: 15px;
        color: rgba(255, 255, 255, 0.7);
        font-size: 14px;
    }
    
    .stCheckbox {
        margin-bottom: 0 !important;
    }
    
    .stCheckbox > div > div > label {
        color: rgba(255, 255, 255, 0.7) !important;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: rgba(255, 255, 255, 0.8) !important;
        border-radius: 12px !important;
        border: 1px solid rgba(102, 126, 234, 0.2) !important;
        margin-top: 25px !important;
        padding: 15px !important;
        transition: all 0.3s ease !important;
    }
    
    .streamlit-expanderHeader:hover {
        background: rgba(255, 255, 255, 0.9) !important;
        border-color: rgba(102, 126, 234, 0.3) !important;
        transform: translateY(-1px) !important;
    }
    
    .streamlit-expanderContent {
        background: rgba(255, 255, 255, 0.95) !important;
        border-radius: 0 0 12px 12px !important;
        border: 1px solid rgba(102, 126, 234, 0.2) !important;
        border-top: none !important;
        padding: 20px !important;
    }
    
    /* Credential list styling */
    .credential-section {
        margin-bottom: 20px;
    }
    
    .credential-section h4 {
        color: #2c3e50 !important;
        font-weight: 600 !important;
        margin-bottom: 10px !important;
    }
    
    .credential-item {
        background: rgba(102, 126, 234, 0.1);
        padding: 8px 12px;
        border-radius: 8px;
        margin-bottom: 5px;
        font-family: 'Monaco', 'Menlo', monospace;
        font-size: 13px;
        color: #2c3e50;
    }
    
    /* Alert styling */
    .stAlert {
        margin-top: 20px !important;
        border-radius: 12px !important;
        border: none !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1) !important;
    }
    
    /* Success message */
    .stSuccess {
        background: linear-gradient(135deg, #2ecc71 0%, #27ae60 100%) !important;
        color: white !important;
    }
    
    /* Error message */
    .stError {
        background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%) !important;
        color: white !important;
    }
    
    /* Warning message */
    .stWarning {
        background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%) !important;
        color: white !important;
    }
    
    /* Info message */
    .stInfo {
        background: linear-gradient(135deg, #3498db 0%, #2980b9 100%) !important;
        color: white !important;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .login-card {
            padding: 30px 25px;
        }
        
        .login-container {
            padding: 0 15px;
            margin: 0;
        }
        
        .login-title {
            font-size: 2rem;
        }
        
        .university-icon {
            font-size: 3rem;
        }
    }
    
    /* Animation for login card */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .login-card {
        animation: fadeInUp 0.6s ease-out;
    }
    
    /* Floating particles background effect */
    .particles {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: -1;
    }
    
    .particle {
        position: absolute;
        width: 4px;
        height: 4px;
        background: rgba(255, 255, 255, 0.3);
        border-radius: 50%;
        animation: float 6s ease-in-out infinite;
    }
    
    @keyframes float {
        0%, 100% { transform: translateY(0px) rotate(0deg); }
        50% { transform: translateY(-20px) rotate(180deg); }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Create the login interface to match exactly with the image
    st.markdown("""
    <div class="login-container">
        <div class="login-card">
            <div class="login-header">
                <h1 class="login-title">Log In</h1>
            </div>
            <div class="login-columns">
                <div class="left-column">
                    <!-- Form will be inserted here by Streamlit -->
                </div>
                <div class="right-column">
                    <img src="https://img.freepik.com/free-vector/secure-login-concept-illustration_114360-4582.jpg" alt="Login illustration">
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Display sample credentials with style matching the new design
    with st.expander("Sample Login Credentials", expanded=False):
        st.markdown("""
        <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
            <h4 style="color: #333; font-weight: 600; margin-bottom: 10px;">👨‍💼 Administrator</h4>
            <div style="background: white; padding: 8px 12px; border-radius: 6px; margin-bottom: 5px; border: 1px solid #e0e0e0;">
                Username: admin | Password: admin
            </div>
        </div>
        
        <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
            <h4 style="color: #333; font-weight: 600; margin-bottom: 10px;">👨‍🏫 Teachers/Professors</h4>
            <div style="background: white; padding: 8px 12px; border-radius: 6px; margin-bottom: 5px; border: 1px solid #e0e0e0;">
                Username: emp2024001 | Password: emp2024001
            </div>
            <div style="background: white; padding: 8px 12px; border-radius: 6px; margin-bottom: 5px; border: 1px solid #e0e0e0;">
                Username: emp2024002 | Password: emp2024002
            </div>
        </div>
        
        <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
            <h4 style="color: #333; font-weight: 600; margin-bottom: 10px;">👨‍🎓 Students</h4>
            <div style="background: white; padding: 8px 12px; border-radius: 6px; margin-bottom: 5px; border: 1px solid #e0e0e0;">
                Username: 2024001 | Password: 2024001
            </div>
            <div style="background: white; padding: 8px 12px; border-radius: 6px; margin-bottom: 5px; border: 1px solid #e0e0e0;">
                Username: 2024002 | Password: 2024002
            </div>
        </div>
        
        <div style="background: #e9f0ff; padding: 15px; border-radius: 8px; border-left: 4px solid #4a6cf7;">
            <p style="margin: 0; color: #333; font-size: 14px;">
                <strong>📝 Note:</strong> All passwords match their respective usernames for easy testing.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
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
        # Check if we have users_enhanced instead
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users_enhanced'")
        if cursor.fetchone():
            print("Found users_enhanced table, using it for authentication")
        else:
            st.error("User accounts table not found. Login functionality may be unavailable.")
    
    # Create login form that matches exactly with the image
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Username field
        username = st.text_input(
            "Username", 
            placeholder="Enter your username",
            key="username_input"
        )
        
        # Password field
        password = st.text_input(
            "Password", 
            type="password",
            placeholder="Enter your password",
            key="password_input"
        )
        
        # Forgot password link
        st.markdown('<div style="text-align: right; margin-bottom: 20px;"><a href="#" style="color: #4a6cf7; text-decoration: none; font-size: 14px;">Forgot Password?</a></div>', unsafe_allow_html=True)

        # Login button
        if st.button("Login", use_container_width=True):
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
                    
                st.error("❌ Invalid username or password. Please try again.")

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
    # Apply global CSS
    apply_global_css()
    
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