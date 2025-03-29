"""
Base view class for the application.

This module provides a base class for views with common functionality.
"""
import streamlit as st
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

from src.core.error_handling import handle_errors, ErrorContext
from src.ui.styles import apply_global_css, ensure_consistent_padding

class BaseView(ABC):
    """
    Base class for all views in the application
    
    This class provides common functionality for views including:
    - Error handling
    - Consistent styling
    - Navigation
    - User session handling
    """
    
    def __init__(self, title: str = "View"):
        """
        Initialize the view
        
        Args:
            title: Title of the view
        """
        self.title = title
        self.username = st.session_state.get('username', 'Unknown')
        self.user_role = st.session_state.get('user_role', 'Unknown')
        self.is_admin = st.session_state.get('is_admin', False)
        self.is_professor = st.session_state.get('is_professor', False)

    @handle_errors
    def render(self):
        """Render the view with global styling and error handling"""
        # Apply global styles
        apply_global_css()
        ensure_consistent_padding()
        
        # Page content
        with ErrorContext(f"rendering {self.title}"):
            self._render_content()
    
    @abstractmethod
    def _render_content(self):
        """Render the view content (to be implemented by subclasses)"""
        pass
    
    def render_top_bar(self):
        """Render a consistent top navigation bar"""
        top_col1, top_col2 = st.columns([3, 2])
        
        with top_col1:
            st.markdown(f"## {self.title}")
        
        with top_col2:
            # Username display with right alignment
            st.markdown(f"""
            <div class="username-container">
                <div class="username-text">
                    👤 {self.username} ({self.user_role.capitalize()})
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Action buttons side by side
            button_col1, button_col2 = st.columns(2)
            
            with button_col1:
                # Refresh button with same style as logout
                if st.button("🔄 Refresh", key=f"{self.__class__.__name__}_refresh", use_container_width=True):
                    st.rerun()
            
            with button_col2:
                # Logout button
                if st.button("🚪 Logout", key=f"{self.__class__.__name__}_logout", use_container_width=True):
                    self.logout()
    
    def logout(self):
        """Log out the user"""
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.query_params.clear()
        st.rerun()
