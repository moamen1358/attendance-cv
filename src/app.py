import streamlit as st
import home
import real_time_prediction
import report
import student_report
import db_explorer
import registration_form

def show_app():
    # Get user role from session state (default to student if not set)
    user_role = st.session_state.get('user_role', 'student')
    username = st.session_state.get('username', 'User')
    
    if user_role == 'admin':
        # Admin sees all pages with sidebar navigation
        
        # Add custom CSS for logout button to match student page
        st.markdown("""
        <style>
        /* Style the sidebar logout button to match student page */
        .stButton button[key="sidebar_logout"] {
            background-color: #f44336;
            color: white;
            border: none;
            font-weight: bold;
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
        </style>
        """, unsafe_allow_html=True)
        
        # Redesigned sidebar header with user info - show only username without role label
        st.sidebar.markdown(f"""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
            <div style="font-weight: bold; color: #1E88E5;">
                👤 {username}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Logout button next to username
        if st.sidebar.button("🚪 Logout", key="sidebar_logout"):
            # Clear session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            # Clear query params
            st.query_params.clear()
            st.rerun()
        
        # Add a subtle divider
        st.sidebar.markdown("<hr style='margin: 5px 0; opacity: 0.3;'>", unsafe_allow_html=True)
        
        # Create a dictionary mapping page names to their respective functions
        pages = {
            "Home": home.show_home,
            "Real-Time Face Recognition": real_time_prediction.show_real_time_prediction,
            "Student Registration": registration_form.show_registration_form,
            "Reports": report.show_report,
            "Database Explorer": db_explorer.show_db_explorer
        }
        
        # Create a radio button for navigation (without the "Navigation" header)
        selection = st.sidebar.radio("", list(pages.keys()))
        
        # Call the selected page function
        st.session_state.current_page = selection
        pages[selection]()
                
    else:
        # Student only sees their attendance
        # Keep the top navigation for student view with the improved styling
        student_report.show_student_report()

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