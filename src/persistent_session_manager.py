import streamlit as st
import json

class PersistentSessionManager:
    """
    Manages persistent session state across page refreshes
    for usernames, roles, and other critical session data.
    """
    
    @staticmethod
    def ensure_session_persistence():
        """
        Ensures critical session variables like username and role
        are maintained across page refreshes.
        """
        print("PersistentSessionManager: Checking session persistence...")
        
        # STEP 1: Try to restore from query parameters
        # This is the most reliable way since query params persist across refreshes
        username_from_params = st.query_params.get("username")
        role_from_params = st.query_params.get("user_role")
        
        if username_from_params:
            print(f"PersistentSessionManager: Found username in query params: {username_from_params}")
            st.session_state.username = username_from_params
        
        if role_from_params:
            print(f"PersistentSessionManager: Found role in query params: {role_from_params}")
            st.session_state.user_role = role_from_params
            
            # Set role-specific flags
            if role_from_params == "admin":
                st.session_state.is_admin = True
            elif role_from_params == "professor":
                st.session_state.is_professor = True
        
        # STEP 2: Ensure logged_in state is consistent with having username and role
        if st.session_state.get('username') and st.session_state.get('user_role'):
            st.session_state.logged_in = True
        
        # STEP 3: Set query params based on session state if not already set
        # This ensures URL state matches session state
        if st.session_state.get('username') and 'username' not in st.query_params:
            st.query_params['username'] = st.session_state.username
            
        if st.session_state.get('user_role') and 'user_role' not in st.query_params:
            st.query_params['user_role'] = st.session_state.user_role
        
        # STEP 4: Log the current session state
        print("PersistentSessionManager: Current session state:")
        print(f"- Username: {st.session_state.get('username', 'None')}")
        print(f"- Role: {st.session_state.get('user_role', 'None')}")
        print(f"- Logged in: {st.session_state.get('logged_in', False)}")
        
        # Return if session persistence was successful
        return (st.session_state.get('username') is not None and 
                st.session_state.get('user_role') is not None)
                
    @staticmethod
    def inject_session_js():
        """
        Injects JavaScript code to help maintain session across page refreshes.
        """
        # Create JavaScript to persist session into localStorage
        # and restore on page load
        script = """
        <script>
        // On page load, check local storage for session data
        document.addEventListener('DOMContentLoaded', function() {
            console.log("PersistentSessionManager JS: Initializing session persistence...");
            
            // Function to get URL parameters
            function getUrlParameter(name) {
                name = name.replace(/[\[]/, '\\[').replace(/[\]]/, '\\]');
                var regex = new RegExp('[\\?&]' + name + '=([^&#]*)');
                var results = regex.exec(location.search);
                return results === null ? '' : decodeURIComponent(results[1].replace(/\+/g, ' '));
            }
            
            // Get current session info from URL
            const urlUsername = getUrlParameter('username');
            const urlRole = getUrlParameter('user_role');
            
            // If URL has session info, store it in localStorage
            if (urlUsername) {
                localStorage.setItem('streamlit:username', urlUsername);
                console.log("PersistentSessionManager JS: Stored username in localStorage:", urlUsername);
            }
            
            if (urlRole) {
                localStorage.setItem('streamlit:user_role', urlRole);
                console.log("PersistentSessionManager JS: Stored role in localStorage:", urlRole);
            }
            
            // If URL doesn't have session info but localStorage does,
            // add the parameters back to URL
            const storedUsername = localStorage.getItem('streamlit:username');
            const storedRole = localStorage.getItem('streamlit:user_role');
            
            if ((!urlUsername || !urlRole) && (storedUsername || storedRole)) {
                console.log("PersistentSessionManager JS: Restoring session from localStorage");
                
                // Build new URL with session parameters
                const url = new URL(window.location.href);
                
                if (storedUsername && !urlUsername) {
                    url.searchParams.set('username', storedUsername);
                }
                
                if (storedRole && !urlRole) {
                    url.searchParams.set('user_role', storedRole);
                }
                
                if (storedUsername || storedRole) {
                    url.searchParams.set('logged_in', 'True');
                    
                    // Update URL without reloading page
                    window.history.replaceState({}, '', url.toString());
                    console.log("PersistentSessionManager JS: Updated URL with session params");
                }
            }
        });
        
        // Before page unload, ensure session is stored
        window.addEventListener('beforeunload', function() {
            const urlUsername = new URLSearchParams(window.location.search).get('username');
            const urlRole = new URLSearchParams(window.location.search).get('user_role');
            
            if (urlUsername) {
                localStorage.setItem('streamlit:username', urlUsername);
            }
            
            if (urlRole) {
                localStorage.setItem('streamlit:user_role', urlRole);
            }
        });
        </script>
        """
        st.markdown(script, unsafe_allow_html=True)

# Run session persistence check when this module is imported
persistent_session = PersistentSessionManager()
persistent_session.ensure_session_persistence()
persistent_session.inject_session_js()
