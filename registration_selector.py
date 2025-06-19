#!/usr/bin/env python3
"""
Registration Form Launcher
==========================
Choose between the old simple registration form and the new enhanced version
"""

import streamlit as st
import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def main():
    st.set_page_config(
        page_title="Registration Form Selector",
        page_icon="📝",
        layout="wide"
    )
    
    st.title("📝 Registration Form Selector")
    st.markdown("Choose which registration form you want to use:")
    
    # Create two columns for the options
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 👤 Old/Simple Registration Form")
        st.markdown("""
        **Features:**
        - ✅ Simple name input
        - ✅ Photo upload or camera capture
        - ✅ Quick registration
        - ✅ Minimal information required
        - ✅ Just like the original version
        """)
        
        if st.button("🚀 Use Old Registration Form", type="primary", key="old_form"):
            st.markdown("---")
            # Import and show the old form
            from old_registration_form import show_old_registration_form
            show_old_registration_form()
    
    with col2:
        st.markdown("### 🎓 Enhanced Registration Form")
        st.markdown("""
        **Features:**
        - ✅ Comprehensive student information
        - ✅ Academic details (ID, department, major)
        - ✅ Contact information (email, phone)
        - ✅ Personal details (address, emergency contact)
        - ✅ Automatic account creation
        - ✅ Professional database integration
        """)
        
        if st.button("🚀 Use Enhanced Registration Form", type="secondary", key="new_form"):
            st.markdown("---")
            # Import and show the enhanced form
            from registration_form import show_registration_form, initialize_database
            initialize_database()
            show_registration_form()
    
    # Show current database status
    st.markdown("---")
    st.subheader("📊 Current Database Status")
    
    try:
        import sqlite3
        conn = sqlite3.connect('attendance_system.db')
        cursor = conn.cursor()
        
        # Count students in different tables
        try:
            cursor.execute("SELECT COUNT(*) FROM students")
            students_count = cursor.fetchone()[0]
        except:
            students_count = 0
            
        try:
            cursor.execute("SELECT COUNT(*) FROM student_profiles")
            profiles_count = cursor.fetchone()[0]
        except:
            profiles_count = 0
            
        try:
            cursor.execute("SELECT COUNT(*) FROM presidents_embeds")
            faces_count = cursor.fetchone()[0]
        except:
            faces_count = 0
        
        col_stat1, col_stat2, col_stat3 = st.columns(3)
        
        with col_stat1:
            st.metric("Students (Simple)", students_count)
        
        with col_stat2:
            st.metric("Student Profiles (Enhanced)", profiles_count)
        
        with col_stat3:
            st.metric("Registered Faces", faces_count)
        
        conn.close()
        
    except Exception as e:
        st.error(f"Error reading database: {e}")
    
    # Instructions
    st.markdown("---")
    st.subheader("💡 Which Form Should I Use?")
    
    st.markdown("""
    **Use the Old/Simple Form if:**
    - You want quick registration with minimal data
    - You only need name and photo for attendance
    - You prefer the familiar interface
    - You're doing bulk registrations
    
    **Use the Enhanced Form if:**
    - You need comprehensive student records
    - You want professional academic management
    - You need contact information and academic details
    - You're setting up a complete academic system
    """)

if __name__ == "__main__":
    main()
