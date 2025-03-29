"""
Login view module.

This module provides the login interface for the application.
"""
import streamlit as st
from src.core.security import secure_verify_credentials
from src.database.schema import ensure_tables_exist

def initialize_database():
    """Initialize the database for first use"""
    return ensure_tables_exist()

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
                    # First try direct admin check
                    if username.lower() == "admin" and password.lower() == "admin":
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.session_state.user_role = "admin"
                        st.session_state.is_admin = True
                        st.query_params["user_role"] = "admin"
                        st.rerun()
                    else:
                        # Check database
                        success, role = secure_verify_credentials(username, password)
                        if success:
                            st.session_state.logged_in = True
                            st.session_state.username = username
                            st.session_state.user_role = role
                            
                            # Set role-specific flags
                            if role.lower() == "admin":
                                st.session_state.is_admin = True
                                st.query_params["user_role"] = "admin"
                            elif role.lower() == "professor":
                                st.session_state.is_professor = True
                                st.query_params["user_role"] = "professor"
                                
                            st.rerun()
                        else:
                            st.error("Invalid username or password")
        
        # Registration info
        st.info("If you don't have an account, please contact an administrator.")
