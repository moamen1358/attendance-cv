"""
Shared configuration settings for the application.
This centralizes settings like page configuration.
"""

import streamlit as st

# Initialize page config - only called if it hasn't been set already
def init_page_config():
    try:
        st.set_page_config(
            page_title="Attendance Management System",
            page_icon="📚",
            layout="wide",
            initial_sidebar_state="auto"
        )
        print("Page config initialized successfully")
    except Exception as e:
        # This will happen if another module already set the page config
        print(f"Page config already set: {e}")
