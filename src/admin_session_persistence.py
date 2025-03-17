import streamlit as st
import os
import json

def ensure_admin_persistence():
    """
    Ensures that admin users maintain their admin status throughout the session,
    even when the page is refreshed.
    """
    # Check if we're in a valid Streamlit runtime environment
    if not hasattr(st, 'session_state'):
        return False
        
    # Debug information
    print("Admin session check:")
    print(f"- Username: {st.session_state.get('username', 'None')}")
    print(f"- Current role: {st.session_state.get('user_role', 'None')}")
    print(f"- Query params: {st.query_params.to_dict()}")
    
    # Method 1: Check if user is already marked as admin in session state
    if st.session_state.get('user_role') == 'admin':
        print("Admin role detected in session_state")
        # Ensure the admin flag is set
        st.session_state.is_admin = True
        return True
        
    # Method 2: Check username for 'admin' string
    username = st.session_state.get('username', '')
    if username and ('admin' in username.lower() or username.lower() == 'admin'):
        print(f"Admin username detected: {username}")
        # Force admin role in session state
        st.session_state.user_role = 'admin'
        st.session_state.is_admin = True
        # Set query param
        st.query_params.update({'user_role': 'admin'})
        return True
        
    # Method 3: Check query parameters (for refresh persistence)
    if st.query_params.get('user_role') == 'admin':
        print("Admin role detected in query parameters")
        st.session_state.user_role = 'admin'
        st.session_state.is_admin = True
        return True
        
    # Method 4: Check if URL contains admin fragment
    if 'is_admin' in st.session_state:
        print("Admin flag found in session state")
        st.session_state.user_role = 'admin'
        st.query_params.update({'user_role': 'admin'})
        return True
        
    return False

def inject_admin_session_js():
    """Inject JavaScript to help maintain admin session"""
    script = """
    <script>
    // Helper function to check if user is admin
    function isAdminUser() {
        // Check URL for admin indicators
        const url = window.location.href;
        const urlParams = new URLSearchParams(window.location.search);
        return urlParams.get('user_role') === 'admin' || url.includes('admin');
    }
    
    // If admin, ensure we keep that status on refresh
    if (isAdminUser()) {
        // Add admin role parameter to any interactions that might cause refresh
        document.addEventListener('click', function(e) {
            if (e.target && e.target.tagName === 'A' && !e.target.href.includes('user_role=admin')) {
                const url = new URL(e.target.href);
                url.searchParams.set('user_role', 'admin');
                e.target.href = url.toString();
            }
        });
        
        // Also ensure any form submission preserves admin status
        document.addEventListener('submit', function(e) {
            if (e.target && e.target.tagName === 'FORM') {
                const input = document.createElement('input');
                input.type = 'hidden';
                input.name = 'user_role';
                input.value = 'admin';
                e.target.appendChild(input);
            }
        });
        
        // Add listener to detect page refreshes/navigations
        window.addEventListener('beforeunload', function() {
            // Store admin status in sessionStorage (browser's session storage)
            sessionStorage.setItem('is_admin', 'true');
        });
        
        // Check if we're coming back from a refresh
        if (sessionStorage.getItem('is_admin') === 'true') {
            // Ensure the user_role parameter is in URL
            const url = new URL(window.location.href);
            if (!url.searchParams.has('user_role')) {
                url.searchParams.set('user_role', 'admin');
                window.history.replaceState({}, '', url.toString());
            }
        }
    }
    </script>
    """
    st.markdown(script, unsafe_allow_html=True)

# Run the admin session check when this module is imported
ensure_admin_persistence()
