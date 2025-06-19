"""
Professional Database Explorer for Academic Management System
============================================================
Enhanced database explorer optimized for the new professional academic database structure
"""

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import json

def get_db_connection():
    """Get database connection with foreign keys enabled"""
    conn = sqlite3.connect('attendance_system.db')
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def show_professional_dashboard():
    """Show professional academic dashboard"""
    st.title("🎓 Professional Academic Management System")
    st.markdown("---")
    
    # Key metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        conn = get_db_connection()
        students_count = conn.execute("SELECT COUNT(*) FROM student_profiles").fetchone()[0]
        st.metric("Total Students", students_count)
        conn.close()
    
    with col2:
        conn = get_db_connection()
        classes_count = conn.execute("SELECT COUNT(*) FROM classes WHERE status = 'active'").fetchone()[0]
        st.metric("Active Classes", classes_count)
        conn.close()
    
    with col3:
        conn = get_db_connection()
        subjects_count = conn.execute("SELECT COUNT(*) FROM subjects_new").fetchone()[0]
        st.metric("Subjects", subjects_count)
        conn.close()
    
    with col4:
        conn = get_db_connection()
        enrollments_count = conn.execute("SELECT COUNT(*) FROM student_classes WHERE status = 'enrolled'").fetchone()[0]
        st.metric("Active Enrollments", enrollments_count)
        conn.close()

def show_student_management():
    """Professional student management interface"""
    st.header("👥 Student Management")
    
    tab1, tab2, tab3 = st.tabs(["Student Profiles", "Class Enrollments", "Attendance Analytics"])
    
    with tab1:
        st.subheader("Student Profiles")
        conn = get_db_connection()
        students_df = pd.read_sql_query("""
            SELECT 
                sp.id,
                sp.username,
                sp.name,
                sp.student_id as student_number,
                sp.section,
                sp.email,
                sp.phone,
                COUNT(sc.class_id) as enrolled_classes,
                AVG(sc.attendance_percentage) as avg_attendance
            FROM student_profiles sp
            LEFT JOIN student_classes sc ON sp.id = sc.student_id AND sc.status = 'enrolled'
            GROUP BY sp.id
            ORDER BY sp.name
        """, conn)
        conn.close()
        
        st.dataframe(students_df, use_container_width=True)
    
    with tab2:
        st.subheader("Class Enrollments")
        conn = get_db_connection()
        enrollments_df = pd.read_sql_query("""
            SELECT 
                sp.name as student_name,
                sp.username,
                c.class_code,
                s.subject_name,
                s.subject_code,
                sc.enrollment_date,
                sc.status,
                sc.grade,
                sc.attendance_percentage,
                p.name as professor_name
            FROM student_classes sc
            JOIN student_profiles sp ON sc.student_id = sp.id
            JOIN classes c ON sc.class_id = c.class_id
            JOIN subjects_new s ON c.subject_id = s.subject_id
            JOIN professor_profiles p ON c.professor_id = p.id
            ORDER BY sp.name, s.subject_name
        """, conn)
        conn.close()
        
        # Filter options
        col1, col2 = st.columns(2)
        with col1:
            status_filter = st.selectbox("Filter by Status", 
                                       ["All"] + list(enrollments_df['status'].unique()))
        with col2:
            student_filter = st.selectbox("Filter by Student", 
                                        ["All"] + list(enrollments_df['student_name'].unique()))
        
        # Apply filters
        filtered_df = enrollments_df.copy()
        if status_filter != "All":
            filtered_df = filtered_df[filtered_df['status'] == status_filter]
        if student_filter != "All":
            filtered_df = filtered_df[filtered_df['student_name'] == student_filter]
        
        st.dataframe(filtered_df, use_container_width=True)
    
    with tab3:
        st.subheader("Attendance Analytics")
        conn = get_db_connection()
        attendance_df = pd.read_sql_query("""
            SELECT * FROM v_attendance_summary
            WHERE total_sessions > 0
            ORDER BY attendance_percentage DESC
        """, conn)
        conn.close()
        
        if not attendance_df.empty:
            # Attendance distribution chart
            fig = px.histogram(attendance_df, x='attendance_percentage', 
                             title='Attendance Percentage Distribution',
                             nbins=20)
            st.plotly_chart(fig, use_container_width=True)
            
            # Detailed attendance table
            st.dataframe(attendance_df, use_container_width=True)
        else:
            st.info("No attendance data available yet.")

