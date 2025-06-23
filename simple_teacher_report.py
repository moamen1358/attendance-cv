"""
Simplified report function for teacher dashboard
This version focuses on core functionality with the enhanced database schema
"""

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta

def show_simple_teacher_report():
    """Simplified teacher report that works with enhanced database schema"""
    
    st.title("Teacher Dashboard")
    
    # Get current user info
    username = st.session_state.get('username', '')
    
    if not username:
        st.error("Please log in to access the teacher dashboard.")
        return
    
    # Connect to database
    conn = sqlite3.connect('attendance_system.db')
    cursor = conn.cursor()
    
    try:
        # Get teacher information
        cursor.execute("""
            SELECT te.teacher_id, te.name, te.employee_id, te.department
            FROM teachers_enhanced te
            JOIN users_enhanced ue ON te.teacher_id = ue.linked_id
            WHERE ue.username = ? AND ue.role = 'teacher'
        """, (username,))
        
        teacher_info = cursor.fetchone()
        
        if not teacher_info:
            st.error("Teacher information not found. Please contact administrator.")
            return
        
        teacher_id, teacher_name, employee_id, department = teacher_info
        
        # Display teacher info
        st.subheader(f"Welcome, {teacher_name}")
        st.write(f"**Employee ID:** {employee_id}")
        st.write(f"**Department:** {department}")
        
        # Get assigned subjects
        cursor.execute("""
            SELECT s.subject_id, s.subject_name, s.course_code, s.credit_hours
            FROM subjects_enhanced s
            JOIN teacher_subjects_enhanced tse ON s.subject_id = tse.subject_id
            WHERE tse.teacher_id = ? AND tse.status = 'active'
            ORDER BY s.subject_name
        """, (teacher_id,))
        
        subjects = cursor.fetchall()
        
        if subjects:
            st.subheader("Your Assigned Subjects")
            
            for subject_id, subject_name, course_code, credit_hours in subjects:
                with st.expander(f"📚 {subject_name} ({course_code})", expanded=False):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Credit Hours:** {credit_hours}")
                        st.write(f"**Subject ID:** {subject_id}")
                    
                    with col2:
                        # Get attendance statistics for this subject
                        cursor.execute("""
                            SELECT 
                                COUNT(*) as total_records,
                                COUNT(CASE WHEN status = 'present' THEN 1 END) as present_count,
                                COUNT(CASE WHEN status = 'absent' THEN 1 END) as absent_count,
                                COUNT(CASE WHEN status = 'late' THEN 1 END) as late_count
                            FROM attendance_records_enhanced
                            WHERE subject_id = ? AND teacher_id = ?
                        """, (subject_id, teacher_id))
                        
                        stats = cursor.fetchone()
                        if stats and stats[0] > 0:
                            total, present, absent, late = stats
                            attendance_rate = (present / total) * 100 if total > 0 else 0
                            
                            st.metric("Total Records", total)
                            st.metric("Attendance Rate", f"{attendance_rate:.1f}%")
                            st.write(f"Present: {present}, Absent: {absent}, Late: {late}")
                        else:
                            st.info("No attendance records yet")
            
            # Show recent attendance overview
            st.subheader("Recent Attendance Overview")
            
            # Get recent attendance data
            cursor.execute("""
                SELECT 
                    ar.attendance_date,
                    s.subject_name,
                    st.name as student_name,
                    ar.status,
                    ar.attendance_time
                FROM attendance_records_enhanced ar
                JOIN subjects_enhanced s ON ar.subject_id = s.subject_id
                JOIN students_enhanced st ON ar.student_id = st.student_id
                WHERE ar.teacher_id = ?
                ORDER BY ar.attendance_date DESC, ar.attendance_time DESC
                LIMIT 20
            """, (teacher_id,))
            
            recent_records = cursor.fetchall()
            
            if recent_records:
                df = pd.DataFrame(recent_records, columns=[
                    'Date', 'Subject', 'Student', 'Status', 'Time'
                ])
                
                # Format the dataframe for better display
                df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
                df['Time'] = df['Time'].fillna('--:--')
                
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No recent attendance records found.")
                
        else:
            st.warning("No subjects assigned to you yet.")
            st.info("Please contact the administrator to assign subjects.")
    
    except Exception as e:
        st.error(f"Error loading teacher dashboard: {e}")
        st.write("**Debug Info:**")
        st.write(f"Username: {username}")
        st.write(f"Error: {str(e)}")
    
    finally:
        conn.close()

if __name__ == "__main__":
    show_simple_teacher_report()
