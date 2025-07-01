import streamlit as st
import sqlite3
import pandas as pd
from global_fixes import apply_global_dropdown_fixes
from data_access import get_current_assignments_simple

def show_professor_assignments():
    """Main function to show professor assignments interface - View Only"""
    # Apply global fixes
    apply_global_dropdown_fixes()
    
    # Show only the assignments view (removed assignment form)
    show_current_assignments()

def show_current_assignments():
    """Show current professor-subject assignments with enhanced styling"""
    # Load current assignments
    assignments_df = get_current_assignments_simple()
    
    if assignments_df.empty:
        st.info("📋 No professor-subject assignments found")
        return
    
    # Add styling header
    st.markdown("### 📊 Assignment Overview")
    
    # Display assignments in a nice table
    st.dataframe(
        assignments_df,
        column_config={
            "professor_username": "👤 Username",
            "professor_name": "👨‍🏫 Professor Name",
            "subject_name": "📚 Subject",
            "assigned_date": "📅 Assigned Date"
        },
        hide_index=True,
        use_container_width=True
    )
    
    # Show summary statistics with icons
    with st.expander("📈 Assignment Statistics"):
        total_assignments = len(assignments_df)
        unique_professors = assignments_df['professor_username'].nunique()
        unique_subjects = assignments_df['subject_name'].nunique()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🔢 Total Assignments", total_assignments)
        with col2:
            st.metric("👨‍🏫 Professors Assigned", unique_professors)
        with col3:
            st.metric("📚 Subjects Assigned", unique_subjects)
