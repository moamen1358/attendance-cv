"""
Application Startup Module

This module runs at the application startup to ensure consistent layouts and settings
are applied before any other code executes.
"""
import streamlit as st
from global_css_handler import apply_global_css, enforce_fixed_padding

def initialize_app():
    """
    Initialize application settings and layout preferences
    """
    # Always apply full-width layout at startup
    apply_global_css()
    enforce_fixed_padding()
    
    # Set up JavaScript for persistent full-width layout
    st.markdown("""
    <script>
        // Ensure full width layout persists across all pages and sessions
        (function() {
            // Function to enforce full width
            function enforceFullWidth() {
                // Apply to all relevant containers
                document.querySelectorAll('.block-container, .main .block-container').forEach(el => {
                    el.style.maxWidth = '100%';
                    el.style.width = '100%';
                    el.style.paddingLeft = '40px';
                    el.style.paddingRight = '40px';
                });
                
                // Apply to all charts, tables and elements
                document.querySelectorAll('.element-container, [data-testid="stDataFrame"], .js-plotly-plot').forEach(el => {
                    el.style.maxWidth = '100%';
                    el.style.width = '100%';
                });
            }
            
            // Apply immediately
            enforceFullWidth();
            
            // Apply on window load
            window.addEventListener('load', enforceFullWidth);
            
            // Apply periodically
            setInterval(enforceFullWidth, 1000);
            
            // Save to session and localStorage
            sessionStorage.setItem('fullWidthLayout', 'enabled');
            localStorage.setItem('fullWidthLayout', 'enabled');
            
            // Set a cookie for persistence across sessions
            document.cookie = "fullWidthLayout=enabled; path=/; max-age=31536000";
        })();
    </script>
    """, unsafe_allow_html=True)

# Run initialization immediately when this module is imported
initialize_app()
