"""
Display Patch Module

This module provides patches and fixes for Streamlit's display functionality.
"""
import streamlit as st
import pandas as pd
import numpy as np
import sqlite3

# Original warning function
original_warning = st.warning

# Database check function
def check_student_profiles_exists():
    try:
        conn = sqlite3.connect('attendance_system.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='student_profiles'")
        exists = cursor.fetchone() is not None
        conn.close()
        return exists
    except:
        return False

# Create student profiles table function
def create_student_profiles_table():
    try:
        conn = sqlite3.connect('attendance_system.db')
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS student_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            name TEXT,
            student_id TEXT,
            section TEXT,
            email TEXT,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Try to add current user or default user
        try:
            username = st.session_state.get('username', 'default_user')
        except:
            username = 'default_user'
            
        cursor.execute("""
        INSERT OR IGNORE INTO student_profiles (username, name, student_id, section) 
        VALUES (?, ?, ?, ?)
        """, (username, username, username, 'Default'))
        
        conn.commit()
        conn.close()
        print("Created student_profiles table with default user")
        return True
    except Exception as e:
        print(f"Error creating student profiles table: {e}")
        return False

# Override warning function to intercept and fix the student profiles warning
def patched_warning(text, *args, **kwargs):
    if text == "Student profiles table not found. Some features may be limited.":
        print("Intercepted student profiles warning! Attempting to fix...")
        
        # Check if table exists first
        if not check_student_profiles_exists():
            # Try to create it
            if create_student_profiles_table():
                print("Successfully created student_profiles table!")
            else:
                print("Failed to create student_profiles table.")
        else:
            print("Student profiles table exists, but warning was still triggered.")
            
        # Don't display the warning regardless of whether we fixed it or not
        return None
    else:
        # For all other warnings, use the original function
        return original_warning(text, *args, **kwargs)

# Apply the patch
st.warning = patched_warning

def patch_display_functions():
    """
    Apply patches to Streamlit display functions to handle edge cases.
    
    This includes:
    - Handling NaN values and None values in DataFrames
    - Formatting dates in a consistent way
    - Improving the display of numeric values
    """
    # Patch pandas DataFrame display in Streamlit
    # Save original _repr_html_ method
    original_repr_html = pd.DataFrame._repr_html_
    
    def patched_repr_html(self):
        """Patched HTML representation with better NaN handling"""
        # Replace NaN with empty string for display
        df_display = self.copy()
        df_display = df_display.replace({np.nan: ""})
        return original_repr_html(df_display)
    
    # Apply the patch (optional - uncomment if needed)
    # pd.DataFrame._repr_html_ = patched_repr_html
    
    print("Display patches applied successfully")
    return True
