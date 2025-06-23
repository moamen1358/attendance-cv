import streamlit as st
import sqlite3
from database_utils import execute_query, execute_query_df
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from global_css_handler import apply_global_css

DATABASE_PATH = 'attendance_system.db'

def get_student_info(username):
    """Get student information from enhanced database"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get from enhanced tables using proper joins
        cursor.execute("""
            SELECT s.student_id, s.name, s.roll_number, s.department, 
                   s.year, s.section, s.email, s.phone, u.full_name
            FROM users_enhanced u
            JOIN students_enhanced s ON u.linked_id = s.student_id
            WHERE u.username = ? AND u.role = 'student'
        """, (username,))
        
        result = cursor.fetchone()
        if result:
            return {
                'id': result[0],
                'name': result[1],
                'student_id': result[2],
                'department': result[3],
                'academic_year': result[4],
                'section': result[5],
                'email': result[6],
                'phone': result[7],
                'gpa': None  # GPA not stored in current schema
            }
        
        return None
        
    except Exception as e:
        st.error(f"Error getting student info: {e}")
        return None
    finally:
        conn.close()

def get_student_subjects(student_id):
    """Get subjects enrolled by the student"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get enrolled subjects through enhanced tables
        cursor.execute("""
            SELECT DISTINCT se.subject_id, se.subject_name, se.course_code, se.credit_hours, 
                   se.description, se.semester, cs.room_number as room, cs.day_of_week, cs.start_time, cs.end_time,
                   en.status, en.grade, 
                   COALESCE(att.attendance_percentage, 0) as attendance_percentage
            FROM student_enrollments_enhanced en
            JOIN subjects_enhanced se ON en.subject_id = se.subject_id  
            LEFT JOIN class_schedules_enhanced cs ON se.subject_id = cs.subject_id
            LEFT JOIN (
                SELECT subject_id, student_id, 
                       ROUND(AVG(CASE WHEN status = 'present' THEN 100.0 ELSE 0.0 END), 1) as attendance_percentage
                FROM attendance_records_enhanced 
                WHERE student_id = ?
                GROUP BY subject_id, student_id
            ) att ON se.subject_id = att.subject_id AND en.student_id = att.student_id
            WHERE en.student_id = ? AND en.status = 'active'
            ORDER BY se.subject_name
        """, (student_id, student_id))
        
        subjects = cursor.fetchall()
        
        subject_list = []
        for subject in subjects:
            subject_list.append({
                'id': subject[0],
                'name': subject[1],
                'course_code': subject[2],
                'credit_hours': subject[3],
                'description': subject[4],
                'section': subject[5],  # semester
                'room': subject[6],
                'schedule_days': subject[7],  # day_of_week
                'start_time': subject[8],
                'end_time': subject[9],
                'status': subject[10],
                'grade': subject[11],
                'attendance_percentage': subject[12]
            })
        
        return subject_list
        
    except Exception as e:
        st.error(f"Error getting student subjects: {e}")
        return []
    finally:
        conn.close()

