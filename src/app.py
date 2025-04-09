import streamlit as st
# Set page config as the very first Streamlit command
st.set_page_config(
    page_title="Attendance Management System",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="auto"
)

"""
Main Application Entry Point

This module serves as the main entry point for the Attendance Management System.
It handles user authentication, page routing, and session management.

The app provides different views based on the user's role:
- Student: Access to attendance records and personal profile
- Professor: Access to class attendance records and reports
- Admin: Full system management and configuration
"""
import os
import sys
import sqlite3
import time
import importlib
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional
import logging

# Standard library imports
from datetime import datetime

# Local imports - direct module imports
import home
import real_time_prediction
import report
import student_report
import registration_form

# Use direct imports without src prefix
from database_utils import execute_query, execute_query_df
from database_maintenance import repair_attendance_tables
from global_css_handler import apply_global_css, enforce_fixed_padding
from display_patch import patch_display_functions

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Apply display patches
patch_display_functions()

# Database path using pathlib for better cross-platform compatibility
DATABASE_PATH = Path(os.path.dirname(os.path.dirname(__file__))) / 'attendance_system.db'
logger.info(f"Using database at: {DATABASE_PATH.absolute()}")

# Run attendance table repair early in startup
try:
    # First fix schema detection
    from database_utils import get_attendance_records_schema
    logger.info("Pre-initializing attendance records schema...")
    schema_mapping = get_attendance_records_schema()
    logger.info(f"Attendance schema mapping: {schema_mapping}")
    
    # Fix any database issues using the consolidated maintenance module
    repair_attendance_tables()
    logger.info("Database maintenance completed at startup")
except Exception as e:
    logger.error(f"Error during database maintenance: {e}")

# Now import bootstrap tables after ensuring critical tables exist
from bootstrap_tables import bootstrap_essential_tables
bootstrap_essential_tables()  # Run table creation at import time

# Add import for database sync
from database_sync import sync_user_tables

