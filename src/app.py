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