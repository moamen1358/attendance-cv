import streamlit as st
import sqlite3
import pandas as pd
from global_fixes import apply_global_dropdown_fixes
from data_access import get_professors_simple, get_subjects_simple, get_current_assignments_simple, assign_subject_to_professor

def show_professor_assignments():
    """Main function to show professor assignments interface"""
    # Apply global fixes
    apply_global_dropdown_fixes()
    
    # Create tabs for different operations
    assignment_tabs = st.tabs(["Assign Subjects", "View Assignments"])
    
    with assignment_tabs[0]:
        show_assignment_form()
    
    with assignment_tabs[1]:
        show_current_assignments()

def show_assignment_form():
    """Show clean, reliable assignment form"""
    st.subheader("Assign Subjects to Professors")
    
    # Create form with enhanced styling
    with st.form("professor_assignment_form", clear_on_submit=True):
        # Load data
        professors_df = get_professors_simple()
        subjects_df = get_subjects_simple()
        
        # Check if data is available
        if professors_df.empty:
            st.error("No professors found in the system")
            st.form_submit_button("Assign Subjects", disabled=True)
            return
            
        if subjects_df.empty:
            st.error("No subjects found in the system")
            st.form_submit_button("Assign Subjects", disabled=True)
            return
        
        # Create two columns for better layout
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.write("**Select Professor:**")
            selected_professor = st.selectbox(
                "Professor",
                options=professors_df['username'].tolist(),
                format_func=lambda x: f"{professors_df[professors_df['username'] == x]['name'].iloc[0]}",
                key="prof_select",
                label_visibility="collapsed"
            )
        
        with col2:
            st.write("**Select Subjects:**")
            selected_subjects = st.multiselect(
                "Subjects",
                options=subjects_df['subject_id'].tolist(),
                format_func=lambda x: f"{subjects_df[subjects_df['subject_id'] == x]['subject_name'].iloc[0]}",
                key="subj_select",
                label_visibility="collapsed"
            )
        
        # Add some space before submit button
        st.write("")
        
        # Submit button
        submit_button = st.form_submit_button("Assign Subjects", use_container_width=True)
        
        # Handle form submission
        if submit_button and selected_professor and selected_subjects:
            success_count = assign_subject_to_professor(selected_professor, selected_subjects)
            
            if success_count > 0:
                st.success(f"Successfully assigned {success_count} subject(s) to {selected_professor}")
                st.rerun()  # Refresh to show updated assignments
            else:
                st.warning("No new assignments were made (subjects may already be assigned)")
        elif submit_button:
            st.error("Please select both a professor and at least one subject")

def show_current_assignments():
    """Show current professor-subject assignments"""
    st.subheader("Current Professor-Subject Assignments")
    
    # Load current assignments
    assignments_df = get_current_assignments_simple()
    
    if assignments_df.empty:
        st.info("No professor-subject assignments found")
        return
    
    # Display assignments in a nice table
    st.dataframe(
        assignments_df,
        column_config={
            "professor_username": "Username",
            "professor_name": "Professor Name",
            "subject_name": "Subject",
            "assigned_date": "Assigned Date"
        },
        hide_index=True,
        use_container_width=True
    )
    
    # Show summary statistics
    with st.expander("Assignment Statistics"):
        total_assignments = len(assignments_df)
        unique_professors = assignments_df['professor_username'].nunique()
        unique_subjects = assignments_df['subject_name'].nunique()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Assignments", total_assignments)
        with col2:
            st.metric("Professors Assigned", unique_professors)
        with col3:
            st.metric("Subjects Assigned", unique_subjects)
