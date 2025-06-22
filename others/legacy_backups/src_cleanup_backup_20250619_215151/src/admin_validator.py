import streamlit as st
import time

def enforce_admin_role():
    """
    Ensures that users with 'admin' in their username always have the admin role.
    Call this function at the start of any page that requires reliable admin access.
    """
    # Get user info from session state
    username = st.session_state.get('username', '')
    current_role = st.session_state.get('user_role', '')
    
    # Check if this should be an admin user
    should_be_admin = (
        username.lower() == "admin" or 
        "admin" in username.lower() or 
        current_role == "admin"
    )
    
    # If they should be admin but don't have admin role, fix it
    if should_be_admin and current_role != "admin":
        print(f"Fixing role for {username}: {current_role} → admin")
        st.session_state.user_role = "admin"
        st.session_state.is_admin = True
        
        # Update query params as well
        st.query_params["user_role"] = "admin"
        
        # Give feedback and refresh
        st.warning("Admin role restored. Refreshing page...")
        time.sleep(1)
        st.rerun()
    
    # Return True if user is admin, False otherwise
    return st.session_state.get('user_role', '') == "admin"

def is_admin():
    """Simple check if current user is admin"""
    # Force admin for users with admin in their name
    username = st.session_state.get('username', '')
    if "admin" in username.lower():
        return True
    
    # Otherwise check role
    return st.session_state.get('user_role', '') == "admin"