def get_student_attendance(student_name, limit_days=30):
    """Get student attendance records from enhanced database"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get student ID from students_enhanced table
        cursor.execute("SELECT student_id FROM students_enhanced WHERE name = ?", (student_name,))
        student_result = cursor.fetchone()
        if not student_result:
            return []
        student_id = student_result[0]
        
        # Get attendance from the last N days (using a wider window to capture more data)
        cursor.execute("""
            SELECT ar.created_at as timestamp, ar.subject_id, se.subject_name, ar.status, ar.attendance_date
            FROM attendance_records_enhanced ar
            LEFT JOIN subjects_enhanced se ON ar.subject_id = se.subject_id
            WHERE ar.student_id = ?
            AND ar.attendance_date >= date('now', '-{} days')
            ORDER BY ar.attendance_date DESC, ar.attendance_time DESC
            LIMIT ?
        """.format(180), (student_id, limit_days * 10))  # Use 180 days window, limit results
        
        attendance = cursor.fetchall()
        
        attendance_list = []
        for record in attendance:
            attendance_list.append({
                'timestamp': record[0],
                'subject_id': record[1],
                'subject_name': record[2] or 'Unknown Subject',
                'status': record[3],
                'class_date': record[4]
            })
        
        return attendance_list
        
    except Exception as e:
        st.error(f"Error getting attendance: {e}")
        return []
    finally:
        conn.close()

def show_student_dashboard():
    """Main student dashboard"""
    # Apply global CSS
    apply_global_css()
    
    st.title("🎓 Student Dashboard")
    
    # Add refresh button
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 Refresh Data", type="secondary"):
            # Clear any cached data
            if hasattr(st, 'cache_data'):
                st.cache_data.clear()
            st.rerun()
    
    # Get current user info
    username = st.session_state.get('username', 'Unknown')
    student_info = get_student_info(username)
    
    if not student_info:
        st.error("Student information not found. Please contact your administrator.")
        return
    
    # Display student info
    st.subheader("👤 Student Information")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info(f"**Name:** {student_info['name']}")
        st.info(f"**Student ID:** {student_info['student_id'] or 'N/A'}")
        
    with col2:
        st.info(f"**Department:** {student_info['department'] or 'N/A'}")
        st.info(f"**Academic Year:** {student_info['academic_year'] or 'N/A'}")
        
    with col3:
        st.info(f"**Section:** {student_info['section'] or 'N/A'}")
        st.info(f"**GPA:** {student_info['gpa'] or 'N/A'}")
    
    st.markdown("---")
    
    # Get and display subjects
    st.subheader("📚 My Subjects")
    subjects = get_student_subjects(student_info['id'])
    
    if not subjects:
        st.warning("No subjects found. You may not be enrolled in any subjects yet.")
        st.info("Please contact your academic advisor to enroll in subjects.")
    else:
        # Display subjects in a nice format
        for subject in subjects:
            with st.expander(f"📖 {subject['name']} ({subject['course_code']})", expanded=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Credit Hours:** {subject['credit_hours']}")
                    st.write(f"**Section:** {subject['section']}")
                    st.write(f"**Room:** {subject['room'] or 'TBA'}")
                    
                with col2:
                    st.write(f"**Schedule:** {subject['schedule_days'] or 'TBA'}")
                    st.write(f"**Time:** {subject['start_time']} - {subject['end_time']}" if subject['start_time'] else "TBA")
                    st.write(f"**Status:** {subject['status']}")
                
                if subject['description']:
                    st.write(f"**Description:** {subject['description']}")
                
                # Attendance percentage with highlighting for recent updates
                if subject['attendance_percentage'] is not None:
                    attendance_pct = subject['attendance_percentage']
                    color = "green" if attendance_pct >= 75 else "orange" if attendance_pct >= 60 else "red"
                    
                    # Check if there's a recent attendance record for today
                    today = datetime.now().strftime('%Y-%m-%d')
                    recent_record = any(record['class_date'] == today and record['subject_id'] == subject['id'] 
                                      for record in attendance_records)
                    
                    if recent_record:
                        st.markdown(f"**Attendance:** <span style='color: {color}; background-color: yellow; padding: 2px 6px; border-radius: 3px;'>{attendance_pct:.1f}% ✨ Updated Today!</span>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"**Attendance:** <span style='color: {color}'>{attendance_pct:.1f}%</span>", unsafe_allow_html=True)
                
                # Grade if available
                if subject['grade']:
                    st.write(f"**Current Grade:** {subject['grade']}")
    
    st.markdown("---")
    
    # Attendance summary
    st.subheader("📊 Attendance Summary")
    
    # Show last refresh time
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.info(f"📅 Last updated: {current_time}")
    
    attendance_records = get_student_attendance(student_info['name'])
    
    if not attendance_records:
        st.info("No attendance records found.")
    else:
        # Create attendance summary
        df = pd.DataFrame(attendance_records)
        
        # Count attendance by subject
        subject_counts = df.groupby('subject_name').size().reset_index(name='count')
        
        if not subject_counts.empty:
            fig = px.bar(subject_counts, x='subject_name', y='count', 
                        title='Attendance Count by Subject',
                        labels={'subject_name': 'Subject', 'count': 'Attendance Count'})
            st.plotly_chart(fig, use_container_width=True)
        
        # Recent attendance
        st.subheader("📅 Recent Attendance")
        
        # Highlight today's attendance if any
        today = datetime.now().strftime('%Y-%m-%d')
        today_records = [record for record in attendance_records if record['class_date'] == today]
        
        if today_records:
            st.success(f"🎉 Today's Attendance ({today}):")
            for record in today_records:
                status_icon = "✅" if record['status'] == 'present' else "❌"
                st.info(f"{status_icon} **{record['subject_name']}** - {record['status'].capitalize()}")
        
        recent_df = df.head(10)
        
        if not recent_df.empty:
            # Format the dataframe for display
            display_df = recent_df[['timestamp', 'subject_name', 'status', 'class_date']].copy()
            display_df['timestamp'] = pd.to_datetime(display_df['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
            display_df.columns = ['Date/Time', 'Subject', 'Status', 'Class Date']
            
            st.dataframe(display_df, use_container_width=True)
        else:
            st.info("No recent attendance records.")

def show_student_profile():
    """Show and edit student profile"""
    st.title("👤 My Profile")
    
    username = st.session_state.get('username', 'Unknown')
    student_info = get_student_info(username)
    
    if not student_info:
        st.error("Student information not found.")
        return
    
    st.subheader("Personal Information")
    
    # Create form for profile editing
    with st.form("profile_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            email = st.text_input("Email", value=student_info['email'] or "")
            phone = st.text_input("Phone", value=student_info['phone'] or "")
            
        with col2:
            # Display read-only fields
            st.text_input("Name", value=student_info['name'], disabled=True)
            st.text_input("Student ID", value=student_info['student_id'] or "", disabled=True)
            st.text_input("Department", value=student_info['department'] or "", disabled=True)
            st.text_input("Academic Year", value=student_info['academic_year'] or "", disabled=True)
        
        submitted = st.form_submit_button("Update Profile")
        
        if submitted:
            # Update profile
            try:
                conn = sqlite3.connect(DATABASE_PATH)
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE students_enhanced 
                    SET email = ?, phone = ?
                    WHERE student_id = (
                        SELECT linked_id FROM users_enhanced WHERE username = ?
                    )
                """, (email, phone, username))
                
                conn.commit()
                st.success("Profile updated successfully!")
                st.rerun()
                
            except Exception as e:
                st.error(f"Error updating profile: {e}")
            finally:
                conn.close()

