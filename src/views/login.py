"""
Login view module with direct access to views.

This module provides the login interface and handles routing to role-based views.
"""
import streamlit as st
import sqlite3
from pathlib import Path

# Database path
DATABASE_PATH = Path('attendance_system.db')

def show_login_view():
    """Show the login interface"""
    st.title("👤 Login to Attendance System")
    
    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Create login form
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login", use_container_width=True)
            
            if submit:
                if not username or not password:
                    st.error("Please enter both username and password")
                else:
                    # Check if credentials are valid (direct database check for simplicity)
                    success, role = verify_credentials(username, password)
                    
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
        
        # Help text with default credentials
        st.info("Default accounts: admin/123, professor/123, student/123")
        
        # Emergency login button
        if st.button("🛠️ Emergency Admin Login", type="secondary"):
            st.session_state.logged_in = True
            st.session_state.username = "admin"
            st.session_state.user_role = "admin"
            st.session_state.is_admin = True
            st.rerun()

def verify_credentials(username, password):
    """Simple credential verification with direct DB access"""
    # Special case for default users
    default_users = {
        "admin": "123",
        "professor": "123", 
        "student": "123"
    }
    
    # Check default users first
    if username in default_users and password == default_users[username]:
        return True, username
    
    # Check database
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT role FROM user_accounts WHERE username = ? AND password = ?",
            (username, password)
        )
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return True, result[0]
        return False, ""
    except Exception as e:
        print(f"Error verifying credentials: {e}")
        return False, ""
