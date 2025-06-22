"""
Professional Academic Management System - Main Application
=========================================================
This is the main entry point for the professional academic management system
with the new database structure and enhanced functionality.
"""

import streamlit as st
import sqlite3
import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))

def initialize_professional_system():
    """Initialize the professional academic system"""
    st.set_page_config(
        page_title="Professional Academic Management System",
        page_icon="🎓",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for professional look
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #3b82f6;
    }
    .nav-button {
        width: 100%;
        margin: 0.25rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

def check_database_structure():
    """Check if the professional database structure exists"""
    try:
        conn = sqlite3.connect('attendance_system.db')
        cursor = conn.cursor()
        
        # Check for key professional tables
        professional_tables = [
            'academic_terms', 'departments', 'subjects_new', 
            'classes', 'student_classes', 'attendance_sessions'
        ]
        
        existing_tables = []
        for table in professional_tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if cursor.fetchone():
                existing_tables.append(table)
        
        conn.close()
        
        return len(existing_tables) == len(professional_tables), existing_tables
        
    except Exception as e:
        st.error(f"Database error: {e}")
        return False, []

def show_system_status():
    """Show system status and setup if needed"""
    st.markdown('<div class="main-header"><h1>🎓 Professional Academic Management System</h1></div>', 
                unsafe_allow_html=True)
    
    # Check database structure
    is_professional, existing_tables = check_database_structure()
    
    if not is_professional:
        st.warning("⚠️ Professional database structure not detected!")
        st.info("This system requires the professional database structure. Please run the database restructure script first.")
        
        with st.expander("💡 How to Setup Professional Database"):
            st.markdown("""
            1. Run the database restructure script:
            ```bash
            python professional_database_restructure.py
            ```
            
            2. This will create:
            - Academic terms and departments
            - Professional class management
            - Student enrollment system
            - Advanced attendance tracking
            - Performance optimizations
            """)
        
        st.code("python professional_database_restructure.py", language="bash")
        
        if st.button("🔄 Check Database Status Again"):
            st.experimental_rerun()
        
        return False
    
    else:
        st.success("✅ Professional database structure detected!")
        
        # Show system metrics
        col1, col2, col3, col4 = st.columns(4)
        
        try:
            conn = sqlite3.connect('attendance_system.db')
            
            with col1:
                students = conn.execute("SELECT COUNT(*) FROM student_profiles").fetchone()[0]
                st.metric("👥 Students", students)
            
            with col2:
                classes = conn.execute("SELECT COUNT(*) FROM classes WHERE status = 'active'").fetchone()[0]
                st.metric("📚 Active Classes", classes)
            
            with col3:
                enrollments = conn.execute("SELECT COUNT(*) FROM student_classes WHERE status = 'enrolled'").fetchone()[0]
                st.metric("📝 Enrollments", enrollments)
            
            with col4:
                attendance = conn.execute("SELECT COUNT(*) FROM attendance_records_new").fetchone()[0]
                st.metric("📊 Attendance Records", attendance)
            
            conn.close()
            
        except Exception as e:
            st.error(f"Error fetching metrics: {e}")
        
        return True

def show_navigation():
    """Show main navigation"""
    st.sidebar.title("🎓 Academic System")
    st.sidebar.markdown("---")
    
    # Main navigation options
    nav_options = {
        "🏠 Dashboard": "dashboard",
        "👥 Student Management": "students",
        "📚 Class Management": "classes", 
        "📊 Attendance Management": "attendance",
        "📈 Analytics & Reports": "analytics",
        "🔧 Database Explorer": "explorer",
        "⚙️ System Settings": "settings"
    }
    
    selected = st.sidebar.selectbox("Navigate to:", list(nav_options.keys()))
    
    return nav_options[selected]

def show_dashboard():
    """Show main dashboard"""
    st.header("🏠 Dashboard")
    
    # Quick stats
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Today's Overview")
        try:
            conn = sqlite3.connect('attendance_system.db')
            
            # Today's attendance sessions
            today_sessions = conn.execute("""
                SELECT COUNT(*) FROM attendance_sessions 
                WHERE session_date = DATE('now')
            """).fetchone()[0]
            
            # Today's attendance records
            today_attendance = conn.execute("""
                SELECT COUNT(*) FROM attendance_records_new ar
                JOIN attendance_sessions ats ON ar.session_id = ats.session_id
                WHERE ats.session_date = DATE('now')
            """).fetchone()[0]
            
            st.metric("Sessions Today", today_sessions)
            st.metric("Attendance Records Today", today_attendance)
            
            conn.close()
            
        except Exception as e:
            st.error(f"Error loading today's data: {e}")
    
    with col2:
        st.subheader("🎯 Quick Actions")
        
        if st.button("👥 View All Students", use_container_width=True):
            st.session_state.page = "students"
            st.experimental_rerun()
        
        if st.button("📚 Manage Classes", use_container_width=True):
            st.session_state.page = "classes"
            st.experimental_rerun()
        
        if st.button("📊 Attendance Reports", use_container_width=True):
            st.session_state.page = "attendance"
            st.experimental_rerun()
        
        if st.button("🔍 Database Explorer", use_container_width=True):
            st.session_state.page = "explorer"
            st.experimental_rerun()

def show_student_management():
    """Show student management interface"""
    from professional_db_explorer import show_student_management
    show_student_management()

def show_class_management():
    """Show class management interface"""
    from professional_db_explorer import show_class_management
    show_class_management()

def show_attendance_management():
    """Show attendance management interface"""
    from professional_db_explorer import show_attendance_management
    show_attendance_management()

def show_analytics():
    """Show analytics interface"""
    from professional_db_explorer import show_analytics_dashboard
    show_analytics_dashboard()

def show_database_explorer():
    """Show database explorer"""
    st.header("🔍 Database Explorer")
    
    tab1, tab2 = st.tabs(["Professional Explorer", "Legacy Explorer"])
    
    with tab1:
        st.info("Loading Professional Database Explorer...")
        try:
            from professional_db_explorer import main as run_professional_explorer
            run_professional_explorer()
        except Exception as e:
            st.error(f"Error loading professional explorer: {e}")
    
    with tab2:
        st.info("Loading Legacy Database Explorer...")
        try:
            from enhanced_db_explorer import show_db_explorer
            show_db_explorer()
        except Exception as e:
            st.error(f"Error loading legacy explorer: {e}")

def show_settings():
    """Show system settings"""
    st.header("⚙️ System Settings")
    
    tab1, tab2, tab3 = st.tabs(["Database Info", "System Maintenance", "Configuration"])
    
    with tab1:
        st.subheader("Database Information")
        
        try:
            conn = sqlite3.connect('attendance_system.db')
            
            # Table information
            tables = conn.execute("""
                SELECT name, type FROM sqlite_master 
                WHERE type IN ('table', 'view') 
                ORDER BY type DESC, name
            """).fetchall()
            
            st.write("**Database Objects:**")
            for name, obj_type in tables:
                if obj_type == 'table':
                    count = conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
                    st.write(f"📊 Table: `{name}` ({count} records)")
                else:
                    st.write(f"👁️ View: `{name}`")
            
            conn.close()
            
        except Exception as e:
            st.error(f"Error getting database info: {e}")
    
    with tab2:
        st.subheader("System Maintenance")
        
        if st.button("🧹 Optimize Database"):
            try:
                conn = sqlite3.connect('attendance_system.db')
                conn.execute("VACUUM")
                conn.execute("ANALYZE")
                conn.close()
                st.success("Database optimized successfully!")
            except Exception as e:
                st.error(f"Optimization error: {e}")
        
        if st.button("📊 Update Statistics"):
            try:
                conn = sqlite3.connect('attendance_system.db')
                conn.execute("ANALYZE")
                conn.close()
                st.success("Statistics updated!")
            except Exception as e:
                st.error(f"Statistics update error: {e}")
    
    with tab3:
        st.subheader("Configuration")
        st.info("Configuration options will be added here.")

def main():
    """Main application entry point"""
    initialize_professional_system()
    
    # Check if professional database is setup
    if not show_system_status():
        return
    
    # Initialize session state
    if 'page' not in st.session_state:
        st.session_state.page = 'dashboard'
    
    # Navigation
    selected_page = show_navigation()
    
    # Update page if navigation changed
    if selected_page != st.session_state.get('page'):
        st.session_state.page = selected_page
    
    # Route to appropriate page
    pages = {
        'dashboard': show_dashboard,
        'students': show_student_management,
        'classes': show_class_management,
        'attendance': show_attendance_management,
        'analytics': show_analytics,
        'explorer': show_database_explorer,
        'settings': show_settings
    }
    
    # Show selected page
    current_page = st.session_state.get('page', 'dashboard')
    if current_page in pages:
        try:
            pages[current_page]()
        except Exception as e:
            st.error(f"Error loading page: {e}")
            st.write("Please check the system logs for more details.")
    else:
        st.error(f"Unknown page: {current_page}")
        show_dashboard()

if __name__ == "__main__":
    main()