def show_class_management():
    """Professional class management interface"""
    st.header("📚 Class Management")
    
    tab1, tab2, tab3 = st.tabs(["Class Rosters", "Class Schedules", "Subject Management"])
    
    with tab1:
        st.subheader("Class Rosters")
        conn = get_db_connection()
        rosters_df = pd.read_sql_query("""
            SELECT 
                c.class_code,
                c.section,
                s.subject_name,
                s.subject_code,
                p.name as professor_name,
                COUNT(sc.student_id) as enrolled_students,
                c.max_students,
                c.room,
                c.schedule_days,
                c.start_time,
                c.end_time,
                c.status
            FROM classes c
            JOIN subjects_new s ON c.subject_id = s.subject_id
            JOIN professor_profiles p ON c.professor_id = p.id
            LEFT JOIN student_classes sc ON c.class_id = sc.class_id AND sc.status = 'enrolled'
            GROUP BY c.class_id
            ORDER BY s.subject_name, c.section
        """, conn)
        conn.close()
        
        st.dataframe(rosters_df, use_container_width=True)
        
        # Class utilization chart
        if not rosters_df.empty:
            rosters_df['utilization'] = (rosters_df['enrolled_students'] / rosters_df['max_students'] * 100).round(2)
            fig = px.bar(rosters_df, x='class_code', y='utilization',
                        title='Class Utilization (%)',
                        color='utilization',
                        color_continuous_scale='RdYlGn')
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("Class Schedules")
        conn = get_db_connection()
        schedules_df = pd.read_sql_query("""
            SELECT 
                c.class_code,
                s.subject_name,
                c.schedule_days,
                c.start_time,
                c.end_time,
                c.room,
                p.name as professor_name,
                COUNT(sc.student_id) as enrolled_students
            FROM classes c
            JOIN subjects_new s ON c.subject_id = s.subject_id
            JOIN professor_profiles p ON c.professor_id = p.id
            LEFT JOIN student_classes sc ON c.class_id = sc.class_id AND sc.status = 'enrolled'
            WHERE c.status = 'active'
            GROUP BY c.class_id
            ORDER BY c.start_time
        """, conn)
        conn.close()
        
        st.dataframe(schedules_df, use_container_width=True)
    
    with tab3:
        st.subheader("Subject Management")
        conn = get_db_connection()
        subjects_df = pd.read_sql_query("""
            SELECT 
                s.subject_code,
                s.subject_name,
                s.description,
                s.credits,
                d.department_name,
                COUNT(c.class_id) as active_classes,
                COUNT(DISTINCT sc.student_id) as total_enrollments
            FROM subjects_new s
            JOIN departments d ON s.department_id = d.department_id
            LEFT JOIN classes c ON s.subject_id = c.subject_id AND c.status = 'active'
            LEFT JOIN student_classes sc ON c.class_id = sc.class_id AND sc.status = 'enrolled'
            GROUP BY s.subject_id
            ORDER BY s.subject_name
        """, conn)
        conn.close()
        
        st.dataframe(subjects_df, use_container_width=True)

