import streamlit as st
import home
import real_time_prediction
import report
import student_report
# Remove this line: import db_explorer
import registration_form
import subject_management
import sqlite3
import time
from global_css_handler import apply_global_css, enforce_fixed_padding
import enhanced_db_explorer

def show_app():
    # Apply global CSS to ensure consistency across all pages
    apply_global_css()
    
    # Add JavaScript enforcement for padding
    enforce_fixed_padding()
    
    # Add extra strong CSS for consistent padding
    st.markdown("""
    <style>
    /* FORCED PADDING FOR ALL PAGES - Maximum specificity */
    body .main .block-container,
    .main .block-container,
    div.block-container,
    [data-testid="stAppViewBlockContainer"] div.block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        padding-left: 80px !important;
        padding-right: 80px !important;
        max-width: unset !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Remove redundant CSS that might be overriding our global styles
    # Instead, just add role-specific styles if needed
    st.markdown("""
    <style>
    /* Role-specific styles can go here */
    .sidebar-toggle {
        position: fixed;
        bottom: 20px;
        left: 20px;
        background-color: rgba(30, 136, 229, 0.8);
        color: white;
        border: none;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        font-size: 18px;
        z-index: 100;
        cursor: pointer;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        display: flex;
        align-items: center;
        justify-content: center;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Check login status from both session state and query params
    if 'username' not in st.session_state:
        # Check if logged_in parameter exists in URL
        if "logged_in" in st.query_params and st.query_params["logged_in"] == "True":
            if "username" in st.query_params:
                # Restore login state from query parameters
                st.session_state.logged_in = True
                st.session_state.username = st.query_params["username"]
                
                # Retrieve the user role if not in session state
                if 'user_role' not in st.session_state:
                    conn = sqlite3.connect('attendance_system.db')
                    cursor = conn.cursor()
                    cursor.execute("SELECT role FROM user_accounts WHERE username = ?", 
                                 (st.session_state.username,))
                    result = cursor.fetchone()
                    conn.close()
                    
                    if result:
                        st.session_state.user_role = result[0]
                    else:
                        st.session_state.user_role = 'student'  # Default
            else:
                st.error("Please log in to view your attendance")
                time.sleep(1)  # Brief delay before redirecting
                st.rerun()
        else:
            st.error("Please log in to view your attendance")
            time.sleep(1)  # Brief delay before redirecting
            st.rerun()
    
    # Ensure query parameters are updated with current session state
    st.query_params["logged_in"] = "True"
    st.query_params["username"] = st.session_state.username
    
    # Get user role from session state (default to student if not set)
    user_role = st.session_state.get('user_role', 'student')
    username = st.session_state.get('username', 'User')
    
    # Initialize show_sidebar state - now default to TRUE for admin user_accounts
    if 'show_sidebar' not in st.session_state:
        st.session_state.show_sidebar = True if user_role == 'admin' else False
    
    # ADMIN VIEW - Full access to all pages
    if user_role == 'admin':
        # Admin sees all pages with a top navigation bar and sidebar
        
        # Create a dictionary mapping page names to their respective functions
        # Removed "Reports" from the pages dictionary
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

if __name__ == "__main__":
    # This block only runs when app.py is executed directly
    st.set_page_config(layout="wide")