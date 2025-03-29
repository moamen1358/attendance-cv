"""
Admin view module.

This module provides the admin dashboard functionality.
"""
import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path

# Database path
DATABASE_PATH = Path('attendance_system.db')

def show_admin_view():
    """Show the admin interface"""
    st.title("📊 Admin Dashboard")
    
    # Sidebar for navigation
    st.sidebar.title("Admin Navigation")
    
    # Get username from session state
    username = st.session_state.get('username', 'Admin')
    st.sidebar.markdown(f"### Welcome, {username}")
    
    # Logout button
    if st.sidebar.button("🚪 Logout"):
        # Clear session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
    
    # Navigation options
    pages = ["Dashboard", "User Management", "Subject Management", "System Settings"]
    selection = st.sidebar.radio("Navigate to", pages)
    
    # Show selected page
    if selection == "Dashboard":
        show_admin_dashboard()
    elif selection == "User Management":
        show_user_management()
    elif selection == "Subject Management":
        show_subject_management()
    elif selection == "System Settings":
        show_system_settings()

def show_admin_dashboard():
    """Show admin dashboard with key metrics"""
    st.header("System Overview")
    
    # Display key metrics
    col1, col2, col3 = st.columns(3)
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        
        # Count users
        with col1:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM user_accounts WHERE role='student'")
            student_count = cursor.fetchone()[0]
            st.metric("Total Students", student_count)
        
        # Count professors
        with col2:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM user_accounts WHERE role='professor'")
            professor_count = cursor.fetchone()[0]
            st.metric("Total Professors", professor_count)
        
        # Count subjects
        with col3:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM subjects")
            subject_count = cursor.fetchone()[0]
            st.metric("Total Subjects", subject_count)
        
        conn.close()
    except Exception as e:
        st.error(f"Error loading metrics: {e}")
    
    # Recent activity
    st.subheader("Recent Activity")
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        df = pd.read_sql_query(
            "SELECT username, timestamp FROM attendance_records ORDER BY timestamp DESC LIMIT 10",
            conn
        )
        conn.close()
        st.dataframe(df)
    except Exception as e:
        st.info("No recent activity found")

def show_user_management():
    """Show user management interface"""
    st.header("User Management")
    st.info("User management interface will be implemented here.")

def show_subject_management():
    """Show subject management interface"""
    st.header("Subject Management")
    st.info("Subject management interface will be implemented here.")

def show_system_settings():
    """Show system settings interface"""
    st.header("System Settings")
    st.info("System settings will be implemented here.")