def show_student_grades():
    """Show student grades and academic performance"""
    st.title("📊 Academic Performance")
    
    username = st.session_state.get('username', 'Unknown')
    student_info = get_student_info(username)
    
    if not student_info:
        st.error("Student information not found.")
        return
    
    subjects = get_student_subjects(student_info['id'])
    
    if not subjects:
        st.warning("No subjects found.")
        return
    
    # Display grades
    st.subheader("📋 Current Grades")
    
    grades_data = []
    for subject in subjects:
        grades_data.append({
            'Subject': subject['name'],
            'Course Code': subject['course_code'],
            'Credit Hours': subject['credit_hours'],
            'Grade': subject['grade'] or 'N/A',
            'Attendance %': f"{subject['attendance_percentage']:.1f}%" if subject['attendance_percentage'] is not None else 'N/A'
        })
    
    if grades_data:
        df = pd.DataFrame(grades_data)
        st.dataframe(df, use_container_width=True)
        
        # Calculate GPA if grades are available
        numeric_grades = []
        for subject in subjects:
            if subject['grade'] and subject['grade'] != 'N/A':
                try:
                    # Convert letter grades to numeric (simple example)
                    grade_map = {'A+': 4.0, 'A': 4.0, 'A-': 3.7, 'B+': 3.3, 'B': 3.0, 'B-': 2.7, 
                                'C+': 2.3, 'C': 2.0, 'C-': 1.7, 'D+': 1.3, 'D': 1.0, 'F': 0.0}
                    if subject['grade'] in grade_map:
                        numeric_grades.append(grade_map[subject['grade']])
                except:
                    pass
        
        if numeric_grades:
            gpa = sum(numeric_grades) / len(numeric_grades)
            st.metric("Current GPA", f"{gpa:.2f}")
