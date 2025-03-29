"""
Professor view module.

This module provides views for professor users:
- Attendance reporting
- Class management
- Student performance visualization
"""
import streamlit as st
from src.ui.styles import hide_sidebar_for_role
from src.ui.components import create_metric_card

def show_professor_view():
    """Show the professor interface"""
    # Hide sidebar for professors
    hide_sidebar_for_role('professor')
    
    # Show the professor dashboard
    show_professor_dashboard()

def show_professor_dashboard():
    """Show the professor dashboard"""
    # Top navigation bar with title and user info
    top_col1, top_col2 = st.columns([3, 2])
    
    with top_col1:
        st.markdown("## 📚 Teacher Dashboard", unsafe_allow_html=False)
    
    # User info and buttons in column 2
    with top_col2:
        # Username display with right alignment
        username = st.session_state.get('username', 'Unknown')
        st.markdown(f"""
        <div class="username-container">
            <div class="username-text">
                👤 {username}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Refresh and logout buttons side by side
        button_col1, button_col2 = st.columns(2)
        
        with button_col1:
            # Refresh button
            if st.button("🔄 Refresh", key="prof_refresh", use_container_width=True):
                st.rerun()
        
        with button_col2:
            # Logout button
            if st.button("🚪 Logout", key="prof_logout", use_container_width=True):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.query_params.clear()
                st.rerun()
    
    # Import and show the reports module for professors
    import report
    report.show_report()
