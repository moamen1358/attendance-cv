"""
Test page for dropdown functionality
"""
import streamlit as st
from ui_utils import apply_consistent_styling, create_dropdown_with_proper_spacing, create_multiselect_with_proper_spacing
from data_access import get_professors_simple, get_subjects_simple

def main():
    st.set_page_config(
        page_title="Dropdown Test",
        page_icon="🧪",
        layout="wide"
    )
    
    # Apply styling
    apply_consistent_styling()
    
    st.title("🧪 Dropdown Test Page")
    st.write("This page tests if dropdowns work correctly with proper styling and positioning")
    
    # Test form
    with st.form("test_form"):
        st.subheader("Test Form")
        
        # Load data
        professors_df = get_professors_simple()
        subjects_df = get_subjects_simple()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Professor Selection:**")
            if not professors_df.empty:
                selected_prof = create_dropdown_with_proper_spacing(
                    "Choose Professor",
                    options=professors_df['username'].tolist(),
                    format_func=lambda x: f"{professors_df[professors_df['username'] == x]['name'].iloc[0]}",
                    key="test_prof"
                )
                st.write(f"Selected: {selected_prof}")
            else:
                st.error("No professors found")
        
        with col2:
            st.write("**Subject Selection:**")
            if not subjects_df.empty:
                selected_subjects = create_multiselect_with_proper_spacing(
                    "Choose Subjects",
                    options=subjects_df['subject_id'].tolist(),
                    format_func=lambda x: f"{subjects_df[subjects_df['subject_id'] == x]['subject_name'].iloc[0]}",
                    key="test_subj"
                )
                st.write(f"Selected: {selected_subjects}")
            else:
                st.error("No subjects found")
        
        # Submit button
        submit = st.form_submit_button("Test Submit", use_container_width=True)
        
        if submit:
            st.success("Form submitted successfully!")
    
    # Data verification
    st.subheader("Data Verification")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Professors Data:**")
        st.dataframe(professors_df, use_container_width=True)
    
    with col2:
        st.write("**Subjects Data:**")
        st.dataframe(subjects_df, use_container_width=True)

if __name__ == "__main__":
    main()
