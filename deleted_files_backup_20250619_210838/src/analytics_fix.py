import streamlit as st
from database_utils import execute_query_df

def get_subject_attendance_analytics():
    """
    Get subject attendance analytics with automatic table name correction
    """
    try:
        # The original query that was failing
        query = """
        SELECT s.subject_name, COUNT(DISTINCT a.id) as attendance_count 
        FROM subjects s 
        JOIN class_schedules cs ON s.subject_id = cs.subject_id 
        JOIN class_attendance a ON cs.subject = a.subject 
        GROUP BY s.subject_name
        """
        
        # This will automatically fix the table name and execute the query
        df = execute_query_df(query)
        return df
    
    except Exception as e:
        st.error(f"Error generating analytics: {str(e)}")
        
        # Create a fallback query using simpler approach
        fallback_query = """
        SELECT cs.subject as subject_name, COUNT(*) as attendance_count 
        FROM class_schedules cs
        JOIN class_attendance ca ON cs.subject = ca.subject
        WHERE ca.attended = 1
        GROUP BY cs.subject
        """
        
        try:
            # Try the fallback query
            df = execute_query_df(fallback_query)
            st.success("Used fallback query for analytics")
            return df
        except Exception as e2:
            st.error(f"Fallback query also failed: {str(e2)}")
            
            # Create simple empty dataframe with expected structure
            import pandas as pd
            return pd.DataFrame(columns=['subject_name', 'attendance_count'])
