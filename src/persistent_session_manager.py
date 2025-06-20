"""
Persistent Session Manager

This module handles Streamlit session state persistence across page refreshes
by using browser storage and query parameters.
"""
import streamlit as st
import json
from datetime import datetime

class PersistentSessionManager:
    """
    A class to manage session persistence for Streamlit applications.
    Ensures user sessions are maintained across page refreshes.
    """
    
    def __init__(self):
        """Initialize the session manager."""
        self.stored_keys = [
            'logged_in', 'username', 'user_role', 'is_admin', 
            'is_professor', 'current_page'
        ]
    
    def ensure_session_persistence(self):
        """
        Restore session state from query parameters if available.
        This should be called at the start of the application.
        """
        # Check if we have query parameters to restore from
        if "logged_in" in st.query_params and st.query_params["logged_in"] == "True":
            # Restore basic login state
            st.session_state.logged_in = True
            
            # Restore username if available
            if "username" in st.query_params:
                st.session_state.username = st.query_params["username"]
            
            # Restore role if available
            if "user_role" in st.query_params:
                role = st.query_params["user_role"]
                st.session_state.user_role = role
                
                # Set role-specific flags
                if role == "admin":
                    st.session_state.is_admin = True
                elif role == "professor":
                    st.session_state.is_professor = True
                
            # Restore admin flag explicitly if available
            if "is_admin" in st.query_params and st.query_params["is_admin"] == "true":
                st.session_state.is_admin = True
                st.session_state.user_role = "admin"
            
            # Restore professor flag explicitly if available
            if "is_professor" in st.query_params and st.query_params["is_professor"] == "true":
                st.session_state.is_professor = True
                if "user_role" not in st.session_state:
                    st.session_state.user_role = "professor"
    
    def inject_session_js(self):
        """
        Inject JavaScript to enhance session persistence using browser storage.
        This provides an additional layer of persistence beyond query parameters.
        """
        # Skip JavaScript injection for student users to avoid display issues
        if st.session_state.get('user_role') == 'student':
            return
            
        # Create a JSON representation of key session variables
        session_data = {}
        for key in self.stored_keys:
            if key in st.session_state:
                # Convert non-serializable types to strings
                if isinstance(st.session_state[key], datetime):
                    session_data[key] = st.session_state[key].isoformat()
                else:
                    session_data[key] = st.session_state[key]
        
        # Only inject if we have data to store
        if session_data:
            session_json = json.dumps(session_data)
            
            # JavaScript to store and retrieve session data
            js_code = f"""
            <script>
                // Store current session data
                const sessionData = {session_json};
                localStorage.setItem('streamlitSessionData', JSON.stringify(sessionData));
                
                // Function to restore session on page load
                window.addEventListener('load', function() {{
                    // Check if URL already has parameters
                    const hasParams = window.location.search.includes('logged_in=True');
                    if (!hasParams) {{
                        // Try to get stored session
                        const storedData = localStorage.getItem('streamlitSessionData');
                        if (storedData) {{
                            try {{
                                const sessionData = JSON.parse(storedData);
                                // Only redirect if user was logged in
                                if (sessionData.logged_in) {{
                                    // Construct redirect URL with query parameters
                                    let url = '?logged_in=True';
                                    if (sessionData.username) url += '&username=' + encodeURIComponent(sessionData.username);
                                    if (sessionData.user_role) url += '&user_role=' + encodeURIComponent(sessionData.user_role);
                                    
                                    // Add other flags if present
                                    if (sessionData.is_admin) url += '&is_admin=true';
                                    if (sessionData.is_professor) url += '&is_professor=true';
                                    
                                    // Redirect to preserve session
                                    window.location.href = url;
                                }}
                            }} catch (e) {{
                                console.error('Error parsing stored session:', e);
                            }}
                        }}
                    }}
                }});
            </script>
            """
            
            st.markdown(js_code, unsafe_allow_html=True)

# Module-level function to initialize session persistence (called explicitly in app.py)
def initialize_session_persistence():
    """Initialize session persistence - should be called explicitly in app.py"""
    # Skip for student users
    if st.session_state.get('user_role') == 'student':
        return
        
    persistent_session = PersistentSessionManager()
    persistent_session.ensure_session_persistence()
    persistent_session.inject_session_js()
