import streamlit as st

def apply_global_css():
    """
    Apply consistent CSS styling across all pages regardless of user role
    with increased specificity to guarantee padding values
    
    Uses session state to ensure CSS is only applied once per session
    """
    # Check if CSS has already been applied this session
    if 'css_applied' not in st.session_state:
        st.session_state.css_applied = True
        
        # This function should be called only ONCE per page
        st.markdown("""
        <style>
        /* GLOBAL PADDING ENFORCEMENT - Max specificity */
        .main .block-container,
        [data-testid="stAppViewBlockContainer"] .main .block-container,
        body .main .block-container,
        body [data-testid="stAppViewBlockContainer"] > div > div > div > .block-container,
        body > div[class*="appview"] > section > div > div > div > div > div.block-container {
            padding-top: 1rem !important;
            padding-bottom: 1rem !important;
            padding-left: 80px !important;
            padding-right: 80px !important;
            max-width: unset !important;
        }
        
        /* Hide sidebar properly */
        section[data-testid="stSidebar"][aria-expanded="false"] {
            display: none !important;
            width: 0px !important;
            margin-left: 0px !important;
            padding-left: 0px !important;
        }
        
        /* Hard-fix for containers with any special styling */
        div.stApp > div[data-testid="stAppViewContainer"] > section > div > div[data-testid="stVerticalBlock"] > div[style*="padding"] {
            padding-left: 80px !important;
            padding-right: 80px !important;
        }
        
        /* Prevent Streamlit's auto-adjustments when sidebar is toggled */
        [data-testid="stAppViewBlockContainer"] {
            padding-left: 0px !important;
            padding-right: 0px !important;
        }
        
        /* Remove transitions to prevent flickering */
        section[data-testid="stSidebar"],
        div[data-testid="stDecoration"],
        div.block-container,
        div[data-testid="stVerticalBlock"] {
            transition: none !important;
        }
        
        /* Ensure sidebar padding is controlled when visible */
        section[data-testid="stSidebar"] .block-container {
            padding-left: 20px !important;
            padding-right: 20px !important;
            text-align: center;
        }
        
        /* Consistent spacing between sections */
        .main .block-container > div > div[data-testid="stVerticalBlock"] > div[data-stale="false"] {
            margin-top: 1rem !important;
        }
        
        /* Button styling */
        .stButton button {
            background-color: #f44336;
            color: white;
            border: none;
            font-weight: bold;
        }
        
        .stButton button:hover {
            background-color: #d32f2f;
            border: none;
        }
        
        /* Username styling for ALL roles */
        .username-container {
            text-align: right;
            margin-bottom: 5px;
            padding-bottom: 0;
            margin-right: 75px;
        }
        
        .username-text {
            font-weight: bold;
            font-size: 1.1rem;
            color: #1E88E5;
            display: inline-block;
        }
        
        /* Admin-specific styles - adjusted margin to match professor view */
        .admin-username-container {
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 5px;
            padding: 5px;
            width: 100%;
            background: transparent;
            text-align: center;
        }
        
        .admin-username-text {
            font-weight: bold;
            font-size: 1.2rem;
            color: #1E88E5;
            margin-left: 8px;
        }
        
        /* Override any page-specific padding attempts */
        body {
            --sidebar-width: 21rem;
        }
        
        /* Student-specific styles moved from apply_student_css to avoid duplication */
        .class-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            grid-gap: 15px;
            margin-bottom: 15px;
        }
        
        .class-card {
            height: 100%;
            transition: transform 0.2s ease;
        }
        
        .class-card:hover {
            transform: translateY(-3px);
        }
        
        /* Force absolutely no space for the first element - specific to student view */
        .element-container:first-child,
        .stMarkdown:first-child,
        .main .stMarkdown:first-child > div:first-child > p:first-child,
        .element-container:first-of-type {
            margin-top: 0 !important;
            padding-top: 0 !important;
            line-height: 0 !important;
            height: auto !important;
            min-height: 0 !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Also include the JS that was in enforce_fixed_padding to avoid multiple calls
        st.markdown("""
        <script>
        // Run immediately and also after any changes
        function enforcePagePadding() {
            // Force consistent padding with JavaScript too
            const containers = document.querySelectorAll('.block-container');
            containers.forEach(container => {
                container.style.setProperty('padding-left', '80px', 'important');
                container.style.setProperty('padding-right', '80px', 'important');
            });
        }
        
        // Run immediately
        enforcePagePadding();
        
        // Set up an observer to detect DOM changes
        const observer = new MutationObserver(function(mutations) {
            enforcePagePadding();
        });
        
        // Start observing the document for changes
        observer.observe(document.body, { 
            childList: true,
            subtree: true
        });
        </script>
        """, unsafe_allow_html=True)
    
    # If CSS has already been applied, do nothing

# Keep these functions as empty functions for backward compatibility
def enforce_fixed_padding():
    """
    Empty function for backward compatibility - 
    All functionality now in apply_global_css()
    """
    pass

def apply_student_css():
    """
    Empty function for backward compatibility - 
    All functionality now in apply_global_css()
    """
    pass

# Add a function to reset the CSS flag (useful for testing)
def reset_css_flag():
    """Reset the CSS application flag to force reapplication of CSS"""
    if 'css_applied' in st.session_state:
        del st.session_state.css_applied
