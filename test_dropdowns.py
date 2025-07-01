"""
Simple test page for dropdown functionality
"""
import streamlit as st
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from dropdown_utils import create_professor_dropdown, create_subjects_multiselect, create_subjects_dropdown

st.title("Dropdown Test Page")

st.header("Testing Professor Dropdown")
selected_prof = create_professor_dropdown()
if selected_prof:
    st.write(f"Selected professor: {selected_prof}")

st.header("Testing Subject Dropdown (Single)")
selected_subject = create_subjects_dropdown()
if selected_subject:
    st.write(f"Selected subject: {selected_subject}")

st.header("Testing Subjects Multiselect")
selected_subjects = create_subjects_multiselect()
if selected_subjects:
    st.write(f"Selected subjects: {selected_subjects}")

# Test form
st.header("Testing in Form")
with st.form("test_form"):
    prof = create_professor_dropdown("Professor", key="form_prof")
    subjects = create_subjects_multiselect("Subjects", key="form_subjects")
    
    if st.form_submit_button("Test Submit"):
        st.success(f"Form submitted with prof={prof}, subjects={subjects}")
