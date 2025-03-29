"""
Global styles and CSS for the application.

This module provides styling functions for consistent UI appearance:
- Global CSS application
- Theme customization
- Layout adjustments
"""
import streamlit as st

def apply_global_css():
    """Apply global CSS styles for consistent appearance"""
    st.markdown("""
    <style>
    /* Main container styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Data table styling */
    .dataframe {
        width: 100%;
        font-size: 0.9rem;
    }
    
    /* Card styling */
    .card {
        border-radius: 8px;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
        background-color: white;
    }
    
    /* Metric cards */
    .metric-card {
        text-align: center;
        border-radius: 8px;
        padding: 1rem;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .metric-label {
        font-size: 1rem;
        color: #555;
    }
    
    /* Admin username in sidebar */
    .admin-username-container {
        background-color: rgba(151, 166, 195, 0.15);
        padding: 10px;
        border-radius: 5px;
        text-align: center;
        margin-bottom: 15px;
    }
    .admin-username-text {
        font-weight: bold;
        font-size: 1rem;
        margin-left: 8px;
    }
    
    /* Username container for non-admin */
    .username-container {
        text-align: right;
        margin-bottom: 10px;
    }
    .username-text {
        font-weight: bold;
        font-size: 1rem;
    }
    
    /* Improved button styles */
    div[data-testid="stButton"] button {
        border-radius: 4px;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    div[data-testid="stButton"] button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* Status indicators */
    .status-indicator {
        border-radius: 50%;
        display: inline-block;
        height: 10px;
        width: 10px;
        margin-right: 5px;
    }
    .status-active { background-color: #28a745; }
    .status-inactive { background-color: #dc3545; }
    .status-pending { background-color: #ffc107; }
    </style>
    """, unsafe_allow_html=True)

def ensure_consistent_padding():
    """Ensure consistent padding across all pages"""
    st.markdown("""
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        function enforcePadding() {
            const containers = document.querySelectorAll('.block-container, [data-testid="stAppViewBlockContainer"] div.block-container');
            containers.forEach(function(container) {
                container.style.setProperty('padding-left', '80px', 'important');
                container.style.setProperty('padding-right', '80px', 'important');
                container.style.setProperty('max-width', 'unset', 'important');
            });
        }
        
        enforcePadding();
        setTimeout(enforcePadding, 100);
        setTimeout(enforcePadding, 500);
    });
    </script>
    """, unsafe_allow_html=True)

def hide_sidebar_for_role(role):
    """Hide sidebar for specific roles"""
    if role.lower() in ['student', 'professor']:
        st.markdown("""
        <script>
        document.addEventListener('DOMContentLoaded', function() {
            const style = document.createElement('style');
            style.innerHTML = `
                section[data-testid="stSidebar"] { 
                    display: none !important;
                    width: 0px !important;
                }
            `;
            document.head.appendChild(style);
        });
        </script>
        """, unsafe_allow_html=True)
