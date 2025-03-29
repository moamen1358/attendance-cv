"""
Admin view module.

This module provides views for admin users:
- Dashboard overview
- User management
- System settings
- Database management
"""
import streamlit as st
import pandas as pd
from src.database import execute_query_df
from src.ui.components import create_metric_card, create_sidebar_navigation

def show_admin_view():
    """Show the admin interface"""
    # Create pages dictionary
    pages = {
        "Admin Dashboard": show_admin_dashboard,
        "Subject Management": show_subject_management,
        "User Management": show_user_management,
        "Database Explorer": show_database_explorer,
        "System Settings": show_system_settings
    }
    
    # Set default page if not set
    if 'current_page' not in st.session_state or st.session_state.current_page not in pages:
        st.session_state.current_page = "Admin Dashboard"
    
    # Create navigation
    selection = create_sidebar_navigation(pages, st.session_state.current_page)
    
    # Update page if changed
    if selection != st.session_state.current_page:
        st.session_state.current_page = selection
        st.rerun()
    
    # Show the selected page
    pages[st.session_state.current_page]()

def show_admin_dashboard():
    """Show the admin dashboard"""
    st.title("📊 Admin Dashboard")
    
    # Display system metrics in a row
    col1, col2, col3 = st.columns(3)
    
    with col1:
        try:
            student_count = execute_query_df("SELECT COUNT(*) as count FROM user_accounts WHERE role = 'student'")['count'][0]
        except:
            student_count = 0
        create_metric_card(student_count, "Total Students", "#4CAF50")
    
    with col2:
        try:
            subject_count = execute_query_df("SELECT COUNT(*) as count FROM subjects")['count'][0]
        except:
            subject_count = 0
        create_metric_card(subject_count, "Total Subjects", "#2196F3")
    
    with col3:
        try:
            attendance_count = execute_query_df("""
                SELECT COUNT(*) as count FROM attendance_records 
                WHERE DATE(timestamp) = DATE('now')
            """)['count'][0]
        except:
            attendance_count = 0
        create_metric_card(attendance_count, "Today's Attendance", "#FFC107")
    
    # Recent activity
    st.subheader("Recent Activity")
    
    try:
        recent_activity = execute_query_df("""
            SELECT username, timestamp, 'Attendance' as activity_type
            FROM attendance_records
            ORDER BY timestamp DESC
            LIMIT 10
        """)
        st.dataframe(recent_activity, use_container_width=True)
    except Exception as e:
        st.error(f"Could not load recent activity: {e}")

def show_subject_management():
    """Show subject management interface"""
    st.title("📚 Subject Management")
    
    # Import the dedicated subject management module
    import subject_management
    
    # Call the function from the module
    subject_management.show_subject_management()

def show_user_management():
    """Show user management interface"""
    st.title("👥 User Management")
    
    # Create tabs for different user types
    user_tabs = st.tabs(["All Users", "Students", "Professors", "Admins"])
    
    # All Users tab
    with user_tabs[0]:
        try:
            users = execute_query_df("""
                SELECT username, role, last_login
                FROM user_accounts
                ORDER BY role, username
            """)
            st.dataframe(users, use_container_width=True)
        except Exception as e:
            st.error(f"Could not load users: {e}")
    
    # Students tab  
    with user_tabs[1]:
        try:
            students = execute_query_df("""
                SELECT ua.username, sp.name, sp.student_id, sp.section
                FROM user_accounts ua
                LEFT JOIN student_profiles sp ON ua.username = sp.username
                WHERE ua.role = 'student'
                ORDER BY sp.name
            """)
            st.dataframe(students, use_container_width=True)
        except Exception as e:
            st.error(f"Could not load students: {e}")
    
    # Professors tab
    with user_tabs[2]:
        try:
            professors = execute_query_df("""
                SELECT ua.username, pp.name, pp.department
                FROM user_accounts ua
                LEFT JOIN professor_profiles pp ON ua.username = pp.username
                WHERE ua.role = 'professor'
                ORDER BY pp.name
            """)
            st.dataframe(professors, use_container_width=True)
        except Exception as e:
            st.error(f"Could not load professors: {e}")
    
    # Admins tab
    with user_tabs[3]:
        try:
            admins = execute_query_df("""
                SELECT username, last_login
                FROM user_accounts
                WHERE role = 'admin'
                ORDER BY username
            """)
            st.dataframe(admins, use_container_width=True)
        except Exception as e:
            st.error(f"Could not load admins: {e}")

