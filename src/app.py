import streamlit as st
import home
import real_time_prediction
import report
import student_report
import db_explorer  # Import the new module
import registration_form
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
    
    # Create a radio button for navigation
    selection = st.sidebar.radio("Go to", list(pages.keys()))
    
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