"""
Main Application Entry Point

This module serves as the main entry point for the Attendance Management System.
It handles user authentication, page routing, and session management.

The app provides different views based on the user's role:
- Student: Access to attendance records and personal profile
- Professor: Access to class attendance records and reports
- Admin: Full system management and configuration
"""
import streamlit as st
import os
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Local imports
from src.core.session_manager import session_manager, ensure_role_persistence
from src.database.schema import ensure_tables_exist, validate_schema
from src.database.maintenance import repair_attendance_tables
from src.views import get_view_for_role
from src.ui.styles import apply_global_css

# Database path
DATABASE_PATH = Path('attendance_system.db')

def initialize_application():
    """Initialize the application"""
    logger.info("Initializing application")
    
    # Ensure critical tables exist
    ensure_tables_exist()
    
    # Validate and fix schema as needed
    validate_schema()
    
    # Repair any database issues
    repair_attendance_tables()
    
    logger.info("Application initialization complete")

def show_app():
    """Main application entry point"""
    # Apply global CSS first
    apply_global_css()
    
    # Ensure session persistence
    session_manager.ensure_session_persistence()
    
    # Ensure role persistence
    ensure_role_persistence()
    
    # Get user info from session state
    username = st.session_state.get('username', 'Unknown')
    user_role = st.session_state.get('user_role', 'Unknown')
    
    # Handle login logic
    if not st.session_state.get('logged_in', False):
        from src.views.login import show_login_view
        show_login_view()
        return
    
    # Log the user role
    logger.info(f"Showing view for user {username} with role {user_role}")
    
    # Display appropriate view based on user role
    view_func = get_view_for_role(user_role)
    view_func()

if __name__ == "__main__":
    # Set page configuration
    st.set_page_config(
        page_title="Attendance Management System",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="auto"
    )
    
    # Initialize the application
    initialize_application()
    
    # Show the app
    show_app()
