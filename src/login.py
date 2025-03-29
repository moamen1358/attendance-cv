"""
Login module for the Attendance Management System.
"""
import streamlit as st
import sqlite3
import logging
from pathlib import Path

# Import page config first to prevent errors
from src.page_config import apply_page_config

# Import core modules
from src.core.security import secure_verify_credentials

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database path
DATABASE_PATH = Path('attendance_system.db')

def get_db_connection():
    """Get a connection to the database"""
    return sqlite3.connect(DATABASE_PATH)

def initialize_database():
    """Initialize the database for first use"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create tables if they don't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL,
        last_login TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Check if admin user exists
    cursor.execute("SELECT * FROM user_accounts WHERE username = 'admin'")
    if not cursor.fetchone():
        # Create default admin user
        cursor.execute("INSERT INTO user_accounts (username, password, role) VALUES (?, ?, ?)",
                      ('admin', 'admin', 'admin'))
    
    conn.commit()
    conn.close()
    return True

def main():
    """Main login function"""
    st.title("👤 Login to Attendance System")
    
    # Create login form
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login", use_container_width=True)
        
        if submit:
            if not username or not password:
                st.error("Please enter both username and password")
            else:
                # Check credentials
                success, role = secure_verify_credentials(username, password)
                
                if success:
                    # Set session state
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.user_role = role
                    
                    if role.lower() == "admin":
                        st.session_state.is_admin = True
                    elif role.lower() == "professor":
                        st.session_state.is_professor = True
                    
                    # Force reload to show the authenticated view
                    st.rerun()
                else:
                    st.error("Invalid username or password")
    
    # Help text
    st.info("Default accounts: admin/123, professor/123, student/123")
    
    # Emergency admin login button
    if st.button("🛠️ Emergency Admin Login", type="secondary"):
        st.session_state.logged_in = True
        st.session_state.username = "admin"
        st.session_state.user_role = "admin"
        st.session_state.is_admin = True
        st.rerun()

if __name__ == "__main__":
    # Apply page configuration
    apply_page_config()
    main()