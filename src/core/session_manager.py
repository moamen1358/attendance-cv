"""
Session management for Streamlit application.

This module provides session state management functionality:
- Persistent session storage
- Session state restoration
- Role-based session handling
"""
import streamlit as st
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional

class SessionManager:
    """
    Manages user sessions for the application.
    
    This class provides functionality to persist session state across
    page refreshes and browser restarts, ensuring a seamless user experience.
    """
    
    def __init__(self, storage_dir: str = ".sessions"):
        """
        Initialize the session manager
        
        Args:
            storage_dir: Directory to store session data
        """
        self.storage_dir = storage_dir
        
        # Create storage directory if it doesn't exist
        if not os.path.exists(storage_dir):
            os.makedirs(storage_dir)
    
    def save_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """
        Save session data to persistent storage
        
        Args:
            session_id: Unique session identifier
            data: Session data to save
            
        Returns:
            bool: Success status
        """
        try:
            # Remove non-serializable objects
            serializable_data = {
                k: v for k, v in data.items() 
                if isinstance(v, (str, int, float, bool, list, dict)) or v is None
            }
            
            # Add timestamp
            serializable_data['_last_saved'] = datetime.now().isoformat()
            
            # Save to file
            session_path = os.path.join(self.storage_dir, f"{session_id}.json")
            with open(session_path, 'w') as f:
                json.dump(serializable_data, f)
            
            return True
            
        except Exception as e:
            print(f"Error saving session: {e}")
            return False
    
    def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Load session data from persistent storage
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Optional[Dict[str, Any]]: Loaded session data or None if not found
        """
        try:
            session_path = os.path.join(self.storage_dir, f"{session_id}.json")
            
            if not os.path.exists(session_path):
                return None
            
            with open(session_path, 'r') as f:
                data = json.load(f)
            
            return data
            
        except Exception as e:
            print(f"Error loading session: {e}")
            return None
    
    def clear_session(self, session_id: str) -> bool:
        """
        Clear session data
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            bool: Success status
        """
        try:
            session_path = os.path.join(self.storage_dir, f"{session_id}.json")
            
            if os.path.exists(session_path):
                os.remove(session_path)
            
            return True
            
        except Exception as e:
            print(f"Error clearing session: {e}")
            return False
    
    def get_session_id(self) -> str:
        """
        Get current session ID from Streamlit or generate one
        
        Returns:
            str: Session ID
        """
        # Try to get from query parameters
        if 'session_id' in st.query_params:
            return st.query_params['session_id']
        
        # Get from cookies if available
        # Note: This is a workaround as Streamlit doesn't officially support cookies
        # In a production app, use a more robust session ID generation
        
        # Generate a new session ID if not found
        import uuid
        session_id = str(uuid.uuid4())
        
        # Store in query parameters for persistence
        st.query_params['session_id'] = session_id
        
        return session_id
    
    def ensure_session_persistence(self) -> None:
        """
        Ensure session state is persisted across page refreshes
        """
        session_id = self.get_session_id()
        
        # Check if we should restore session
        if not st.session_state.get('_initialized', False):
            saved_session = self.load_session(session_id)
            
            if saved_session:
                # Restore session state
                for key, value in saved_session.items():
                    if key != '_last_saved' and key != '_initialized':
                        st.session_state[key] = value
                
                st.session_state['_initialized'] = True
        
        # Save current session state
        self.save_session(session_id, dict(st.session_state))

# Create a global session manager instance
session_manager = SessionManager()

def ensure_role_persistence():
    """
    Ensure user role is persisted correctly
    """
    # Restore role from query parameters if present
    if "user_role" in st.query_params:
        role = st.query_params["user_role"]
        st.session_state.user_role = role
        
        if role == "admin":
            st.session_state.is_admin = True
        elif role == "professor":
            st.session_state.is_professor = True
