import streamlit as st
import home
import real_time_prediction
import report
import student_report
import db_explorer
import registration_form

def show_app():
    st.sidebar.title("Navigation")
    
    # Get user role from session state (default to student if not set)
    user_role = st.session_state.get('user_role', 'student')
    username = st.session_state.get('username', 'User')
    
    # Show user info in sidebar
    st.sidebar.info(f"Logged in as: {username} ({user_role})")
    
    # Create a dictionary mapping page names to their respective functions
    if user_role == 'admin':
        # Admin sees all pages except Student Attendance
        pages = {
            "Home": home.show_home,
            "Real-Time Face Recognition": real_time_prediction.show_real_time_prediction,
            "Student Registration": registration_form.show_registration_form,
            "Reports": report.show_report,
            "Database Explorer": db_explorer.show_db_explorer
        }
    else:
        # Student only sees their attendance
        pages = {
            "My Attendance": student_report.show_student_report
        }
    
    # Create a radio button for navigation
    selection = st.sidebar.radio("Go to", list(pages.keys()))
    
    # Add logout button to sidebar
    if st.sidebar.button("Logout"):
        # Clear session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        # Clear query params
        st.query_params.clear()
        st.rerun()
    
    # Call the selected page function
    pages[selection]()

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