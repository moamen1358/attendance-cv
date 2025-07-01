"""
Simplified professor subject assignment functions using the new dropdown utilities
"""
import streamlit as st
import sqlite3
from dropdown_utils import fix_dropdown_css, create_professor_dropdown, create_subjects_multiselect

def assign_subjects_to_professor(professor_username, subject_ids):
    """Assign subjects to a professor"""
    conn = sqlite3.connect('attendance_system.db')
    cursor = conn.cursor()
    
    try:
        success_count = 0
        for subject_id in subject_ids:
            try:
                # Insert into professor_subject_assignments view (which maps to teacher_subjects_enhanced)
                cursor.execute("""
                INSERT OR IGNORE INTO teacher_subjects_enhanced 
                (teacher_id, subject_id, academic_year, semester, section, assigned_date)
                SELECT 
                    u.linked_id,
                    ?,
                    '2024-2025',
                    'Fall',
                    'A',
                    date('now')
                FROM users_enhanced u 
                WHERE u.username = ? AND u.role = 'teacher'
                """, (subject_id, professor_username))
                
                if cursor.rowcount > 0:
                    success_count += 1
                    
            except Exception as e:
                st.error(f"Error assigning subject {subject_id}: {e}")
        
        conn.commit()
        
        if success_count > 0:
            st.success(f"Successfully assigned {success_count} subject(s) to {professor_username}")
        else:
            st.warning("No new assignments were made (subjects may already be assigned)")
            
    except Exception as e:
        st.error(f"Error in assignment process: {e}")
    finally:
        conn.close()

def show_assignment_form_new():
    """New simplified assignment form using dropdown utilities"""
    fix_dropdown_css()
    
    st.subheader("Assign Subjects to Professors")
    
    with st.form("assignment_form_new"):
        col1, col2 = st.columns([1, 1])
        
        with col1:
            selected_professor = create_professor_dropdown("Select Professor")
        
        with col2:
            selected_subjects = create_subjects_multiselect("Select Subject(s)")
        
        st.markdown("<br>", unsafe_allow_html=True)
        submit_button = st.form_submit_button("Assign Subjects", use_container_width=True)
    
    if submit_button and selected_professor and selected_subjects:
        assign_subjects_to_professor(selected_professor, selected_subjects)
        st.rerun()  # Refresh to show updated assignments