def show_database_explorer():
    """Show database explorer interface"""
    st.title("🔍 Database Explorer")
    
    # Import the database explorer module
    import enhanced_db_explorer
    
    # Call the function from the module
    enhanced_db_explorer.show_db_explorer()

def show_system_settings():
    """Show system settings interface"""
    st.title("⚙️ System Settings")
    
    # Create tabs for different settings
    settings_tabs = st.tabs(["General", "Backup & Restore", "Logging", "About"])
    
    # General settings tab
    with settings_tabs[0]:
        st.subheader("General Settings")
        
        # Load current settings
        try:
            settings = execute_query_df("SELECT key, value, description FROM system_config")
            # Convert to dict for easier access
            settings_dict = {row['key']: row['value'] for _, row in settings.iterrows()}
        except Exception as e:
            st.error(f"Could not load settings: {e}")
            settings_dict = {}
        
        # Display settings form
        with st.form("general_settings"):
            # Auto backup interval
            auto_backup = st.number_input(
                "Automatic backup interval (hours)",
                min_value=1,
                max_value=168,
                value=int(settings_dict.get('auto_backup_interval', 24))
            )
            
            # Backup retention days
            retention_days = st.number_input(
                "Backup retention period (days)",
                min_value=1,
                max_value=365,
                value=int(settings_dict.get('backup_retention_days', 7))
            )
            
            # Password security
            password_security = st.checkbox(
                "Enable enhanced password security",
                value=settings_dict.get('enable_password_security', 'true').lower() == 'true'
            )
            
            # Debug logging
            debug_logging = st.checkbox(
                "Enable detailed debug logging",
                value=settings_dict.get('enable_debug_logs', 'false').lower() == 'true'
            )
            
            # Submit button
            submit = st.form_submit_button("Save Settings")
            
            if submit:
                try:
                    # Update settings in database
                    conn = st.connection('sqlite', type='sql', url='attendance_system.db')
                    
                    # Update each setting
                    conn.session.execute(
                        "UPDATE system_config SET value = ? WHERE key = 'auto_backup_interval'",
                        (str(auto_backup),)
                    )
                    conn.session.execute(
                        "UPDATE system_config SET value = ? WHERE key = 'backup_retention_days'",
                        (str(retention_days),)
                    )
                    conn.session.execute(
                        "UPDATE system_config SET value = ? WHERE key = 'enable_password_security'",
                        (str(password_security).lower(),)
                    )
                    conn.session.execute(
                        "UPDATE system_config SET value = ? WHERE key = 'enable_debug_logs'",
                        (str(debug_logging).lower(),)
                    )
                    
                    st.success("Settings saved successfully")
                except Exception as e:
                    st.error(f"Error saving settings: {e}")
    
    # Backup & Restore tab
    with settings_tabs[1]:
        st.subheader("Backup & Restore")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("Create a new database backup")
            if st.button("Create Backup Now", use_container_width=True):
                try:
                    from src.backup_manager import BackupManager
                    backup_mgr = BackupManager()
                    success, message, path = backup_mgr.create_backup()
                    if success:
                        st.success(f"Backup created: {os.path.basename(path)}")
                    else:
                        st.error(message)
                except Exception as e:
                    st.error(f"Error creating backup: {e}")
        
        with col2:
            st.write("Clean up old backup files")
            if st.button("Remove Old Backups", use_container_width=True):
                try:
                    from src.backup_manager import BackupManager
                    backup_mgr = BackupManager()
                    count = backup_mgr.cleanup_old_backups()
                    st.success(f"Removed {count} old backup files")
                except Exception as e:
                    st.error(f"Error cleaning up backups: {e}")
    
    # Logging tab
    with settings_tabs[2]:
        st.subheader("Log Viewer")
        
        log_file = 'app.log'
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                logs = f.readlines()
                if logs:
                    # Show most recent logs first
                    st.code(''.join(logs[-100:]))
                else:
                    st.info("Log file is empty")
        else:
            st.info("No log file found")
    
    # About tab
    with settings_tabs[3]:
        st.subheader("About This System")
        
        st.markdown("""
        ### Attendance Management System
        
        Version 1.0.0
        
        This system provides comprehensive attendance management with face recognition:
        - Student attendance tracking
        - Real-time attendance reporting
        - Administrator dashboard
        - Database management
        
        © 2023 Your Organization
        """)
