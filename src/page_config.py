"""
Centralized page configuration settings.

This module ensures that page configuration is consistent across the application
and only happens once, preventing the StreamlitSetPageConfigMustBeFirstCommandError.
"""
import streamlit as st

# Track whether page config has been set
_page_config_applied = False

def apply_page_config():
    """
    Apply page configuration if not already applied.
    Should be called at the very beginning of each entry point.
    """
    global _page_config_applied
    
    if not _page_config_applied:
        st.set_page_config(
            page_title="Attendance Management System",
            page_icon="📚",
            layout="wide",
            initial_sidebar_state="auto"
        )
        _page_config_applied = True
        return True
    return False

# Apply configuration when this module is imported
apply_page_config()