def show_attendance_management():
    """Professional attendance management interface"""
    st.header("📊 Attendance Management")
    
    tab1, tab2, tab3 = st.tabs(["Session Management", "Attendance Records", "Reports"])
    
    with tab1:
        st.subheader("Attendance Sessions")
        conn = get_db_connection()
        sessions_df = pd.read_sql_query("""
            SELECT 
                ats.session_id,
                c.class_code,
                s.subject_name,
                ats.session_date,
                ats.session_time,
                ats.session_type,
                ats.topic,
                ats.is_mandatory,
                COUNT(ar.attendance_id) as recorded_attendance
            FROM attendance_sessions ats
            JOIN classes c ON ats.class_id = c.class_id
            JOIN subjects_new s ON c.subject_id = s.subject_id
            LEFT JOIN attendance_records_new ar ON ats.session_id = ar.session_id
            GROUP BY ats.session_id
            ORDER BY ats.session_date DESC, ats.session_time DESC
        """, conn)
        conn.close()
        
        st.dataframe(sessions_df, use_container_width=True)
    
    with tab2:
        st.subheader("Attendance Records")
        conn = get_db_connection()
        records_df = pd.read_sql_query("""
            SELECT 
                sp.name as student_name,
                sp.username,
                c.class_code,
                s.subject_name,
                ats.session_date,
                ats.session_time,
                ar.status,
                ar.check_in_time,
                ar.method,
                ar.notes
            FROM attendance_records_new ar
            JOIN attendance_sessions ats ON ar.session_id = ats.session_id
            JOIN classes c ON ats.class_id = c.class_id
            JOIN subjects_new s ON c.subject_id = s.subject_id
            JOIN student_profiles sp ON ar.student_id = sp.id
            ORDER BY ats.session_date DESC, ats.session_time DESC
        """, conn)
        conn.close()
        
        if not records_df.empty:
            # Status distribution
            status_counts = records_df['status'].value_counts()
            if len(status_counts) > 0:
                fig = px.pie(values=status_counts.values, names=status_counts.index,
                           title='Attendance Status Distribution')
                st.plotly_chart(fig, use_container_width=True)
            
            st.dataframe(records_df, use_container_width=True)
        else:
            st.info("No attendance records found.")
    
    with tab3:
        st.subheader("Attendance Reports")
        conn = get_db_connection()
        
        # Student attendance summary
        student_summary = pd.read_sql_query("""
            SELECT 
                sp.name as student_name,
                COUNT(ar.attendance_id) as total_sessions,
                SUM(CASE WHEN ar.status = 'present' THEN 1 ELSE 0 END) as present_count,
                ROUND(AVG(CASE WHEN ar.status = 'present' THEN 100.0 ELSE 0.0 END), 2) as attendance_rate
            FROM student_profiles sp
            LEFT JOIN attendance_records_new ar ON sp.id = ar.student_id
            GROUP BY sp.id
            HAVING total_sessions > 0
            ORDER BY attendance_rate DESC
        """, conn)
        conn.close()
        
        if not student_summary.empty:
            st.dataframe(student_summary, use_container_width=True)
            
            # Attendance rate chart
            fig = px.bar(student_summary, x='student_name', y='attendance_rate',
                        title='Student Attendance Rates',
                        color='attendance_rate',
                        color_continuous_scale='RdYlGn')
            fig.update_xaxis(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)

def show_analytics_dashboard():
    """Professional analytics dashboard"""
    st.header("📈 Analytics Dashboard")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Enrollment Trends")
        conn = get_db_connection()
        enrollment_trends = pd.read_sql_query("""
            SELECT 
                DATE(enrollment_date) as date,
                COUNT(*) as enrollments
            FROM student_classes
            WHERE enrollment_date IS NOT NULL
            GROUP BY DATE(enrollment_date)
            ORDER BY date
        """, conn)
        conn.close()
        
        if not enrollment_trends.empty:
            fig = px.line(enrollment_trends, x='date', y='enrollments',
                         title='Daily Enrollment Trends')
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Subject Popularity")
        conn = get_db_connection()
        subject_popularity = pd.read_sql_query("""
            SELECT 
                s.subject_name,
                COUNT(sc.student_id) as enrollments
            FROM subjects_new s
            LEFT JOIN classes c ON s.subject_id = c.subject_id
            LEFT JOIN student_classes sc ON c.class_id = sc.class_id AND sc.status = 'enrolled'
            GROUP BY s.subject_id
            ORDER BY enrollments DESC
            LIMIT 10
        """, conn)
        conn.close()
        
        if not subject_popularity.empty:
            fig = px.bar(subject_popularity, x='subject_name', y='enrollments',
                        title='Most Popular Subjects')
            fig.update_xaxis(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)

def main():
    """Main professional database explorer interface"""
    st.set_page_config(
        page_title="Professional Academic Database Explorer",
        page_icon="🎓",
        layout="wide"
    )
    
    st.sidebar.title("🎓 Academic System")
    
    # Navigation
    pages = {
        "Dashboard": show_professional_dashboard,
        "Student Management": show_student_management,
        "Class Management": show_class_management,
        "Attendance Management": show_attendance_management,
        "Analytics": show_analytics_dashboard
    }
    
    selected_page = st.sidebar.selectbox("Navigate to:", list(pages.keys()))
    
    # Run selected page
    pages[selected_page]()
    
    # System info in sidebar
    st.sidebar.markdown("---")
    st.sidebar.subheader("System Information")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Database stats
    cursor.execute("SELECT COUNT(*) FROM student_profiles")
    total_students = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM classes WHERE status = 'active'")
    active_classes = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM student_classes WHERE status = 'enrolled'")
    active_enrollments = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM attendance_records_new")
    total_attendance_records = cursor.fetchone()[0]
    
    conn.close()
    
    st.sidebar.metric("Students", total_students)
    st.sidebar.metric("Active Classes", active_classes)
    st.sidebar.metric("Enrollments", active_enrollments)
    st.sidebar.metric("Attendance Records", total_attendance_records)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Professional Academic Database**")
    st.sidebar.markdown("*Optimized for academic management*")

if __name__ == "__main__":
    main()
