"""
Login module for the attendance system.

This module handles user authentication and provides the login interface.
"""
import streamlit as st
import sqlite3
import logging

# Import app module
from src.app import get_db_connection

# Setup logging
logger = logging.getLogger(__name__)

def verify_credentials(username, password):
    """
    Verify user credentials against the database
    
    Args:
        username (str): Username to verify
        password (str): Password to verify
    
    Returns:
        tuple: (success, role)
    """
    # Special case for admin account
    if username == "admin" and password == "admin":
        return True, "admin"
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Simple password check (plain text)
        cursor.execute(
            "SELECT id, role FROM user_accounts WHERE username = ? AND password = ?",
            (username, password)
        )
        user = cursor.fetchone()
        
        if not user:
            return False, ""
        
        user_id, role = user
        
        # Update last login time
        cursor.execute(
            "UPDATE user_accounts SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
            (user_id,)
        )
        conn.commit()
        
        return True, role
            
    except Exception as e:
        logger.error(f"Error verifying credentials: {e}")
        return False, ""
    finally:
        conn.close()

def show_login_view():
    """Show the login interface"""
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.title("👤 Login")
        
        # Create login form
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login", use_container_width=True)
            
            if submit:
                if not username or not password:
                    st.error("Please enter both username and password")
                else:
                    success, role = verify_credentials(username, password)
                    if success:
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.session_state.user_role = role
                        
                        # Set role-specific flags
                        if role.lower() == "admin":
                            st.session_state.is_admin = True
                        elif role.lower() == "professor":
                            st.session_state.is_professor = True
                            
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
        
        # Registration info
        st.info("If you don't have an account, please contact an administrator.")