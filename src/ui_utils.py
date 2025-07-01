"""
Enhanced UI utilities for consistent dropdown and form styling
"""
import streamlit as st

def apply_consistent_styling():
    """Apply consistent styling that works reliably across refreshes"""
    st.markdown("""
    <style>
    /* Force consistent styling for all dropdowns */
    .stSelectbox > div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        border: 1px solid #cccccc !important;
        border-radius: 4px !important;
        min-height: 40px !important;
        width: 100% !important;
    }
    
    /* Fix dropdown menu positioning */
    .stSelectbox > div[data-baseweb="select"] [role="listbox"] {
        background-color: #ffffff !important;
        border: 1px solid #cccccc !important;
        border-radius: 4px !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15) !important;
        z-index: 9999 !important;
        position: absolute !important;
        width: 100% !important;
    }
    
    /* Remove unwanted spacing between rows */
    .stSelectbox {
        margin-bottom: 8px !important;
    }
    
    /* Fix multiselect styling */
    .stMultiSelect > div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        border: 1px solid #cccccc !important;
        border-radius: 4px !important;
        min-height: 40px !important;
        width: 100% !important;
    }
    
    .stMultiSelect > div[data-baseweb="select"] [role="listbox"] {
        background-color: #ffffff !important;
        border: 1px solid #cccccc !important;
        border-radius: 4px !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15) !important;
        z-index: 9999 !important;
        position: absolute !important;
        width: 100% !important;
        max-height: 200px !important;
        overflow-y: auto !important;
    }
    
    /* Ensure form containers use full width */
    .stForm {
        width: 100% !important;
        background-color: #f8f9fa !important;
        padding: 20px !important;
        border-radius: 8px !important;
        border: 1px solid #e0e0e0 !important;
    }
    
    /* Fix button positioning */
    .stButton > button {
        width: 100% !important;
        background-color: #007bff !important;
        color: white !important;
        border: none !important;
        border-radius: 4px !important;
        padding: 10px 20px !important;
        font-weight: 500 !important;
    }
    
    .stButton > button:hover {
        background-color: #0056b3 !important;
    }
    
    /* Remove default streamlit spacing issues */
    .element-container {
        margin-bottom: 8px !important;
    }
    
    /* Fix tab content positioning */
    .stTabs [data-baseweb="tab-panel"] {
        padding-top: 20px !important;
    }
    
    /* Ensure consistent colors across refreshes */
    .stApp {
        background-color: #ffffff !important;
    }
    
    .main .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

def create_form_container():
    """Create a properly styled form container"""
    return st.container()

def create_dropdown_with_proper_spacing(label, options, format_func=None, key=None):
    """Create a dropdown with proper spacing and styling"""
    if not options:
        st.warning(f"No options available for {label}")
        return None
    
    return st.selectbox(
        label,
        options=options,
        format_func=format_func,
        key=key,
        help=f"Select {label.lower()}"
    )

def create_multiselect_with_proper_spacing(label, options, format_func=None, key=None):
    """Create a multiselect with proper spacing and styling"""
    if not options:
        st.warning(f"No options available for {label}")
        return []
    
    return st.multiselect(
        label,
        options=options,
        format_func=format_func,
        key=key,
        help=f"Select multiple {label.lower()}"
    )
