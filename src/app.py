import streamlit as st
import home
import real_time_prediction
import report
import student_report
import db_explorer
import registration_form

def show_app():
    # Set consistent padding for all pages
    st.markdown("""
    <style>
    /* Apply consistent padding to all pages */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        padding-left: 80px !important;  /* Force 80px padding on left */
        padding-right: 80px !important; /* Force 80px padding on right */
        max-width: unset;
    }
    
    /* Style for sidebar logout button to match student page */
    .stButton button[key="sidebar_logout"] {
        background-color: #f44336;
        color: white;
        border: none;
        font-weight: bold;
        width: 100%; /* Make button full width of sidebar */
        padding: 0.5rem 0; /* More vertical padding */
        font-size: 1.1rem; /* Slightly larger font */
        height: 50px; /* Fixed height for consistency */
    }
    .stButton button[key="sidebar_logout"]:hover {
        background-color: #d32f2f;
        border: none;
    }
    div[data-testid="stButton"] button {
        background-color: #f44336;
        color: white;
        border: none;
        font-weight: bold;
    }
    div[data-testid="stButton"] button:hover {
        background-color: #d32f2f;
        border: none;
    }
    
    /* Updated admin username styling with better centering */
    .admin-username-container {
        display: flex;
        align-items: center;
        justify-content: center; /* Center contents horizontally */
        margin-bottom: 15px;
        padding: 10px;
        width: 100%;
        box-sizing: border-box;
        background: transparent;
        text-align: center;
    }
    .admin-username-text {
        font-weight: bold;
        font-size: 1.2rem;
        color: #1E88E5;
        margin-left: 8px;
    }
    /* Center sidebar elements */
    section[data-testid="stSidebar"] .block-container {
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Get user role from session state (default to student if not set)
    user_role = st.session_state.get('user_role', 'student')
    username = st.session_state.get('username', 'User')
    
    if user_role == 'admin':
        # Admin sees all pages with sidebar navigation
        
        # Updated sidebar header with centered style
        st.sidebar.markdown(f"""
        <div class="admin-username-container">
            <span style="font-size: 24px;">👤</span>
            <span class="admin-username-text">{username}</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Full-width logout button
        st.sidebar.button("🚪 Logout", key="sidebar_logout", use_container_width=True, on_click=lambda: logout_user())
        
        # Add a subtle divider
        st.sidebar.markdown("<hr style='margin: 5px 0; opacity: 0.3;'>", unsafe_allow_html=True)
        
        # Create a dictionary mapping page names to their respective functions
        # Removed Home page and made Reports the first item
        pages = {
            "Reports": report.show_report,
            "Real-Time Face Recognition": real_time_prediction.show_real_time_prediction,
            "Student Registration": registration_form.show_registration_form,
            "Database Explorer": db_explorer.show_db_explorer
        }
        
        # If there's no current page or it's "Home" (which is now removed), 
        # set it to "Reports" as the default
        if 'current_page' not in st.session_state or st.session_state.current_page == "Home":
            st.session_state.current_page = "Reports"
        
        # Get the index for the current page in the new menu
        current_index = list(pages.keys()).index(st.session_state.current_page) if st.session_state.current_page in pages else 0
        
        # Create a radio button for navigation (without the "Navigation" header)
        selection = st.sidebar.radio("", 
                                   list(pages.keys()),
                                   index=current_index)
        
        # Call the selected page function
        st.session_state.current_page = selection
        pages[selection]()
                
    else:
        # Student only sees their attendance
        # Keep the top navigation for student view with the improved styling
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
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if st.session_state.logged_in:
        show_app()
    else:
        import login
        login.main()