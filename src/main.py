"""
Main Application Entry Point

This module serves as the main entry point for the Attendance Management System.
It handles user authentication, page routing, and session management.
"""
import streamlit as st
import os
import sys
import logging
from pathlib import Path

# Add parent directory to Python path to find the src module
parent_dir = str(Path(__file__).parent.parent.absolute())
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
    print(f"Added {parent_dir} to Python path")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Now imports will work properly
from src.database.schema import ensure_tables_exist
from src.database.maintenance import repair_attendance_tables

# Database path
DATABASE_PATH = Path('attendance_system.db')

def initialize_application():
    """Initialize the application"""
    logger.info("Initializing application")
    
    # Ensure database exists
    if not DATABASE_PATH.exists():
        # Import bootstrap functions only if needed
        ensure_tables_exist()
        logger.info("Created new database")
        
    logger.info("Application initialization complete")

def show_app():
    """Main application entry point"""
    # Get user info from session state
    username = st.session_state.get('username', 'Unknown')
    user_role = st.session_state.get('user_role', 'Unknown')
    
    # Handle login logic
    if not st.session_state.get('logged_in', False):
        # Import only when needed to avoid circular imports
        from src.views.login import show_login_view
        show_login_view()
        return
    
    # Log the user role
    logger.info(f"Showing view for user {username} with role {user_role}")
    
    # Display appropriate view based on user role
    if user_role.lower() == 'admin':
        # Import only when needed
        import src.views.admin as admin_view
        admin_view.show_admin_view()
    elif user_role.lower() == 'professor':
        # Check if professor view exists
        try:
            import src.views.professor as professor_view
            professor_view.show_professor_view()
        except ImportError:
            # Fallback to using report directly if professor view not found
            import report
            report.show_report()
    else:
        # Try to import student view, with fallback
        try:
            import src.views.student as student_view
            student_view.show_student_view()
        except ImportError:
            import student_report
            student_report.show_student_report()

if __name__ == "__main__":
    # Set page configuration
    st.set_page_config(
        page_title="Attendance Management System",
        page_icon="📊",
        layout="wide"
    )
    
    # Initialize the application
    initialize_application()
    
    # Show the app
    show_app()
