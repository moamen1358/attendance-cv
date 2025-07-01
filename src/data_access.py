"""
Simple and reliable data access utilities
"""
import sqlite3
import pandas as pd
import streamlit as st

def get_professors_simple():
    """Get professors with simple, reliable query"""
    try:
        conn = sqlite3.connect('attendance_system.db')
        
        # Try the enhanced query first
        query = """
        SELECT ua.username, COALESCE(pp.name, ua.full_name, ua.username) as name
        FROM user_accounts_enhanced ua
        LEFT JOIN professor_profiles pp ON ua.username = pp.username
        WHERE ua.role = 'professor'
        ORDER BY name
        """
        
        try:
            df = pd.read_sql(query, conn)
        except Exception as e:
            # Fallback to simple query
            st.info("Using fallback professor query")
            query = "SELECT username, username as name FROM user_accounts_enhanced WHERE role = 'professor'"
            df = pd.read_sql(query, conn)
        
        conn.close()
        return df
        
    except Exception as e:
        st.error(f"Error loading professors: {e}")
        return pd.DataFrame(columns=['username', 'name'])

def get_subjects_simple():
    """Get subjects with simple, reliable query"""
    try:
        conn = sqlite3.connect('attendance_system.db')
        
        # Simple subjects query
        query = "SELECT subject_id, subject_name FROM subjects ORDER BY subject_name"
        df = pd.read_sql(query, conn)
        conn.close()
        
        if df.empty:
            st.warning("No subjects found in database")
        
        return df
        
    except Exception as e:
        st.error(f"Error loading subjects: {e}")
        return pd.DataFrame(columns=['subject_id', 'subject_name'])

def get_current_assignments_simple():
    """Get current professor-subject assignments"""
    try:
        conn = sqlite3.connect('attendance_system.db')
        
        query = """
        SELECT 
            psa.professor_username,
            COALESCE(pp.name, psa.professor_username) as professor_name,
            s.subject_name,
            psa.assigned_date
        FROM professor_subject_assignments psa
        LEFT JOIN professor_profiles pp ON psa.professor_username = pp.username
        LEFT JOIN subjects s ON psa.subject_id = s.subject_id
        ORDER BY professor_name, s.subject_name
        """
        
        df = pd.read_sql(query, conn)
        conn.close()
        return df
        
    except Exception as e:
        st.error(f"Error loading assignments: {e}")
        return pd.DataFrame()

def assign_subject_to_professor(professor_username, subject_ids):
    """Assign subjects to a professor"""
    try:
        conn = sqlite3.connect('attendance_system.db')
        cursor = conn.cursor()
        
        success_count = 0
        for subject_id in subject_ids:
            try:
                cursor.execute("""
                INSERT OR IGNORE INTO professor_subject_assignments 
                (professor_username, subject_id) 
                VALUES (?, ?)
                """, (professor_username, subject_id))
                
                if cursor.rowcount > 0:
                    success_count += 1
                    
            except Exception as e:
                st.error(f"Error assigning subject {subject_id}: {e}")
        
        conn.commit()
        conn.close()
        
        return success_count
        
    except Exception as e:
        st.error(f"Error in assignment: {e}")
        return 0
