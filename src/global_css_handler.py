"""
Global CSS Handler Module

This module provides consistent styling across the application
by injecting CSS into Streamlit pages.
"""
import streamlit as st

def apply_global_css():
    """Apply global CSS to Streamlit app for consistent styling"""
    # REMOVED session state check to ensure CSS is ALWAYS applied on every page load
    
    # Define CSS styles
    css = """
    <style>
    /* Force full width layout on all pages */
    .reportview-container .main .block-container,
    .appview-container .main .block-container,
    div[data-testid="stAppViewContainer"] > section[data-testid="stAppViewContainer"] > div,
    div[data-testid="stAppViewContainer"] > section > div,
    .main .block-container,
    .block-container {
        max-width: 100% !important;
        padding-left: 40px !important;
        padding-right: 40px !important;
        width: 100% !important;
    }
    
    /* Override any Streamlit-specific container classes */
    .css-1d391kg, .css-12oz5g7, .css-1r6slb0, .css-18e3th9, .css-1d8a290 {
        max-width: 100% !important;
        width: 100% !important;
        padding-left: 40px !important;
        padding-right: 40px !important;
    }
    
    /* Ensure stDataFrame components use full width */
    [data-testid="stDataFrame"] {
        width: 100% !important;
        max-width: 100% !important;
    }
    
    /* Ensure plotly charts use full width */
    .js-plotly-plot, .plot-container {
        width: 100% !important;
        max-width: 100% !important;
    }
    
    /* Ensure tables use full width */
    .dataframe {
        width: 100% !important;
        max-width: 100% !important;
    }

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

    # Always also apply JavaScript to force full width - this will persist across sessions
    st.markdown("""
    <script>
        (function() {
            // Function to apply full width
            function enforceFullWidth() {
                // Override all container widths
                const style = document.createElement('style');
                style.textContent = `
                    .main .block-container, 
                    .block-container,
                    div[data-testid="stAppViewContainer"] > section > div,
                    .css-1d391kg, .css-12oz5g7, .css-1r6slb0, .css-18e3th9 {
                        max-width: 100% !important;
                        padding-left: 40px !important;
                        padding-right: 40px !important;
                        width: 100% !important;
                    }
                    
                    [data-testid="stDataFrame"], 
                    .js-plotly-plot, 
                    .plot-container,
                    .element-container,
                    .dataframe {
                        width: 100% !important;
                        max-width: 100% !important;
                    }
                `;
                document.head.appendChild(style);
                
                // Apply styles directly to elements
                document.querySelectorAll('.block-container, .main .block-container, [data-testid="stAppViewContainer"] > section > div').forEach(el => {
                    el.style.maxWidth = '100%';
                    el.style.width = '100%';
                    el.style.paddingLeft = '40px';
                    el.style.paddingRight = '40px';
                });
            }
            
            // Apply immediately
            enforceFullWidth();
            
            // Apply again after a delay to handle dynamic content
            setTimeout(enforceFullWidth, 100);
            setTimeout(enforceFullWidth, 500);
            setTimeout(enforceFullWidth, 2000);
            
            // Create a persistent observer to reapply whenever the DOM changes
            const observer = new MutationObserver(enforceFullWidth);
            observer.observe(document.body, { 
                childList: true, 
                subtree: true 
            });
            
            // Store in sessionStorage that we've initialized (persistent across page navigation)
            sessionStorage.setItem('fullWidthInitialized', 'true');
            
            // Also try to set a cookie for persistence across logins
            document.cookie = "fullWidthLayout=enabled; path=/; max-age=31536000"; // 1 year
        })();
    </script>
    """, unsafe_allow_html=True)

def ensure_consistent_padding():
    """Apply consistent padding to all containers"""
    st.markdown("""
    <style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        padding-left: 40px !important;
        padding-right: 40px !important;
        max-width: 100% !important;
        width: 100% !important;
    }
    
    .main .block-container {
        max-width: 100% !important;
        width: 100% !important;
    }
    </style>
    """, unsafe_allow_html=True)

def enforce_fixed_padding():
    """Enforce fixed padding with JavaScript for more reliability"""
    st.markdown("""
    <script>
    (function() {
        // Function to apply full width and padding
        function applyFullWidth() {
            // Apply to all containers
            const containers = document.querySelectorAll('.block-container');
            containers.forEach(container => {
                container.style.paddingLeft = '40px';
                container.style.paddingRight = '40px';
                container.style.maxWidth = '100%';
                container.style.width = '100%';
            });
            
            // Make all dataframes and charts full width
            const dataContainers = document.querySelectorAll('[data-testid="stDataFrame"], .js-plotly-plot, .element-container');
            dataContainers.forEach(container => {
                container.style.maxWidth = '100%';
                container.style.width = '100%';
            });
            
            // Force vertical blocks to be full width
            const verticalBlocks = document.querySelectorAll('[data-testid="stVerticalBlock"]');
            verticalBlocks.forEach(block => {
                block.style.maxWidth = '100%';
                block.style.width = '100%';
            });
            
            // Hide sidebar if needed
            const sidebar = document.querySelector('[data-testid="stSidebar"]');
            if (sidebar) {
                sidebar.style.display = 'none';
            }
        }
        
        // Apply immediately
        applyFullWidth();
        
        // Apply again after delays to catch dynamic content
        setTimeout(applyFullWidth, 100);
        setTimeout(applyFullWidth, 500);
        setTimeout(applyFullWidth, 1000);
        setTimeout(applyFullWidth, 2000);
        
        // Set up persistent observer
        const observer = new MutationObserver(applyFullWidth);
        observer.observe(document.body, { childList: true, subtree: true });
        
        // Store in localStorage to maintain across sessions
        localStorage.setItem('fullWidthEnforced', 'true');
    })();
    </script>
    """, unsafe_allow_html=True)
