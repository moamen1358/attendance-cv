#!/usr/bin/env python3
"""
Enhanced Registration Form Test
================================
Test the new comprehensive student registration form
"""

import streamlit as st
import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from registration_form import show_registration_form, initialize_database

def main():
    st.set_page_config(
        page_title="Enhanced Student Registration",
        page_icon="🎓",
        layout="wide"
    )
    
    # Initialize database on startup
    initialize_database()
    
    st.title("🎓 Enhanced Student Registration System")
    st.markdown("""
    Welcome to the **Professional Student Registration System**! 
    
    This enhanced form captures comprehensive student information including:
    - 📝 **Personal Details**: Name, ID, contact information
    - 🎓 **Academic Information**: Department, major, year, GPA
    - 📍 **Additional Details**: Address, emergency contact, enrollment date
    - 📸 **Photo Registration**: Facial recognition setup
    - 🔐 **Account Creation**: Automatic account setup with secure credentials
    """)
    
    st.markdown("---")
    
    # Show the enhanced registration form
    show_registration_form()
    
    # Show recent registrations
    st.markdown("---")
    st.subheader("📋 Recent Registrations")
    
    try:
        import sqlite3
        conn = sqlite3.connect('attendance_system.db')
        
        # Get recent registrations
        recent_students = conn.execute("""
            SELECT name, student_id, email, section, department, created_at
            FROM student_profiles 
            ORDER BY created_at DESC 
            LIMIT 10
        """).fetchall()
        
        if recent_students:
            import pandas as pd
            df = pd.DataFrame(recent_students, 
                            columns=['Name', 'Student ID', 'Email', 'Section', 'Department', 'Registered'])
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No registrations yet. Use the form above to register the first student!")
            
        conn.close()
    except Exception as e:
        st.error(f"Error loading recent registrations: {e}")

if __name__ == "__main__":
    main()
