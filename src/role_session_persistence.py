"""
Role Session Persistence Module

This module handles persisting user roles across sessions and page refreshes.
It works with Streamlit's session state and query parameters to ensure
users maintain their proper roles and permissions.
"""
import streamlit as st

def ensure_role_persistence():
    """
    Ensure user roles persist across sessions and page refreshes.
    This function checks for roles in query parameters and maintains them in session state.
    """
    # Check if role info exists in query parameters
    if "user_role" in st.query_params:
        role = st.query_params["user_role"]
        
        # Update session state with role information
        st.session_state.user_role = role
        
        # Set appropriate role flags
        if role == "admin":
            st.session_state.is_admin = True
        elif role == "professor":
            st.session_state.is_professor = True
            
        # Log that we've restored the role
        print(f"Role persistence: Restored {role} role from query parameters")
    
    # Handle direct admin username detection
    if "username" in st.query_params and "admin" in st.query_params["username"].lower():
        st.session_state.user_role = "admin"
        st.session_state.is_admin = True
        print(f"Role persistence: Set admin role based on username: {st.query_params['username']}")
    
    # Ensure the corresponding query params are set if session state has role info
    if "user_role" in st.session_state:
        # Update query params to match session state
        st.query_params["user_role"] = st.session_state.user_role
        print(f"Role persistence: Updated query params with role {st.session_state.user_role}")

def store_role_in_session(username, role):
    """
    Store user role information in session state and query parameters.
    
    Args:
        username (str): User's username
        role (str): User's role (admin, professor, student)
    """
    st.session_state.user_role = role
    
    # Set additional helper flags for common roles
    if role.lower() == "admin":
        st.session_state.is_admin = True
    elif role.lower() == "professor":
        st.session_state.is_professor = True
        
    # Update query params to include role information
    st.query_params["user_role"] = role
    
    # Special handling for admin usernames
    if "admin" in username.lower():
        st.session_state.is_admin = True
        st.session_state.user_role = "admin"
        st.query_params["user_role"] = "admin"
