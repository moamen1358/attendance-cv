import streamlit as st
import sqlite3
import pandas as pd
from setup_teacher_subjects import get_teacher_subjects, assign_subject_to_teacher, remove_subject_from_teacher

# Constants
DATABASE_PATH = 'attendance_system.db'

def get_db_connection():
    """Get a connection to the SQLite database"""
    return sqlite3.connect(DATABASE_PATH)

def get_all_subjects():
    """Get a list of all subjects in the system"""
    conn = get_db_connection()
    query = "SELECT DISTINCT subject FROM control_4 WHERE subject != '' ORDER BY subject"
    df = pd.read_sql(query, conn)
    conn.close()
    return df['subject'].tolist()

def get_all_teachers():
    """Get a list of all teachers in the system"""
    conn = get_db_connection()
    query = "SELECT username FROM users WHERE role = 'admin' ORDER BY username"
    df = pd.read_sql(query, conn)
    conn.close()
    return df['username'].tolist()

def show_subject_management():
    st.title("Subject Management")
    
    # Get current user
    username = st.session_state.get('username', '')
    user_role = st.session_state.get('user_role', '')
    
    if user_role != 'admin':
        st.error("You don't have permission to access this page")
        return
    
    # Show the user's subjects
    st.header("Your Subjects")
    teacher_subjects = get_teacher_subjects(username)
    
    if not teacher_subjects:
        st.info("You don't have any subjects assigned yet.")
    else:
        # Create a nice grid to display subjects
        cols = st.columns(3)
        for i, subject in enumerate(teacher_subjects):
            with cols[i % 3]:
                st.markdown(f"""
                <div style="
                    padding: 15px;
                    border-radius: 10px;
                    border: 1px solid #2196F3;
                    margin-bottom: 10px;
                    background-color: rgba(33, 150, 243, 0.1);
                    text-align: center;
                ">
                    <h3 style="margin: 0; color: #2196F3;">{subject}</h3>
                </div>
                """, unsafe_allow_html=True)
    
    # Add subjects
    st.header("Add Subject")
    
    # Get all subjects that the teacher doesn't have
    all_subjects = get_all_subjects()
    available_subjects = [s for s in all_subjects if s not in teacher_subjects]
    
    if not available_subjects:
        st.info("You are already assigned to all available subjects.")
    else:
        col1, col2 = st.columns([3, 1])
        with col1:
            new_subject = st.selectbox("Select Subject", available_subjects, key="add_subject_selectbox")
        with col2:
            if st.button("Add", use_container_width=True):
                if assign_subject_to_teacher(username, new_subject):
                    st.success(f"Added {new_subject} to your subjects!")
                    st.rerun()
                else:
                    st.error("Failed to add subject")
    
    # Remove subjects
    if teacher_subjects:
        st.header("Remove Subject")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            subject_to_remove = st.selectbox("Select Subject to Remove", teacher_subjects, key="remove_subject_selectbox")
        with col2:
            if st.button("Remove", use_container_width=True):
                if remove_subject_from_teacher(username, subject_to_remove):
                    st.success(f"Removed {subject_to_remove} from your subjects!")
                    st.rerun()
                else:
                    st.error("Failed to remove subject")
    
    # Super admin section - if this user has special privileges
    # This is a simplified example - in a real system you'd have proper role-based controls
    if username == "admin":
        st.header("Super Admin: Manage All Teachers")
        st.info("As a super admin, you can assign subjects to any teacher")
        
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            selected_teacher = st.selectbox("Select Teacher", get_all_teachers(), key="teacher_username_selectbox")
        
        with col2:
            teacher_subs = get_teacher_subjects(selected_teacher)
            remaining_subjects = [s for s in all_subjects if s not in teacher_subs]
            if remaining_subjects:
                selected_subject = st.selectbox("Select Subject", remaining_subjects, key="assign_subject_selectbox")
            else:
                st.info("This teacher has all subjects assigned")
                selected_subject = None
        
        with col3:
            if selected_subject and st.button("Assign", use_container_width=True):
                if assign_subject_to_teacher(selected_teacher, selected_subject):
                    st.success(f"Assigned {selected_subject} to {selected_teacher}")
                    st.rerun()
                else:
                    st.error("Failed to assign subject")
        
        # Show the current assignments in a nice table
        st.subheader("Current Teacher-Subject Assignments")
        
        conn = get_db_connection()
        query = """
        SELECT ts.teacher_username, ts.subject
        FROM teacher_subjects ts
        JOIN users u ON ts.teacher_username = u.username
        WHERE u.role = 'admin'
        ORDER BY ts.teacher_username, ts.subject
        """
        assignments_df = pd.read_sql(query, conn)
        conn.close()
        
        if not assignments_df.empty:
            st.dataframe(
                assignments_df,
                column_config={
                    "teacher_username": "Teacher",
                    "subject": "Subject"
                },
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("No teacher-subject assignments found")

if __name__ == "__main__":
    show_subject_management()
