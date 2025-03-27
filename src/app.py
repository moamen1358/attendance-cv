import streamlit as st
import home
import real_time_prediction
import report
import student_report
import registration_form
import subject_management
import sqlite3
from database_utils import execute_query, execute_query_df
import time
from global_css_handler import apply_global_css, enforce_fixed_padding
import enhanced_db_explorer
import admin_dashboard
import importlib  # Add this import

def show_app():
    # Ensure database is initialized at application start
    if 'database_initialized' not in st.session_state:
        from src.login import initialize_database
        print("Initializing database from app.py")
        st.session_state.database_initialized = initialize_database()
    
    # Debug user role to help diagnose issues
    print(f"User role detected: {st.session_state.get('user_role', 'None')}")
    print(f"Username: {st.session_state.get('username', 'None')}")
    print(f"Is admin flag: {st.session_state.get('is_admin', False)}")
    print(f"Is professor flag: {st.session_state.get('is_professor', False)}")
    
    # Import persistence manager to ensure data is maintained
    from persistent_session_manager import PersistentSessionManager
    session_manager = PersistentSessionManager()
    session_manager.ensure_session_persistence()
    session_manager.inject_session_js()
    
    # Apply consistent padding immediately at app start
    from global_css_handler import ensure_consistent_padding
    ensure_consistent_padding()
    
    # Force reload the database_utils module to ensure we get the latest version
    import src.database_utils
    importlib.reload(src.database_utils)
    
    # Now import the function after reloading the module
    from src.database_utils import ensure_student_profiles_compatibility
    ensure_student_profiles_compatibility()
    
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
        print(f"Setting admin role in session and query params for user {username}")
    
    # FORCE PROFESSOR ROLE for any professor username for fallback protection
    elif user_role.lower() == "professor" or st.session_state.get('is_professor', False):
        user_role = "professor"
        st.session_state.user_role = "professor"
        st.session_state.is_professor = True
        
        # IMPORTANT: Also set query param to preserve role on refresh  
        st.query_params["user_role"] = "professor"
        print(f"Setting professor role in session and query params for user {username}")
    
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
        conn = sqlite3.connect('attendance_system.db')
        cursor = conn.cursor()
        
        if user_role == 'student':
            # First check if student profiles exist as a table or a view
            execute_query("SELECT name FROM sqlite_master WHERE (type='table' OR type='view') AND (name='student_profiles' OR name='student_profiles_view')")
            result = cursor.fetchone()
            
            if not result:
                st.warning("Student profiles table not found. Some features may be limited.")
            else:
                # Use the found table or view name
                table_name = result[0]
                
                # Check if the columns exist
                execute_query(f"PRAGMA table_info({table_name})")
                columns = [info[1] for info in cursor.fetchall()]
                
                # Construct a query based on available columns
                query_parts = ["SELECT"]
                select_cols = []
                if "student_id" in columns: select_cols.append("student_id")
                if "section" in columns: select_cols.append("section")
                if "name" in columns: select_cols.append("name")
                
                if not select_cols:
                    st.warning("Student profile columns are missing. Some features may be limited.")
                else:
                    query_parts.append(", ".join(select_cols))
                    query_parts.append(f"FROM {table_name} WHERE")
                    
                    where_parts = []
                    if "name" in columns: where_parts.append("name = ?")
                    if "username" in columns: where_parts.append("username = ?")
                    
                    if not where_parts:
                        # No usable columns to query by
                        st.warning("Cannot query student profiles. Some features may be limited.")
                    else:
                        query_parts.append(" OR ".join(where_parts))
                        
                        # Complete query
                        query = " ".join(query_parts)
                        # Add parameters for each where condition
                        params = [username] * len(where_parts)
                        
                        execute_query(query, params)
                        student_data = cursor.fetchone()
                        
                        if student_data:
                            # Map columns to session state
                            idx = 0
                            if "student_id" in columns:
                                st.session_state['current_user']['student_id'] = student_data[idx]
                                idx += 1
                            if "section" in columns:
                                st.session_state['current_user']['section'] = student_data[idx]
                                idx += 1
                            if "name" in columns:
                                st.session_state['current_user']['full_name'] = student_data[idx]
        
        elif user_role == 'professor':
            # First check if professor_profiles table exists
            execute_query("SELECT name FROM sqlite_master WHERE type='table' AND name='professor_profiles'")
            if cursor.fetchone():
                # Check if the table has the username column
                execute_query("PRAGMA table_info(professor_profiles)")
                columns = [info[1] for info in cursor.fetchall()]
                
                if "username" in columns and "department" in columns:
                    cursor.execute("""
                        SELECT department FROM professor_profiles WHERE username = ?
                    """, (username,))
                    prof_data = cursor.fetchone()
                    
                    if prof_data:
                        st.session_state['current_user']['department'] = prof_data[0] if prof_data else 'Unknown'
            else:
                # Silently handle missing professor_profiles table
                st.session_state['current_user']['department'] = 'Unknown'
        
    except Exception as e:
        st.warning(f"Error retrieving user details: {str(e)}")
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
            import subject_management
            import enhanced_db_explorer
            
            # Create a dictionary mapping page names to their respective functions
            # Include Admin Dashboard in the complete pages dictionary, but we'll filter it from navigation
            all_pages = {
                "Admin Dashboard": admin_dashboard.show_admin_dashboard,
                "Subject Management": subject_management.show_subject_management,
                "Real-Time Recognition": real_time_prediction.show_real_time_prediction,
                "Registration": registration_form.show_registration_form,
                "Database Explorer": enhanced_db_explorer.show_db_explorer
            }
            
            # Create a filtered version for the sidebar navigation (without Admin Dashboard)
            nav_pages = {k: v for k, v in all_pages.items() if k != "Admin Dashboard"}
            
            # Set default page to Subject Management if not already set or if was Admin Dashboard
            if ('current_page' not in st.session_state 
                or st.session_state.current_page not in all_pages
                or st.session_state.current_page == "Admin Dashboard"):
                st.session_state.current_page = "Subject Management"
            
            # Always show sidebar for admin
            with st.sidebar:
                # Updated sidebar header with centered style
                st.markdown(f"""
                <div class="admin-username-container">
                    <span style="font-size: 24px;">👤</span>
                    <span class="admin-username-text">{username} (Admin)</span>
                </div>
                """, unsafe_allow_html=True)
                
                # Full-width logout button - CHANGED KEY TO sidebar_logout_primary
                if st.button("🚪 Logout", key="sidebar_logout_primary", use_container_width=True):
                    logout_user()
                
                # Add a subtle divider
                st.markdown("<hr style='margin: 5px 0; opacity: 0.3;'>", unsafe_allow_html=True)
                
                # Show admin dashboard button at top of sidebar
                if st.button("🏠 Admin Home", use_container_width=True):
                    st.session_state.current_page = "Admin Dashboard"
                    st.rerun()
                
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
            import subject_management
            import enhanced_db_explorer
            
            # Create a dictionary mapping page names to their respective functions
            pages = {
                "Admin Dashboard": admin_dashboard.show_admin_dashboard,  # Add admin dashboard as first option
                "Subject Management": subject_management.show_subject_management,
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
                conn = sqlite3.connect('attendance_system.db')
                try:
                    users_df = execute_query_df("SELECT username, role FROM user_accounts ORDER BY role, username")
                    st.dataframe(users_df)
                except Exception as e:
                    st.error(f"Error loading users: {e}")
                finally:
                    conn.close()
            
            with admin_tabs[1]:
                st.header("System Status")
                
                # Show database tables
                conn = sqlite3.connect('attendance_system.db')
                try:
                    tables_df = execute_query_df("SELECT name, type FROM sqlite_master WHERE type='table'")
                    st.subheader("Database Tables")
                    st.dataframe(tables_df)
                    
                    # Count records in main tables
                    st.subheader("Record Counts")
                    counts = {}
                    
                    for table in tables_df['name']:
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
                });
            }
            
            // Apply immediately and repeatedly
            enforcePadding();
            setTimeout(enforcePadding, 100);
            setTimeout(enforcePadding, 500);
        });
        </script>
        """, unsafe_allow_html=True)
        
        # Top navigation bar with title and user info in a better layout (matching student report)
        top_col1, top_col2 = st.columns([3, 2])
        
        with top_col1:
            st.markdown("## 📚 Teacher Dashboard", unsafe_allow_html=False)
        
        # User info and buttons in column 2
        with top_col2:
            # Username display with right alignment
            st.markdown(f"""
            <div class="username-container">
                <div class="username-text">
                    👤 {username}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Refresh and logout buttons side by side
            button_col1, button_col2 = st.columns(2)
            
            with button_col1:
                # Refresh button with same style as logout
                if st.button("🔄 Refresh", key="prof_refresh", use_container_width=True):
                    st.rerun()
            
            with button_col2:
                # Logout button
                if st.button("🚪 Logout", key="prof_logout", use_container_width=True):
                    logout_user()
        
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
                });
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
            print("Restored admin role from query parameters")
        elif role == "professor":
            st.session_state.is_professor = True
            print("Restored professor role from query parameters")
    
    # Also restore admin role if username contains 'admin'
    if "username" in st.query_params and "admin" in st.query_params["username"].lower():
        st.session_state.user_role = "admin"
        st.session_state.is_admin = True
        print(f"Set admin role based on username: {st.query_params['username']}")
    
    # Setup admin tables to ensure they exist
    try:
        from setup_admin_tables import setup_admin_tables
        setup_admin_tables()
    except Exception as e:
        print(f"Warning: Could not set up admin tables: {e}")
    
    # Setup student tables to ensure they exist
    try:
        from setup_student_tables import setup_student_tables
        # Run in non-interactive mode (not asking for sample data)
        conn = sqlite3.connect('attendance_system.db')
        cursor = conn.cursor()
        
        # Check if student_profiles exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='student_profiles'")
        if not cursor.fetchone():
            print("Creating student_profiles table...")
            setup_student_tables()
        conn.close()
    except Exception as e:
        print(f"Warning: Could not set up student tables: {e}")
    
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if st.session_state.logged_in:
        show_app()
    else:
        import login
        login.main()