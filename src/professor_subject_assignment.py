import streamlit as st
import sqlite3
import pandas as pd
from database_utils import execute_query, execute_query_df

def show_professor_assignments():
    # Remove the title since it will be displayed as a tab
    # st.title("Professor Subject Assignments") - removed
    
    # Create tabs for different operations
    assignment_tabs = st.tabs(["Assign Subjects", "View Assignments"])
    
    with assignment_tabs[0]:
        show_assignment_form()
    
    with assignment_tabs[1]:
        show_current_assignments()

def show_assignment_form():
    st.subheader("Assign Subjects to Professors")
    
    # Get list of professors
    professors_df = execute_query_df("SELECT username, name FROM user_accounts WHERE role = 'professor'")
    if professors_df.empty:
        st.warning("No professors found in the system")
        return
    
    # Get list of subjects
    subjects_df = execute_query_df("SELECT subject_id, subject_name FROM subjects")
    if subjects_df.empty:
        st.warning("No subjects found in the system")
        return
    
    # Create form for assignment
    with st.form("assignment_form"):
        # Select professor
        selected_professor = st.selectbox(
            "Select Professor",
            options=professors_df['username'].tolist(),
            format_func=lambda x: f"{professors_df[professors_df['username'] == x]['name'].values[0]} ({x})"
        )
        
        # Select subject(s)
        selected_subjects = st.multiselect(
            "Select Subject(s)",
            options=subjects_df['subject_id'].tolist(),
            format_func=lambda x: f"{subjects_df[subjects_df['subject_id'] == x]['subject_name'].values[0]} ({x})"
        )
        
        # Submit button
        submit_button = st.form_submit_button("Assign Subjects")
        
        if submit_button and selected_professor and selected_subjects:
            # Ensure both tables exist with the right structure
            execute_query("""
                CREATE TABLE IF NOT EXISTS professor_subject_assignments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    professor_username TEXT,
                    subject_id INTEGER,
                    assigned_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(professor_username, subject_id)
                )
            """)
            
            execute_query("""
                CREATE TABLE IF NOT EXISTS teacher_subjects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subject_id INTEGER,
                    teacher_name TEXT,
                    UNIQUE(subject_id, teacher_name)
                )
            """)
            
            # Insert assignments - now with explicit transaction to ensure consistency
            conn = sqlite3.connect('attendance_system.db')
            cursor = conn.cursor()
            success_count = 0
            
            try:
                # Start transaction
                conn.execute("BEGIN")
                
                for subject_id in selected_subjects:
                    try:
                        # Insert into professor_subject_assignments
                        cursor.execute(
                            "INSERT OR REPLACE INTO professor_subject_assignments (professor_username, subject_id) VALUES (?, ?)",
                            (selected_professor, subject_id)
                        )
                        
                        # Insert into teacher_subjects
                        cursor.execute(
                            "INSERT OR REPLACE INTO teacher_subjects (subject_id, teacher_name) VALUES (?, ?)",
                            (subject_id, selected_professor)
                        )
                        
                        success_count += 1
                    except sqlite3.IntegrityError as e:
                        st.error(f"Error assigning subject {subject_id}: {e}")
                
                # Commit all changes at once
                conn.commit()
                
                if success_count > 0:
                    st.success(f"Successfully assigned {success_count} subject(s) to {selected_professor}")
                    st.rerun()
                    
            except Exception as e:
                conn.rollback()
                st.error(f"Error during assignment: {e}")
            finally:
                conn.close()

def show_current_assignments():
    st.subheader("Current Subject Assignments")
    
    # Check if the assignments table exists
    table_exists = execute_query_df("SELECT name FROM sqlite_master WHERE type='table' AND name='professor_subject_assignments'")
    
    if table_exists.empty:
        st.info("No assignments have been made yet.")
        return
    
    # Get all assignments with professor and subject names - improved query
    assignments_df = execute_query_df("""
        SELECT 
            pa.professor_username, 
            ua.name AS professor_name, 
            pa.subject_id, 
            s.subject_name,
            pa.assigned_date
        FROM 
            professor_subject_assignments pa
        JOIN 
            user_accounts ua ON pa.professor_username = ua.username
        JOIN 
            subjects s ON pa.subject_id = s.subject_id
        ORDER BY 
            ua.name, s.subject_name
    """)
    
    if assignments_df.empty:
        st.info("No subject assignments found.")
        return
    
    # Display assignments in a table
    st.dataframe(assignments_df, use_container_width=True)
    
    # Add option to remove assignments
    st.subheader("Remove Assignment")
    
    # Create a unique list of professors who have assignments
    professors = assignments_df[['professor_username', 'professor_name']].drop_duplicates()
    
    with st.form("remove_assignment_form"):
        # Select professor
        selected_professor = st.selectbox(
            "Select Professor", 
            options=professors['professor_username'].tolist(),
            format_func=lambda x: professors[professors['professor_username'] == x]['professor_name'].values[0]
        )
        
        # Get subjects assigned to the selected professor
        if selected_professor:
            professor_subjects = assignments_df[assignments_df['professor_username'] == selected_professor]
            subject_options = professor_subjects['subject_id'].tolist()
            
            # Select subject to remove
            selected_subject = st.selectbox(
                "Select Subject to Remove",
                options=subject_options,
                format_func=lambda x: professor_subjects[professor_subjects['subject_id'] == x]['subject_name'].values[0]
            )
            
            # Submit button
            remove_button = st.form_submit_button("Remove Assignment")
            
            if remove_button and selected_subject:
                # Remove from both tables to ensure consistency
                conn = sqlite3.connect('attendance_system.db')
                try:
                    # Use a transaction for consistency
                    conn.execute("BEGIN")
                    cursor = conn.cursor()
                    
                    # Remove from professor_subject_assignments
                    cursor.execute(
                        "DELETE FROM professor_subject_assignments WHERE professor_username = ? AND subject_id = ?",
                        (selected_professor, selected_subject)
                    )
                    
                    # Remove from teacher_subjects
                    cursor.execute(
                        "DELETE FROM teacher_subjects WHERE teacher_name = ? AND subject_id = ?",
                        (selected_professor, selected_subject)
                    )
                    
                    conn.commit()
                    st.success(f"Successfully removed subject assignment")
                    st.rerun()
                
                except Exception as e:
                    conn.rollback()
                    st.error(f"Error removing assignment: {e}")
                finally:
                    conn.close()

if __name__ == "__main__":
    show_professor_assignments()
