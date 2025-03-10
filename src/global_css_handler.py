import streamlit as st

def apply_global_css():
    """
    Apply consistent CSS styling across all pages regardless of user role
    with increased specificity to guarantee padding values
    """
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
    
    /* Other global styles remain unchanged */
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
        margin-bottom: 5px;  /* Changed from 15px to 5px to match professor view */
        padding: 5px;        /* Reduced from 10px to 5px for consistency */
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
    </style>
    """, unsafe_allow_html=True)

# Special function for enforcing padding on student and professor pages
def enforce_fixed_padding():
    """Add extra padding enforcement for student and professor views"""
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

# Add a new function specifically for student report CSS
def apply_student_css():
    """
    Apply CSS styling specific to the student report page
    """
    st.markdown("""
    <style>
    /* Class grid and card styling */
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
    
    /* Make refresh button smaller and aligned right */
    .refresh-container {
        display: flex;
        justify-content: flex-end;
        margin-top: -15px;
        margin-bottom: 10px;
    }
    
    .refresh-container button {
        padding: 0.25rem 0.75rem !important;
        min-height: auto !important;
        font-size: 0.8rem !important;
    }
    
    .refresh-button {
        background-color: #f44336 !important;
        color: white !important;
        border: none !important;
        font-weight: bold !important;
        width: 100% !important;
    }
    
    .refresh-button:hover {
        background-color: #d32f2f !important;
        border: none !important;
    }
    
    .button-row {
        display: flex;
        justify-content: flex-end;
        align-items: center;
        margin-bottom: 10px;
    }
    
    /* Username styling specifically for student view */
    .username-container {
        display: flex;
        justify-content: flex-end;
        align-items: center;
        margin-bottom: 5px;
        padding-bottom: 0;
        margin-right: 10px;
    }
    
    .username-text {
        font-weight: bold;
        font-size: 1.1rem;
        color: #1E88E5;
        margin-right: 10px;
    }
    
    /* Button container with zero spacing */
    .button-container {
        display: flex;
        justify-content: flex-end;
        margin-top: 0;
        padding-top: 0;
    }
    </style>
    """, unsafe_allow_html=True)
