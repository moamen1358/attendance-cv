"""
Dropdown utilities for consistent dropdown behavior across all pages
"""
import streamlit as st
import sqlite3
import pandas as pd

def fix_dropdown_css():
    """Apply CSS fixes for dropdown positioning and behavior"""
    st.markdown("""
    <style>
    /* Force dropdowns to use full width and proper positioning */
    .stSelectbox > div > div {
        width: 100% !important;
        min-width: 300px !important;
    }
    
    .stMultiSelect > div > div {
        width: 100% !important;
        min-width: 300px !important;
    }
    
    /* Fix dropdown container positioning */
    .stSelectbox [data-baseweb="select"] {
        min-width: 200px !important;
        width: 100% !important;
    }
    
    .stMultiSelect [data-baseweb="select"] {
        min-width: 200px !important;
        width: 100% !important;
    }
    
    /* Ensure proper form layout */
    .stForm {
        width: 100% !important;
    }
    
    /* Fix any sidebar interference */
    .main .block-container {
        max-width: 100% !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    
    /* Fix z-index for dropdown overlays */
    .stSelectbox [data-baseweb="popover"] {
        z-index: 999999 !important;
    }
    
    .stMultiSelect [data-baseweb="popover"] {
        z-index: 999999 !important;
    }
    
    /* Ensure responsive design */
    @media (max-width: 768px) {
        .main .block-container {
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
        }
        
        .stSelectbox > div > div,
        .stMultiSelect > div > div {
            min-width: 200px !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

def get_subjects_data():
    """Universal function to get subjects data with multiple fallbacks"""
    conn = None
    try:
        conn = sqlite3.connect('attendance_system.db')
        cursor = conn.cursor()
        
        # Method 1: Try compatibility view
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE (type='table' OR type='view') AND name='subjects'")
            if cursor.fetchone():
                query = "SELECT subject_id, subject_name FROM subjects"
                df = pd.read_sql_query(query, conn)
                if not df.empty:
                    return df
        except Exception as e:
            st.warning(f"Method 1 failed: {e}")
        
        # Method 2: Try enhanced table directly
        try:
            query = "SELECT subject_id, subject_name FROM subjects_enhanced"
            df = pd.read_sql_query(query, conn)
            if not df.empty:
                return df
        except Exception as e:
            st.warning(f"Method 2 failed: {e}")
        
        # Method 3: Check what tables actually exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%subject%'")
        subject_tables = [row[0] for row in cursor.fetchall()]
        st.warning(f"Available subject tables: {subject_tables}")
        
        return pd.DataFrame(columns=['subject_id', 'subject_name'])
        
    except Exception as e:
        st.error(f"Error getting subjects: {e}")
        return pd.DataFrame(columns=['subject_id', 'subject_name'])
    finally:
        if conn:
            conn.close()

def get_professors_data():
    """Universal function to get professors data with multiple fallbacks"""
    conn = None
    try:
        conn = sqlite3.connect('attendance_system.db')
        
        # Method 1: Try with professor_profiles join
        try:
            query = """
            SELECT ua.username, COALESCE(pp.name, ua.username) as name
            FROM user_accounts_enhanced ua
            LEFT JOIN professor_profiles pp ON ua.username = pp.username
            WHERE ua.role = 'professor'
            ORDER BY name
            """
            df = pd.read_sql_query(query, conn)
            if not df.empty:
                return df
        except Exception as e:
            st.warning(f"Professor method 1 failed: {e}")
        
        # Method 2: Simple fallback
        try:
            query = "SELECT username, username as name FROM user_accounts_enhanced WHERE role = 'professor'"
            df = pd.read_sql_query(query, conn)
            if not df.empty:
                return df
        except Exception as e:
            st.warning(f"Professor method 2 failed: {e}")
        
        # Method 3: Direct from users_enhanced
        try:
            query = "SELECT username, full_name as name FROM users_enhanced WHERE role = 'teacher'"
            df = pd.read_sql_query(query, conn)
            if not df.empty:
                return df
        except Exception as e:
            st.warning(f"Professor method 3 failed: {e}")
            
        return pd.DataFrame(columns=['username', 'name'])
        
    except Exception as e:
        st.error(f"Error getting professors: {e}")
        return pd.DataFrame(columns=['username', 'name'])
    finally:
        if conn:
            conn.close()

def create_professor_dropdown(label="Select Professor", key=None):
    """Create a standardized professor dropdown"""
    fix_dropdown_css()
    
    professors_df = get_professors_data()
    if professors_df.empty:
        st.error("No professors found")
        return None
        
    return st.selectbox(
        label,
        options=professors_df['username'].tolist(),
        format_func=lambda x: f"{professors_df[professors_df['username'] == x]['name'].values[0]} ({x})",
        key=key
    )

def create_subjects_multiselect(label="Select Subject(s)", key=None):
    """Create a standardized subjects multiselect"""
    fix_dropdown_css()
    
    subjects_df = get_subjects_data()
    if subjects_df.empty:
        st.error("No subjects found")
        return []
        
    return st.multiselect(
        label,
        options=subjects_df['subject_id'].tolist(),
        format_func=lambda x: f"{subjects_df[subjects_df['subject_id'] == x]['subject_name'].values[0]} ({x})",
        key=key
    )

def create_subjects_dropdown(label="Select Subject", key=None):
    """Create a standardized single subject dropdown"""
    fix_dropdown_css()
    
    subjects_df = get_subjects_data()
    if subjects_df.empty:
        st.error("No subjects found")
        return None
        
    return st.selectbox(
        label,
        options=subjects_df['subject_id'].tolist(),
        format_func=lambda x: f"{subjects_df[subjects_df['subject_id'] == x]['subject_name'].values[0]} ({x})",
        key=key
    )
