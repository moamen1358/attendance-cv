"""
Test the dark theme implementation
"""
import streamlit as st
import sys
import os
sys.path.append('src')

from global_fixes import apply_global_dropdown_fixes
from data_access import get_professors_simple, get_subjects_simple

def main():
    st.set_page_config(
        page_title="Dark Theme Test",
        page_icon="🌙",
        layout="wide"
    )
    
    # Apply dark theme
    apply_global_dropdown_fixes()
    
    st.title("🌙 Dark Theme Test")
    st.write("Testing the dark theme implementation for dropdowns and forms")
    
    # Test the form with dark theme
    with st.form("dark_theme_test"):
        st.subheader("Form Elements Test")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Professor Selection:**")
            professors_df = get_professors_simple()
            if not professors_df.empty:
                selected_prof = st.selectbox(
                    "Choose Professor",
                    options=professors_df['username'].tolist(),
                    format_func=lambda x: f"{professors_df[professors_df['username'] == x]['name'].iloc[0]}",
                    key="dark_prof"
                )
        
        with col2:
            st.write("**Subject Selection:**")
            subjects_df = get_subjects_simple()
            if not subjects_df.empty:
                selected_subjects = st.multiselect(
                    "Choose Subjects",
                    options=subjects_df['subject_id'].tolist()[:5],  # Limit to 5 for test
                    format_func=lambda x: f"{subjects_df[subjects_df['subject_id'] == x]['subject_name'].iloc[0]}",
                    key="dark_subj"
                )
        
        submit = st.form_submit_button("Test Dark Theme", use_container_width=True)
        
        if submit:
            st.success("Dark theme form submitted successfully!")
            st.info("The form elements should now have a dark background")
            st.warning("This is a warning message in dark theme")
            st.error("This is an error message in dark theme")

if __name__ == "__main__":
    main()
