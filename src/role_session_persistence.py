import streamlit as st
import os
import json

def ensure_role_persistence():
    """
    Ensures that users maintain their role throughout the session,
    even when the page is refreshed.
    """
    # Check if we're in a valid Streamlit runtime environment
    if not hasattr(st, 'session_state'):
        return False
        
    # Debug information
    print("Role session check:")
    print(f"- Username: {st.session_state.get('username', 'None')}")
    print(f"- Current role: {st.session_state.get('user_role', 'None')}")
    print(f"- Query params: {st.query_params.to_dict()}")
    
    # ADMIN PERSISTENCE
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
        
    # Method 3: Check query parameters for admin (for refresh persistence)
    if st.query_params.get('user_role') == 'admin':
        print("Admin role detected in query parameters")
        st.session_state.user_role = 'admin'
        st.session_state.is_admin = True
        return True
    
    # PROFESSOR PERSISTENCE
    # Method 1: Check if user has professor role in session state
    if st.session_state.get('user_role') == 'professor':
        print("Professor role detected in session_state")
        st.session_state.is_professor = True
        # Make sure query params are updated
        st.query_params.update({'user_role': 'professor'})
        return True
        
    # Method 2: Check query params for professor role
    if st.query_params.get('user_role') == 'professor':
        print("Professor role detected in query parameters")
        st.session_state.user_role = 'professor'
        st.session_state.is_professor = True
        return True
        
    # Method 3: Check for professor username patterns (optional)
    if username and ('prof' in username.lower() or 'teacher' in username.lower() or 'instructor' in username.lower()):
        print(f"Professor username detected: {username}")
        if st.session_state.get('user_role', '') != 'admin':  # Don't override admin role
            st.session_state.user_role = 'professor'
            st.session_state.is_professor = True
            st.query_params.update({'user_role': 'professor'})
            return True
    
    # Method 4: Check if URL contains professor role fragment via is_professor flag
    if 'is_professor' in st.session_state:
        print("Professor flag found in session state")
        st.session_state.user_role = 'professor'
        st.query_params.update({'user_role': 'professor'})
        return True
        
    # If we get here, try to recover from session storage via JS
    inject_role_persistence_js()
    
    # If we have an explicitly set role in session, ensure it's in query params
    current_role = st.session_state.get('user_role')
    if current_role and current_role not in st.query_params.get('user_role', ''):
        st.query_params['user_role'] = current_role
        print(f"Restoring {current_role} role from session state to query params")
    
    # If user has a username but role is unknown/None, restore from database
    if username and (not st.session_state.get('user_role') or 
                    st.session_state.get('user_role') == 'Unknown'):
        role = get_user_role_from_database(username)
        if role:
            st.session_state.user_role = role
            print(f"Restored role {role} from database for user {username}")
            if role == 'professor':
                st.session_state.is_professor = True
                st.query_params.update({'user_role': 'professor'})
            elif role == 'admin':
                st.session_state.is_admin = True
                st.query_params.update({'user_role': 'admin'})
            return True
            
    return False

def inject_role_persistence_js():
    """Inject JavaScript to help maintain role session across refreshes"""
    script = """
    <script>
    // Helper function to check user role
    function getUserRole() {
        const urlParams = new URLSearchParams(window.location.search);
        const role = urlParams.get('user_role');
        return role || window.sessionStorage.getItem('user_role') || 'unknown';
    }
    
    // Get the current role
    const currentRole = getUserRole();
    
    console.log("Current role detected by JS:", currentRole);
    
    // Store role in sessionStorage when page is about to be refreshed or navigated away
    if (currentRole !== 'unknown') {
        // Store role in session storage for persistence
        window.sessionStorage.setItem('user_role', currentRole);
        
        // Add role parameter to any interactions that might cause refresh
        document.addEventListener('click', function(e) {
            if (e.target && e.target.tagName === 'A') {
                try {
                    const url = new URL(e.target.href);
                    url.searchParams.set('user_role', currentRole);
                    e.target.href = url.toString();
                } catch (err) {
                    // Not a valid URL, ignore
                }
            }
        });
        
        // Also ensure any form submission preserves role
        document.addEventListener('submit', function(e) {
            if (e.target && e.target.tagName === 'FORM') {
                const input = document.createElement('input');
                input.type = 'hidden';
                input.name = 'user_role';
                input.value = currentRole;
                e.target.appendChild(input);
            }
        });
        
        // Add listener to detect page refreshes/navigations
        window.addEventListener('beforeunload', function() {
            // Store role in sessionStorage (browser's session storage)
            sessionStorage.setItem('user_role', currentRole);
        });
        
        // Check if we're coming back from a refresh
        if (sessionStorage.getItem('user_role')) {
            // Ensure the user_role parameter is in URL
            const savedRole = sessionStorage.getItem('user_role');
            const url = new URL(window.location.href);
            if (!url.searchParams.has('user_role') || url.searchParams.get('user_role') !== savedRole) {
                url.searchParams.set('user_role', savedRole);
                window.history.replaceState({}, '', url.toString());
            }
        }
    }
    </script>
    """
    st.markdown(script, unsafe_allow_html=True)

def get_user_role_from_database(username):
    """Retrieve user role directly from database as a fallback"""
    try:
        import sqlite3
        conn = sqlite3.connect('attendance_system.db')
        cursor = conn.cursor()
        
        # Check for role in user_accounts table
        cursor.execute("SELECT role FROM user_accounts WHERE username = ?", (username,))
        result = cursor.fetchone()
        
        if result:
            return result[0]
            
        # Additional checks could be added for other tables if needed
        
    except Exception as e:
        print(f"Error retrieving role from database: {e}")
    finally:
        if 'conn' in locals():
            conn.close()
    
    return None

# Run the role persistence check when this module is imported
ensure_role_persistence()