def show_app():
    """Main application entry point"""
    # Apply global CSS immediately at app startup before any other code
    from global_css_handler import apply_global_css, enforce_fixed_padding
    apply_global_css()
    enforce_fixed_padding()
    
    # Ensure database consistency at startup
    from database_sync import sync_user_tables
    sync_user_tables()
    
    # Ensure database is initialized at application start
    if 'database_initialized' not in st.session_state:
        from login import initialize_database
        logger.info("Initializing database from app.py")
        st.session_state.database_initialized = initialize_database()
    
    # Debug user role to help diagnose issues
    logger.info(f"User role detected: {st.session_state.get('user_role', 'None')}")
    logger.info(f"Username: {st.session_state.get('username', 'None')}")
    logger.info(f"Is admin flag: {st.session_state.get('is_admin', False)}")
    logger.info(f"Is professor flag: {st.session_state.get('is_professor', False)}")
    
    # Import persistence manager to ensure data is maintained
    from persistent_session_manager import PersistentSessionManager
    session_manager = PersistentSessionManager()
    session_manager.ensure_session_persistence()
    session_manager.inject_session_js()
    
    # Apply consistent padding immediately at app start
    from global_css_handler import ensure_consistent_padding
    ensure_consistent_padding()
    
    # Fix: Make module reloading more defensive by using try-except
    try:
        # Try to reload the module only if it's available
        import subject_management
        importlib.reload(subject_management)
        logger.info("Successfully reloaded subject_management module")
    except (ImportError, UnboundLocalError):
        # Either the module doesn't exist or it's not in scope
        logger.info("subject_management module not available for reload - will be imported as needed")
    
    # Triple redundancy approach - layer 1: Import and run function
    try:
        from database_utils import ensure_student_profiles_compatibility
        success = ensure_student_profiles_compatibility()
        logger.info(f"Student profiles compatibility setup: {'SUCCESS' if success else 'FAILED'}")
        
    except Exception as e:
        logger.error(f"Error loading student profiles compatibility module: {e}")
    
    # Extra verification - directly check if table exists now
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='student_profiles'")
        table_exists = cursor.fetchone() is not None
        logger.info(f"FINAL CHECK: student_profiles table {'exists' if table_exists else 'STILL MISSING'}")
        
        if not table_exists:
            logger.info("EMERGENCY: Creating student_profiles table as last resort")
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS student_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                name TEXT,
                student_id TEXT,
                section TEXT
            )
            """)
            conn.commit()
    except Exception as e:
        logger.error(f"Error in final table check: {e}")
    finally:
        conn.close()
    
    # Make sure full-width is enforced after login
    st.markdown("""
    <script>
        // Ensure full width layout is enforced even after login
        function enforcePersistentFullWidth() {
            // Override container widths
            document.querySelectorAll('.block-container, .main .block-container').forEach(el => {
                el.style.maxWidth = '100%';
                el.style.width = '100%';
                el.style.paddingLeft = '40px';
                el.style.paddingRight = '40px';
            });
            
            document.querySelectorAll('.element-container, [data-testid="stVerticalBlock"]').forEach(el => {
                el.style.maxWidth = '100%';
                el.style.width = '100%';
            });
        }
        
        // Apply and periodically reapply
        enforcePersistentFullWidth();
        setInterval(enforcePersistentFullWidth, 1000);
        
        // Store preference in localStorage
        localStorage.setItem('fullWidthLayout', 'enabled');
    </script>
    """, unsafe_allow_html=True)
    
    # Get user info from session state
    username = st.session_state.get('username', 'Unknown')
    user_role = st.session_state.get('user_role', 'Unknown')
    
    # FORCE ADMIN ROLE for any admin username for fallback protection
    if username.lower() == "admin" or "admin" in username.lower() or user_role.lower() == "admin" or st.session_state.get('is_admin', False):
        user_role = "admin"
        st.session_state.user_role = "admin"
        st.session_state.is_admin = True
        
        # IMPORTANT: Also set query param to preserve role on refresh
        st.query_params["user_role"] = "admin" 
        logger.info(f"Setting admin role in session and query params for user {username}")
    
    # FORCE PROFESSOR ROLE for any professor username for fallback protection
    elif user_role.lower() == "professor" or st.session_state.get('is_professor', False):
        user_role = "professor"
        st.session_state.user_role = "professor"
        st.session_state.is_professor = True
        
        # IMPORTANT: Also set query param to preserve role on refresh
        st.query_params["user_role"] = "professor"
        logger.info(f"Setting professor role in session and query params for user {username}")
    
    # Debug info for admin login issues
    if username == "admin" and user_role != "admin":
        st.error(f"Login issue detected: Username is 'admin' but role is '{user_role}'. Please contact support.")
    
    # Set up current_user object if not already done
    if 'current_user' not in st.session_state:
        st.session_state.current_user = {
            "username": username,
            "role": user_role,
            "last_login": None
        }
    
    # Get additional user details from database based on role with error handling
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        if user_role == 'student':
            # CRITICAL FIX: First create the table directly if needed - most aggressive approach
            try:
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS student_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    name TEXT,
                    student_id TEXT,
                    section TEXT,
                    email TEXT,
                    phone TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)
                
                # Insert current user if not exists
                cursor.execute("""
                INSERT OR IGNORE INTO student_profiles (username, name) 
                VALUES (?, ?)
                """, (username, username))
                conn.commit()
                logger.info(f"Created or ensured student_profiles table exists with user {username}")
            except Exception as e:
                logger.error(f"Initial table creation error: {e}")
                
            # Then run our compatibility function
            from database_utils import ensure_student_profiles_compatibility
            ensure_student_profiles_compatibility()
            
            # Now check for the table or view
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE (type='table' OR type='view') 
                AND (name='student_profiles' OR name='student_profiles_view' OR name='students')
            """)
            result = cursor.fetchone()
            
            if not result:
                # !!! FIX: Create the table here instead of showing warning !!!
                logger.info("Student profiles table not found in check. Creating it now as last resort.")
                cursor.execute("""
                CREATE TABLE student_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    name TEXT,
                    student_id TEXT,
                    section TEXT,
                    email TEXT,
                    phone TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)
                cursor.execute("""
                INSERT OR IGNORE INTO student_profiles (username, name, student_id, section) 
                VALUES (?, ?, ?, ?)
                """, (username, username, username, 'Default'))
                conn.commit()
                
                # Set default values in session state
                st.session_state['current_user']['student_id'] = username
                st.session_state['current_user']['section'] = 'Default'
                st.session_state['current_user']['full_name'] = username
                
                # IMPORTANT: No warning message displayed to the user
            else:
                # Check if the columns exist
                cursor.execute(f"PRAGMA table_info({result[0]})")
                columns = [info[1].lower() for info in cursor.fetchall()]
                logger.info(f"Columns in {result[0]}: {columns}")
                
                # Construct query with safer approach - using a simple direct query
                try:
                    if 'username' in columns:
                        cursor.execute(f"SELECT * FROM {result[0]} WHERE username = ?", (username,))
                        student_data = cursor.fetchone()
                        if student_data:
                            # Get column indexes for safety
                            column_indexes = {col.lower(): i for i, col in enumerate([info[1] for info in cursor.description])}
                            
                            # Safely get data by column name
                            st.session_state['current_user']['student_id'] = student_data[column_indexes.get('student_id', 0)] if 'student_id' in column_indexes else 'Unknown'
                            st.session_state['current_user']['section'] = student_data[column_indexes.get('section', 0)] if 'section' in column_indexes else 'Unknown'
                            st.session_state['current_user']['full_name'] = student_data[column_indexes.get('name', 0)] if 'name' in column_indexes else username
                        else:
                            # No data for this user, create default values
                            st.session_state['current_user']['student_id'] = 'Unknown'
                            st.session_state['current_user']['section'] = 'Unknown'
                            st.session_state['current_user']['full_name'] = username
                    else:
                        # Use simpler approach if username column missing
                        st.session_state['current_user']['student_id'] = 'Unknown'
                        st.session_state['current_user']['section'] = 'Unknown'
                        st.session_state['current_user']['full_name'] = username
                except Exception as e:
                    logger.error(f"Error retrieving student details: {e}")
                    st.session_state['current_user']['student_id'] = 'Unknown'
                    st.session_state['current_user']['section'] = 'Unknown'
                    st.session_state['current_user']['full_name'] = username
        elif user_role == 'professor':
            # First check if professor_profiles table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='professor_profiles'")
            if cursor.fetchone():
                # Check if the table has the username column
                cursor.execute("PRAGMA table_info(professor_profiles)")
                columns = [info[1].lower() for info in cursor.fetchall()]
                
                try:
                    if "username" in columns and "department" in columns:
                        cursor.execute("""
                            SELECT department FROM professor_profiles WHERE username = ?
                        """, (username,))
                        prof_data = cursor.fetchone()
                        
                        # Add proper null check before accessing tuple index
                        if prof_data and len(prof_data) > 0:
                            st.session_state['current_user']['department'] = prof_data[0]
                        else:
                            # No data found for this professor
                            st.session_state['current_user']['department'] = 'Unknown'
                    else:
                        # Missing required columns
                        st.session_state['current_user']['department'] = 'Unknown'
                except Exception as e:
                    logger.error(f"Error accessing professor data: {e}")
                    st.session_state['current_user']['department'] = 'Unknown'
            else:
                # Silently handle missing professor_profiles table
                st.session_state['current_user']['department'] = 'Unknown'
    except Exception as e:
        logger.error(f"Error retrieving user details: {str(e)}")
        # Don't show warning to the user, just log it
        st.session_state['current_user']['error'] = str(e)
    finally:
        if 'conn' in locals() and conn:
            conn.close()
    
    # Initialize show_sidebar state - now default to TRUE for admin user_accounts
    if 'show_sidebar' not in st.session_state:
        st.session_state.show_sidebar = True if user_role == 'admin' else False
    
    # ADMIN VIEW - Full access to all pages
    if user_role == 'admin':
        try:
            # Import all the required modules for admin users
            import admin_dashboard
            import enhanced_db_explorer
            
            # Create a dictionary mapping page names to their respective functions
            # Include Admin Dashboard in the complete pages dictionary, but we'll filter it from navigation
            all_pages = {
                "Admin Dashboard": admin_dashboard.show_admin_dashboard,
                "Real-Time Recognition": real_time_prediction.show_real_time_prediction,
                "Registration": registration_form.show_registration_form,
                "Database Explorer": enhanced_db_explorer.show_db_explorer
            }
            
            # Create a filtered version for the sidebar navigation (without Admin Dashboard)
            nav_pages = {k: v for k, v in all_pages.items() if k != "Admin Dashboard"}
            
            # Set default page to Database Explorer if not already set or if was Admin Dashboard or Subject Management
            if ('current_page' not in st.session_state 
                or st.session_state.current_page not in all_pages
                or st.session_state.current_page == "Admin Dashboard" 
                or st.session_state.current_page == "Subject Management"):
                st.session_state.current_page = "Database Explorer"
            
            # Always show sidebar for admin
            with st.sidebar:
                # Updated sidebar header with centered style and fixed height
                st.markdown(f"""
                <div class="admin-username-container">
                    <span style="font-size: 20px; line-height: 1;">👤</span>
                    <span class="admin-username-text">{username} (Admin)</span>
                </div>
                """, unsafe_allow_html=True)
                
                # Full-width logout button - CHANGED KEY TO sidebar_logout_primary
                if st.button("🚪 Logout", key="sidebar_logout_primary", use_container_width=True):
                    logout_user()
                
                # Add a subtle divider
                st.markdown("<hr style='margin: 5px 0; opacity: 0.3;'>", unsafe_allow_html=True)
                
                # Create a radio button for navigation - using filtered nav_pages
                current_page = st.session_state.current_page
                # Handle case where current page is Admin Dashboard (not in nav_pages)
                selected_index = list(nav_pages.keys()).index(current_page) if current_page in nav_pages else 0
                
                selection = st.radio("Navigation", list(nav_pages.keys()), index=selected_index)
                
                # Update current page
                if selection != st.session_state.current_page:
                    st.session_state.current_page = selection
                    st.rerun()
            
            # Create simplified top navigation bar
            st.markdown(f"## 👤 {username} - {st.session_state.current_page}")
            
            # Call the selected page function - use all_pages to include Admin Dashboard
            all_pages[st.session_state.current_page]()
            
            # Important - Return here so we don't hit the fallback code below
            return
            
        except (ImportError, AttributeError) as e:
            # Fallback admin dashboard if there's an issue with the modules
            st.error(f"Error loading admin modules: {str(e)}")
            # Continue with the fallback admin dashboard below
            
        # This is the fallback code that runs if the primary admin view fails
        try:
            # Try to import required admin modules - if they fail, we'll handle it
            import enhanced_db_explorer
            
            # Create a dictionary mapping page names to their respective functions
            pages = {
                "Admin Dashboard": admin_dashboard.show_admin_dashboard,  # Add admin dashboard as first option
                "Real-Time Recognition": real_time_prediction.show_real_time_prediction,
                "Registration": registration_form.show_registration_form,
                "Database Explorer": enhanced_db_explorer.show_db_explorer
            }
            
            # Set default page to Admin Dashboard - ALWAYS for admin users
            st.session_state.current_page = "Admin Dashboard"
            
            # Always show sidebar for admin (remove toggle button)
            with st.sidebar:
                # Updated sidebar header with centered style
                st.markdown(f"""
                <div class="admin-username-container">
                    <span style="font-size: 24px;">👤</span>
                    <span class="admin-username-text">{username} (Admin)</span>
                </div>
                """, unsafe_allow_html=True)
                
                # Full-width logout button - CHANGED KEY TO sidebar_logout_fallback
                if st.button("🚪 Logout", key="sidebar_logout_fallback", use_container_width=True):
                    logout_user()
                
                # Add a subtle divider
                st.markdown("<hr style='margin: 5px 0; opacity: 0.3;'>", unsafe_allow_html=True)
                
                # Get the index for the current page
                current_index = list(pages.keys()).index(st.session_state.current_page) if st.session_state.current_page in pages else 0
                
                # Create a radio button for navigation
                selection = st.radio("", list(pages.keys()), index=current_index)
                
                # Update current page
                if selection != st.session_state.current_page:
                    st.session_state.current_page = selection
                    st.rerun()
            
            # Create simplified top navigation bar (no menu toggle needed)
            st.markdown(f"## 👤 {username} - {st.session_state.current_page}")
            
            # Call the selected page function
            pages[st.session_state.current_page]()
        
        except (ImportError, AttributeError) as e:
            # Fallback admin dashboard if there's an issue with the modules
            st.title("Admin Dashboard")
            st.warning(f"Some admin modules could not be loaded: {str(e)}")
            
            # Show basic admin options that don't require the missing modules
            st.subheader("Basic Admin Functions")
            
            # Admin tabs for different areas
            admin_tabs = st.tabs(["User Management", "System Status", "Diagnostics"])
            
            with admin_tabs[0]:
                st.header("User Management")
                st.write("Here you can manage users in the system.")
                
                # Display all users from the database
                conn = sqlite3.connect(DATABASE_PATH)
                try:
                    users_df = execute_query_df("SELECT username, role FROM user_accounts ORDER BY role, username")
                    st.dataframe(users_df)
                except Exception as e:
                    st.error(f"Error loading users: {e}")
                finally:
                    conn.close()
            
            with admin_tabs[1]:
                st.header("System Status")
                st.write("Database table record counts:")
                
                conn = sqlite3.connect(DATABASE_PATH)
                try:
                    tables = ["user_accounts", "student_profiles", "professor_profiles", "attendance_records"]
                    counts = {}
                    for table in tables:
                        try:
                            count_df = execute_query_df(f"SELECT COUNT(*) as count FROM {table}")
                            counts[table] = count_df['count'][0]
                        except:
                            counts[table] = "Error"
                    
                    counts_df = pd.DataFrame(list(counts.items()), columns=['Table', 'Records'])
                    st.dataframe(counts_df)
                    
                except Exception as e:
                    st.error(f"Error checking database: {e}")
                finally:
                    conn.close()
            
            with admin_tabs[2]:
                st.header("System Diagnostics")
                st.write("Session state variables:")
                st.json({k: v for k, v in st.session_state.items() if k != 'current_user'})
                
                # Add a button to reset session state
                if st.button("Reset Session State"):
                    for key in list(st.session_state.keys()):
                        if key != 'logged_in' and key != 'username' and key != 'user_role':
                            del st.session_state[key]
                    st.success("Session state reset (except login information)")
                    st.rerun()
                
    # PROFESSOR VIEW - Only access to Reports page with no sidebar
    elif user_role == 'professor':
        # Use combined CSS + JS approach for consistent padding
        st.markdown("""
        <script>
        // Hide sidebar for professor user_accounts with !important to prevent CSS conflicts
        document.addEventListener('DOMContentLoaded', function() {
            const style = document.createElement('style');
            style.innerHTML = `
                section[data-testid="stSidebar"] { 
                    display: none !important;
                    width: 0px !important;
                }
            `;
            document.head.appendChild(style);
            
            // Force padding on all containers
            function enforcePadding() {
                const containers = document.querySelectorAll('.block-container, [data-testid="stAppViewBlockContainer"] div.block-container');
                containers.forEach(function(container) {
                    container.style.setProperty('padding-left', '80px', 'important');
                    container.style.setProperty('padding-right', '80px', 'important');
                    container.style.setProperty('max-width', 'unset', 'important');
                }
            }
            
            // Apply immediately and repeatedly
            enforcePadding();
            setTimeout(enforcePadding, 100);
            setTimeout(enforcePadding, 500);
        });
        </script>
        """, unsafe_allow_html=True)
        
        # IMPROVED LAYOUT: Put title, username and buttons all in the same container - MATCHING STUDENT LAYOUT
        st.markdown('<div style="margin-top: 0; padding-top: 0;">', unsafe_allow_html=True)
        top_col1, top_col2 = st.columns([3, 2])
        
        # Put the dashboard title in the first column
        with top_col1:
            st.markdown("""
            <div class="dashboard-header">
                <h2 class="dashboard-title">📚 Teacher Dashboard</h2>
            </div>
            """, unsafe_allow_html=True)
        
        # User info and buttons in column 2
        with top_col2:
            # Username display with right alignment - USING THE SAME STYLING AS STUDENT
            st.markdown(f"""
            <div class="username-container">
                <div class="username-text" style="font-size: 0.8rem;">
                    👤 {username} | Professor
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Two buttons side by side - MATCHES STUDENT LAYOUT
            button_col1, button_col2 = st.columns(2)
            
            with button_col1:
                # Refresh button with same style as logout
                if st.button("🔄 Refresh", key="prof_refresh", use_container_width=True):
                    st.rerun()
            
            with button_col2:
                # Logout button
                if st.button("🚪 Logout", key="prof_logout", use_container_width=True):
                    logout_user()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Always show reports page for professor role
        report.show_report()
    
    # STUDENT VIEW - Only access to Student Report
    else:
        # Apply the same sidebar hiding technique and consistent padding
        st.markdown("""
        <script>
        // Hide sidebar for student user_accounts with !important to prevent CSS conflicts
        document.addEventListener('DOMContentLoaded', function() {
            const style = document.createElement('style');
            style.innerHTML = `
                section[data-testid="stSidebar"] { 
                    display: none !important;
                    width: 0px !important;
                }
            `;
            document.head.appendChild(style);
            
            // Force padding on all containers
            function enforcePadding() {
                const containers = document.querySelectorAll('.block-container, [data-testid="stAppViewBlockContainer"] div.block-container');
                containers.forEach(function(container) {
                    container.style.setProperty('padding-left', '80px', 'important');
                    container.style.setProperty('padding-right', '80px', 'important');
                    container.style.setProperty('max-width', 'unset', 'important');
                }
            }
            
            // Apply immediately and repeatedly
            enforcePadding();
            setTimeout(enforcePadding, 100);
            setTimeout(enforcePadding, 500);
        });
        </script>
        """, unsafe_allow_html=True)
        
        # Student only sees their attendance
        student_report.show_student_report()

# Helper function for logout
def logout_user():
    # Clear session state
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    # Clear query params
    st.query_params.clear()
    st.rerun()

if __name__ == "__main__":
    # This block only runs when app.py is executed directly
    st.set_page_config(layout="wide")
    
    # CRITICAL: Import and run persistent session manager FIRST
    from persistent_session_manager import PersistentSessionManager
    session_manager = PersistentSessionManager()
    session_manager.ensure_session_persistence()
    
    # Continue with existing code...
    # CRITICAL: Import role_session_persistence as the very first step
    import role_session_persistence
    role_session_persistence.ensure_role_persistence()
    
    # CRITICAL: Restore roles from query params if present
    if "user_role" in st.query_params:
        role = st.query_params["user_role"]
        st.session_state.user_role = role
        
        if role == "admin":
            st.session_state.is_admin = True
            logger.info("Restored admin role from query parameters")
        elif role == "professor":
            st.session_state.is_professor = True
            logger.info("Restored professor role from query parameters")
    
    # Also restore admin role if username contains 'admin'
    if "username" in st.query_params and "admin" in st.query_params["username"].lower():
        st.session_state.user_role = "admin"
        st.session_state.is_admin = True
        logger.info(f"Set admin role based on username: {st.query_params['username']}")
    
    # Setup admin tables to ensure they exist
    try:
        from setup_admin_tables import setup_admin_tables
        setup_admin_tables()
    except Exception as e:
        logger.warning(f"Warning: Could not set up admin tables: {e}")
    
    # Setup student tables to ensure they exist
    try:
        from setup_student_tables import setup_student_tables
        # Run in non-interactive mode (not asking for sample data)
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Check if student_profiles exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='student_profiles'")
        if not cursor.fetchone():
            logger.info("Creating student_profiles table...")
            setup_student_tables()
        conn.close()
    except Exception as e:
        logger.warning(f"Warning: Could not set up student tables: {e}")
    
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if st.session_state.logged_in:
        show_app()
    else:
        import login
        login.main()