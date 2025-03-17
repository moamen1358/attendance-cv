import streamlit as st
import home
import real_time_prediction
import report
import student_report
<<<<<<< HEAD
import db_explorer  # Import the new module
import registration_form
=======
import registration_form
import subject_management
import sqlite3
from database_utils import execute_query, execute_query_df
import time
from global_css_handler import apply_global_css, enforce_fixed_padding
import enhanced_db_explorer
# Import not needed in main navigation anymore
# import professor_subject_assignment
>>>>>>> 8d6fc74 (working report page)

def show_app():
    st.sidebar.title("Navigation")
    
    # Create a dictionary mapping page names to their respective functions
    pages = {
        "Home": home.show_home,
        "Real-Time Face Recognition": real_time_prediction.show_real_time_prediction,
        "Regestration Form": registration_form.show_registration_form,
        "Reports": report.show_report,
        "Student Attendance": student_report.show_student_report,
        "Database Explorer": db_explorer.show_db_explorer  # Add the new page
    }
    
<<<<<<< HEAD
    # Create a radio button for navigation
    selection = st.sidebar.radio("Go to", list(pages.keys()))
=======
    # Get additional user details from database based on role with error handling
    try:
        conn = sqlite3.connect('attendance_system.db')
        cursor = conn.cursor()
        
        if user_role == 'student':
            # First check if student_profiles table exists
            execute_query("SELECT name FROM sqlite_master WHERE type='table' AND name='student_profiles'")
            if not cursor.fetchone():
                st.warning("Student profiles table not found. Some features may be limited.")
            else:
                # Check if the columns exist
                execute_query("PRAGMA table_info(student_profiles)")
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
                    query_parts.append("FROM student_profiles WHERE")
                    
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
>>>>>>> 00510a2
    
<<<<<<< HEAD
    # Call the selected page function
    pages[selection]()
=======
    # Initialize show_sidebar state - now default to TRUE for admin user_accounts
    if 'show_sidebar' not in st.session_state:
        st.session_state.show_sidebar = True if user_role == 'admin' else False
    
    # ADMIN VIEW - Full access to all pages
    if user_role == 'admin':
        # Admin sees all pages with a top navigation bar and sidebar
        
        # Create a dictionary mapping page names to their respective functions
        # Remove Professor Assignments from the pages dictionary
        pages = {
            "Subject Management": subject_management.show_subject_management,
            "Real-Time Recognition": real_time_prediction.show_real_time_prediction,
            "Registration": registration_form.show_registration_form,
            "Database Explorer": enhanced_db_explorer.show_db_explorer
        }
        
        # Set default page to Subject Management if not already set or if was previously Reports
        if 'current_page' not in st.session_state or st.session_state.current_page == "Reports":
            st.session_state.current_page = "Subject Management"
        
        # Always show sidebar for admin (remove toggle button)
        with st.sidebar:
            # Updated sidebar header with centered style
            st.markdown(f"""
            <div class="admin-username-container">
                <span style="font-size: 24px;">👤</span>
                <span class="admin-username-text">{username}</span>
            </div>
            """, unsafe_allow_html=True)
            
            # Full-width logout button
            if st.button("🚪 Logout", key="sidebar_logout", use_container_width=True):
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
                
    # PROFESSOR VIEW - Only access to Reports page with no sidebar
    elif user_role == 'professor':
        # Use consistent method to hide sidebar
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
                .main .block-container {
                    padding-left: 80px !important;
                    padding-right: 80px !important;
                }
            `;
            document.head.appendChild(style);
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
        # Apply the same sidebar hiding technique for consistency
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
                .main .block-container {
                    padding-left: 80px !important;
                    padding-right: 80px !important;
                }
            `;
            document.head.appendChild(style);
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
>>>>>>> 8d6fc74 (working report page)

if __name__ == "__main__":
    # This block only runs when app.py is executed directly
    st.set_page_config(layout="wide")
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if st.session_state.logged_in:
        show_app()
    else:
        import login
        login.main()