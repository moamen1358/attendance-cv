"""
Reusable UI components for the application.

This module provides reusable UI components:
- Cards and containers
- Navigation components
- Data visualization helpers
- Status indicators
"""
import streamlit as st
import pandas as pd
from typing import Dict, List, Any, Optional

def create_card(title: str, content: str, icon: str = "📄"):
    """
    Create a styled card with title and content
    
    Args:
        title: Card title
        content: Card content text
        icon: Emoji or icon for the card
    """
    st.markdown(f"""
    <div class="card">
        <h3>{icon} {title}</h3>
        <p>{content}</p>
    </div>
    """, unsafe_allow_html=True)

def create_metric_card(value: Any, label: str, color: str = "#1f77b4"):
    """
    Create a metric card with highlighted value
    
    Args:
        value: Metric value to display
        label: Description of the metric
        color: Accent color for the card
    """
    st.markdown(f"""
    <div class="metric-card" style="border-top: 3px solid {color}">
        <div class="metric-value" style="color: {color}">{value}</div>
        <div class="metric-label">{label}</div>
    </div>
    """, unsafe_allow_html=True)

def create_sidebar_navigation(pages: Dict[str, Any], current_page: Optional[str] = None):
    """
    Create sidebar navigation with the specified pages
    
    Args:
        pages: Dictionary mapping page names to view functions
        current_page: Currently selected page
        
    Returns:
        str: Selected page name
    """
    # Get current page or default to first page
    current = current_page or list(pages.keys())[0]
    selected_index = list(pages.keys()).index(current) if current in pages else 0
    
    # Create navigation
    with st.sidebar:
        # Get username if available
        username = st.session_state.get('username', 'User')
        user_role = st.session_state.get('user_role', 'Unknown')
        
        # Display username
        st.markdown(f"""
        <div class="admin-username-container">
            <span style="font-size: 24px;">👤</span>
            <span class="admin-username-text">{username} ({user_role.title()})</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Logout button
        if st.button("🚪 Logout", key="sidebar_logout", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.query_params.clear()
            st.rerun()
        
        # Divider
        st.markdown("<hr style='margin: 5px 0; opacity: 0.3;'>", unsafe_allow_html=True)
        
        # Navigation
        selection = st.radio("Navigation", list(pages.keys()), index=selected_index)
        
    return selection

def create_status_indicator(status: str):
    """
    Create a status indicator dot
    
    Args:
        status: Status value (active, inactive, pending)
    """
    status_class = {
        'active': 'status-active',
        'inactive': 'status-inactive',
        'pending': 'status-pending'
    }.get(status.lower(), 'status-inactive')
    
    return f"""
    <span class="status-indicator {status_class}"></span>
    <span>{status.title()}</span>
    """

def create_data_table(data: pd.DataFrame, use_container_width: bool = True):
    """
    Create a styled data table
    
    Args:
        data: DataFrame to display
        use_container_width: Whether to use full container width
    """
    # Add index column if not present
    if 'id' not in data.columns and 'ID' not in data.columns and data.index.name != 'id':
        data = data.reset_index().rename(columns={'index': 'ID'})
    
    # Display the table
    st.dataframe(
        data,
        use_container_width=use_container_width,
        hide_index=('id' in data.columns or 'ID' in data.columns)
    )
