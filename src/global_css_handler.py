import streamlit as st

def apply_global_css():
    """Apply global CSS styling to all pages"""
    st.markdown("""
    <style>
    /* Global CSS for consistent appearance */
    body {
        font-family: 'Roboto', sans-serif;
    }
    
    /* Additional styles can be added here */
    </style>
    """, unsafe_allow_html=True)

def enforce_fixed_padding():
    """Force consistent 80px padding on both sides with aggressive approach"""
    st.markdown("""
    <style>
    /* Super-aggressive force 80px padding on both sides with maximum specificity */
    body .main .block-container,
    .main .block-container,
    div.block-container,
    [data-testid="stAppViewBlockContainer"] div.block-container,
    #root > div:nth-child(1) > div > div > div > section > div > div > div > div > div.block-container,
    section[data-testid="stVerticalBlock"] > div > div > div,
    .element-container .stBlock > div > div,
    .main > div > div > div > div:not([data-testid="stSidebar"]) div.block-container,
    [data-testid="stAppViewContainer"] .main .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        padding-left: 80px !important;
        padding-right: 80px !important;
        max-width: unset !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Also add JavaScript to ensure padding after the page fully loads
    st.markdown("""
    <script>
    // Run this script after the DOM is fully loaded
    document.addEventListener('DOMContentLoaded', function() {
        function enforcePadding() {
            // Get all possible container elements
            const containers = document.querySelectorAll('.block-container, [data-testid="stAppViewBlockContainer"] div.block-container');
            
            // Apply the padding to each container
            containers.forEach(function(container) {
                container.style.setProperty('padding-left', '80px', 'important');
                container.style.setProperty('padding-right', '80px', 'important');
                container.style.setProperty('max-width', 'unset', 'important');
            });
        }
        
        // Apply immediately 
        enforcePadding();
        
        // Apply again after a short delay to catch any late-loading elements
        setTimeout(enforcePadding, 100);
        setTimeout(enforcePadding, 500);
        setTimeout(enforcePadding, 1000);
        
        // Apply when the window is resized
        window.addEventListener('resize', enforcePadding);
        
        // Create a MutationObserver to detect DOM changes and reapply padding
        const observer = new MutationObserver(function(mutations) {
            enforcePadding();
        });
        
        // Start observing the body for changes
        observer.observe(document.body, { 
            childList: true, 
            subtree: true 
        });
    });
    </script>
    """, unsafe_allow_html=True)

# Function to apply padding to any page
def ensure_consistent_padding():
    """Call this at the beginning of each page to ensure consistent padding"""
    if 'padding_enforced' not in st.session_state:
        enforce_fixed_padding()
        st.session_state.padding_enforced = True
    
    # Re-apply CSS on every page load to be absolutely sure
    enforce_fixed_padding()

# Keep these functions as empty functions for backward compatibility
def apply_student_css():
    """
    Empty function for backward compatibility - 
    All functionality now in apply_global_css()
    """
    enforce_fixed_padding()  # Make sure we still enforce padding even when this is called
    pass

# Add a function to reset the CSS flag (useful for testing)
def reset_css_flag():
    """Reset the CSS application flag to force reapplication of CSS"""
    if 'css_applied' in st.session_state:
        del st.session_state.css_applied
    if 'padding_enforced' in st.session_state:
        del st.session_state.padding_enforced
