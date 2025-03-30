"""
Global CSS Handler Module

This module provides consistent styling across the application
by injecting CSS into Streamlit pages.
"""
import streamlit as st

def apply_global_css():
    """Apply global CSS to Streamlit app for consistent styling"""
    # Only inject once per session
    if 'css_applied' not in st.session_state:
        st.session_state.css_applied = True
        
        # Define CSS styles
        css = """
        <style>
        /* Global font and spacing improvements */
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
        }
        
        /* Improve table styling */
        .dataframe {
            border-collapse: collapse;
            margin: 25px 0;
            font-size: 14px;
            width: 100%;
        }
        
        .dataframe th {
            background-color: #1E88E5;
            color: white;
            text-align: left;
            padding: 12px;
            font-weight: 600;
        }
        
        .dataframe td {
            padding: 10px;
            border-bottom: 1px solid #ddd;
        }
        
        .dataframe tr:nth-of-type(even) {
            background-color: #f3f3f3;
        }
        
        .dataframe tr:hover {
            background-color: #e1f5fe;
        }
        
        /* Button improvements */
        .stButton>button {
            color: #ffffff;
            background-color: #1E88E5;
            border: none;
            border-radius: 4px;
            padding: 0.5rem 1rem;
            font-weight: 600;
            transition: all 0.2s ease;
        }
        
        .stButton>button:hover {
            background-color: #1565C0;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
        }
        
        /* Username container for consistent header styling */
        .username-container {
            display: flex;
            justify-content: flex-end;
            margin-bottom: 1rem;
        }
        
        .username-text {
            background-color: #f0f2f6;
            padding: 8px 15px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.9rem;
        }
        
        /* Admin username container */
        .admin-username-container {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            padding: 10px;
            background-color: #FFECB3;
            border-radius: 8px;
            margin-bottom: 10px;
        }
        
        .admin-username-text {
            font-weight: bold;
            color: #E65100;
        }
        </style>
        """
        
        # Inject CSS
        st.markdown(css, unsafe_allow_html=True)

def ensure_consistent_padding():
    """Apply consistent padding to all containers"""
    st.markdown("""
    <style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        padding-left: 5rem;
        padding-right: 5rem;
    }
    </style>
    """, unsafe_allow_html=True)

def enforce_fixed_padding():
    """Enforce fixed padding with JavaScript for more reliability"""
    st.markdown("""
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        const style = document.createElement('style');
        style.innerHTML = `
            section[data-testid="stSidebar"] { 
                width: 20rem !important;
            }
            .block-container {
                padding-left: 5rem !important;
                padding-right: 5rem !important;
                max-width: none !important;
            }
        `;
        document.head.appendChild(style);
        
        // Force padding on containers
        function applyPadding() {
            const containers = document.querySelectorAll('.block-container');
            containers.forEach(container => {
                container.style.paddingLeft = '5rem';
                container.style.paddingRight = '5rem';
                container.style.maxWidth = 'none';
            });
        }
        
        // Apply immediately and after a delay to ensure it's applied
        applyPadding();
        setTimeout(applyPadding, 100);
        setTimeout(applyPadding, 500);
    });
    </script>
    """, unsafe_allow_html=True)
