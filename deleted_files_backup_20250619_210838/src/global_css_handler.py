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
    
    /* Enhanced button improvements with rounded styling - APPLIED TO ALL BUTTONS INCLUDING ADMIN PAGES */
    .stButton>button,
    button.css-e12lpz,
    button.st-bq,
    button.st-bu,
    button.st-ae,
    button.st-af,
    .stButton>button[kind="primary"],
    .stSidebar .stButton>button,
    [data-testid="stSidebar"] .stButton>button {
        color: #ffffff !important;
        background-color: #1E88E5 !important;
        border: none !important;
        border-radius: 50px !important;  /* Fully rounded buttons */
        padding: 0.5rem 1.2rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1) !important;
    }
    
    .stButton>button:hover,
    button.css-e12lpz:hover,
    button.st-bq:hover,
    button.st-bu:hover,
    button.st-ae:hover,
    button.st-af:hover,
    .stButton>button[kind="primary"]:hover,
    .stSidebar .stButton>button:hover,
    [data-testid="stSidebar"] .stButton>button:hover {
        background-color: #1565C0 !important;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2) !important;
        transform: translateY(-1px) !important;
    }
    
    /* Admin-specific button styling */
    .admin-page .stButton>button,
    .admin_dashboard .stButton>button,
    #admin-section .stButton>button,
    #quick-access-section .stButton>button,
    div[data-testid="stSidebar"] .stButton>button {
        border-radius: 50px !important;
        padding: 0.5rem 1.2rem !important;
    }
    
    /* Admin username container - UPDATED TO REMOVE BACKGROUND */
    .admin-username-container {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 10px;
        padding: 0.5rem 1.2rem;
        background-color: transparent !important; /* Removed background color */
        border-radius: 8px;
        margin-bottom: 10px;
        height: 38px;
        box-sizing: border-box;
    }
    
    .admin-username-text {
        font-weight: bold;
        color: #E65100;
        line-height: 1;
    }
    
    /* Admin red separator line */
    .admin-red-separator {
        height: 3px;
        background-color: #e53935;
        margin: 15px 0;
        border-radius: 1.5px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12);
    }
    
    /* Admin sidebar specific styling for consistent height */
    [data-testid="stSidebar"] .admin-username-container {
        height: 38px;
        margin-bottom: 16px;
    }
    
    [data-testid="stSidebar"] .stButton > button {
        height: 38px;
        box-sizing: border-box;
    }
    
    /* Username container for consistent header styling */
    .username-container {
        display: flex;
        justify-content: flex-end;
        margin-bottom: 1rem;
    }
    
    /* Updated username text styling for student users */
    .username-text {
        background: linear-gradient(to right, #4CAF50, #2E7D32);
        color: white;
        padding: 8px 15px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.9rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.15);
        text-shadow: 0 1px 1px rgba(0, 0, 0, 0.2);
        border: 1px solid #2E7D32;
    }
    
    /* Professor username text styling with white background */
    .professor-username-text {
        background: white;
        color: #1E88E5;
        padding: 10px 20px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 1rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        border: 1px solid #1E88E5;
        text-align: center;
        margin: 0 auto 15px auto;
        display: inline-block;
    }
    
    /* Professor username container for centered display */
    .professor-username-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-bottom: 1.2rem;
        width: 100%;
    }
    
    /* Remove ALL background colors from tab elements */
    button[data-baseweb="tab"],
    button[data-testid="stTab"],
    button[role="tab"],
    .st-as, .st-at, .st-au, .st-av, .st-aw,
    [data-baseweb="tab"],
    [role="tab"] {
        background-color: transparent !important;
        background-image: none !important;
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
        /* Remove the red border separator */
        border-right: none !important;
        margin-right: 4px !important;
        padding-right: 8px !important;
        position: relative !important;
    }
    
    /* Remove border from last tab */
    button[data-testid="stTab"]:last-child,
    button[data-baseweb="tab"]:last-child,
    [role="tab"]:last-child {
        border-right: none !important;
        margin-right: 0 !important;
    }

    /* Ensure active/selected tab states also have no background */
    button[data-baseweb="tab"][aria-selected="true"],
    button[data-testid="stTab"][aria-selected="true"],
    [role="tab"][aria-selected="true"],
    .st-bs[aria-selected="true"] {
        background-color: transparent !important;
        background-image: none !important;
        box-shadow: none !important;
        border-bottom-color: #ddd !important;
        color: inherit !important;
    }
    
    /* Ensure tab container has padding for the separators */
    div[role="tablist"] {
        padding: 0 5px !important;
        display: flex !important;
        align-items: center !important;
    }
    
    /* Fix hover state to avoid background color */
    button[data-baseweb="tab"]:hover,
    button[data-testid="stTab"]:hover,
    [role="tab"]:hover {
        background-color: transparent !important;
        background-image: none !important;
        color: inherit !important;
        text-decoration: underline !important;
    }
    
    /* Fix tab panel containers */
    [role="tabpanel"],
    [data-testid="stTabContent"] {
        background-color: transparent !important;
        background-image: none !important;
        border: none !important;
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
