"""
Login module for the Attendance Management System.
Handles user authentication against the user_accounts table.
"""
import streamlit as st
import sqlite3
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database path
DATABASE_PATH = Path('attendance_system.db')

def get_db_connection():
    """Get a connection to the database"""
    return sqlite3.connect(DATABASE_PATH)

def fix_user_accounts_schema():
    """
    Ensure the user_accounts table has the necessary columns
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # First check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_accounts'")
        if not cursor.fetchone():
            # Create the table
            cursor.execute("""
            CREATE TABLE user_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL,
                last_login TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            logger.info("Created user_accounts table")
            
            # Add default users
            cursor.execute("""
            INSERT INTO user_accounts (username, password, role) VALUES 
            ('admin', 'admin', 'admin'),
            ('professor', 'professor', 'professor'),
            ('student', 'student', 'student')
            """)
            logger.info("Added default users")
            conn.commit()
            return True
            
        # Check if last_login column exists
        cursor.execute("PRAGMA table_info(user_accounts)")
        columns = [col[1].lower() for col in cursor.fetchall()]
        
        if 'last_login' not in columns:
            # Add the missing column
            cursor.execute("ALTER TABLE user_accounts ADD COLUMN last_login TIMESTAMP")
            logger.info("Added last_login column to user_accounts table")
            conn.commit()
            
        return True
    except Exception as e:
        logger.error(f"Error fixing schema: {e}")
        return False
    finally:
        conn.close()

def verify_credentials(username, password):
    """
    Verify user credentials directly with the database
    
    Args:
        username: The username to check
        password: The password to check
        
    Returns:
        tuple: (success, role, error_message)
    """
    # Special hard-coded credentials for emergency access
    if username == "admin" and password == "admin":
        return True, "admin", None
    if username == "professor" and password == "professor":
        return True, "professor", None
    if username == "student" and password == "student":
        return True, "student", None
    
    # Fix schema before accessing the database
    fix_user_accounts_schema()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if the user exists with matching password
        cursor.execute(
            "SELECT role FROM user_accounts WHERE username = ? AND password = ?", 
            (username, password)
        )
        result = cursor.fetchone()
        
        if result:
            role = result[0]
            
            # Try to update last login time - but don't fail if column doesn't exist
            try:
                cursor.execute(
                    "UPDATE user_accounts SET last_login = ? WHERE username = ?",
                    (datetime.now().isoformat(), username)
                )
                conn.commit()
            except sqlite3.OperationalError as e:
                # Column may not exist - log but don't fail login
                logger.warning(f"Could not update last_login: {e}")
                conn.rollback()
            
            logger.info(f"Successful login for user {username} with role {role}")
            return True, role, None
        else:
            return False, None, "Invalid username or password"
            
    except Exception as e:
        logger.error(f"Database error during login: {e}")
        return False, None, "Internal server error - please try again"
    finally:
        conn.close()

def initialize_database():
    """Ensure default users exist in the database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Fix the schema first
        fix_user_accounts_schema()
        
        # Check if any users exist
        cursor.execute("SELECT COUNT(*) FROM user_accounts")
        user_count = cursor.fetchone()[0]
        
        if user_count == 0:
            # Add default users
            cursor.execute("""
            INSERT INTO user_accounts (username, password, role) VALUES 
            ('admin', 'admin', 'admin'),
            ('professor', 'professor', 'professor'),
            ('student', 'student', 'student')
            """)
            conn.commit()
            logger.info("Added default users")
        
        return True
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return False
    finally:
        conn.close()

def main():
    """Main login function"""
    st.title("📚 Attendance System Login")
    
    # Initialize database without showing errors to users
    try:
        initialize_database()
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
    
    # Add a subtle background
    st.markdown("""
    <style>
    .stApp {
        background-color: #f5f7fa;
        background-image: linear-gradient(315deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Centered login form with improved styling
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 20px;">
            <h2>👤 Login</h2>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            
            submit_col1, submit_col2 = st.columns([3, 1])
            with submit_col1:
                submit = st.form_submit_button("Login", use_container_width=True)
            with submit_col2:
                reset = st.form_submit_button("Reset", use_container_width=True)
                
            if submit:
                if not username or not password:
                    st.error("Please enter both username and password")
                else:
                    # Verify credentials with error handling
                    success, role, error = verify_credentials(username, password)
                    
                    if success:
                        # Set session state
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.session_state.user_role = role
                        
                        if role.lower() == "admin":
                            st.session_state.is_admin = True
                        elif role.lower() == "professor":
                            st.session_state.is_professor = True
                        
                        # Save role in query parameters for persistence
                        st.query_params["user_role"] = role
                        st.query_params["username"] = username
                        
                        # Force reload to show the authenticated view
                        st.rerun()
                    else:
                        st.error(error or "Invalid username or password")
        
        # Help box            
        with st.expander("Need Help?"):
            st.info("Default accounts: admin/admin, professor/professor, student/student")
            
        # Emergency admin login button (only for recovery)
        if st.button("🛠️ Emergency Admin Access", type="secondary"):
            st.session_state.logged_in = True
            st.session_state.username = "admin"
            st.session_state.user_role = "admin" 
            st.session_state.is_admin = True
            st.query_params["user_role"] = "admin"
            st.query_params["username"] = "admin"
            st.rerun()

if __name__ == "__main__":
    main()