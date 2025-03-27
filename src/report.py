import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sqlite3
import io
import sys

# Add utils directory to path
sys.path.append('/home/invisa/Desktop/my_grad_streamlit')

# Update imports to use utils directory
from src.database_utils import execute_query, execute_query_df
from src.time_format_utils import normalize_time_format
from src.student_visualization import create_attendance_sunburst, create_attendance_gauge
from src.student_visualization import create_subject_radial_chart, create_weekly_heatmap
from src.setup_teacher_subjects import get_teacher_subjects
from src.global_css_handler import apply_global_css, enforce_fixed_padding, ensure_consistent_padding

# Constants
DATABASE_PATH = 'attendance_system.db'
CHROMA_STORE_PATH = "./store"

# Function to get a connection to the SQLite database
def get_db_connection():
    return sqlite3.connect(DATABASE_PATH)

# Function to get attendance data with filtering options - now with schema validation
def get_attendance_data(start_date=None, end_date=None, student_name=None, limit=1000):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # First check if the attendance_log table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='attendance_log'")
        if not cursor.fetchone():
            # Table doesn't exist - try attendance_records as fallback
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='attendance_records'")
            if cursor.fetchone():
                table_name = 'attendance_records'
            else:
                # Neither table exists
                return pd.DataFrame(columns=['name', 'timestamp', 'date', 'time'])
        else:
            table_name = 'attendance_log'
            
        # Check what columns actually exist in the table
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Build a SELECT clause based on available columns
        select_cols = ['name', 'timestamp']  # These are required
        
        # Add optional columns if they exist
        if 'confidence' in columns:
            select_cols.append('confidence')
        if 'device_id' in columns:
            select_cols.append('device_id')
            
        # Build the query dynamically
        query_parts = [f"SELECT {', '.join(select_cols)} FROM {table_name}"]
        params = []
        
        # Build WHERE clause based on filters
        where_clauses = []
        
        if start_date:
            where_clauses.append("DATE(timestamp) >= ?")
            params.append(start_date)
        
        if end_date:
            where_clauses.append("DATE(timestamp) <= ?")
            params.append(end_date)
        
        if student_name and student_name != "All Students":
            where_clauses.append("name = ?")
            params.append(student_name)
        
        if where_clauses:
            query_parts.append("WHERE " + " AND ".join(where_clauses))
        
        # Add order by and limit
        query_parts.append("ORDER BY timestamp DESC")
        query_parts.append(f"LIMIT {limit}")
        
        # Combine query parts
        query = " ".join(query_parts)
        
        # Execute query
        df = pd.read_sql(query, conn, params=params)
        
        # Add missing columns with default values so downstream code doesn't break
        if 'confidence' not in df.columns:
            df['confidence'] = 1.0  # Default confidence
        if 'device_id' not in df.columns:
            df['device_id'] = 'unknown'  # Default device
        
        # Convert timestamp to datetime for better display
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['date'] = df['timestamp'].dt.date
            df['time'] = df['timestamp'].dt.strftime('%I:%M %p')
        
        return df
        
    except Exception as e:
        print(f"Error in get_attendance_data: {e}")
        return pd.DataFrame(columns=['name', 'timestamp', 'confidence', 'device_id', 'date', 'time'])
    finally:
        conn.close()

# Function to get class attendance data
def get_class_attendance_data(start_date=None, end_date=None, student_name=None, subject=None, teacher_subjects=None):
    conn = get_db_connection()
    
    query_parts = ["SELECT student_name, class_date, subject, start_time, end_time, attended FROM class_attendance"]
    params = []
    
    # Build WHERE clause based on filters
    where_clauses = []
    
    if start_date:
        where_clauses.append("class_date >= ?")
        params.append(start_date)
    
    if end_date:
        where_clauses.append("class_date <= ?")
        params.append(end_date)
    
    if student_name and student_name != "All Students":
        where_clauses.append("student_name = ?")
        params.append(student_name)
        
    if subject and subject != "All Subjects":
        where_clauses.append("subject = ?")
        params.append(subject)
    
    # Add filter for teacher's subjects
    if teacher_subjects and "All Subjects" not in teacher_subjects:
        placeholders = ", ".join(["?"] * len(teacher_subjects))
        where_clauses.append(f"subject IN ({placeholders})")
        params.extend(teacher_subjects)
    
    if where_clauses:
        query_parts.append("WHERE " + " AND ".join(where_clauses))
    
    # Add order by
    query_parts.append("ORDER BY class_date DESC, start_time ASC")
    
    # Combine query parts
    query = " ".join(query_parts)
    
    # Execute query
    df = pd.read_sql(query, conn, params=params)
    conn.close()
    
    # Format the data
    if not df.empty:
        df['class_date'] = pd.to_datetime(df['class_date']).dt.date
        df['attended_status'] = df['attended'].apply(lambda x: "✅ Yes" if x else "❌ No")
    
    return df

# Function to get list of registered students from the database
def get_registered_students():
    conn = get_db_connection()
    query = "SELECT name FROM students ORDER BY name"
    df = pd.read_sql(query, conn)
    conn.close()
    return df['name'].tolist()

# Modified function to get list of subjects filtered by teacher - now with robust table checking
def get_subjects(username=None):
    """Get a list of subjects with robust table checking"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # If username provided and not "All Teachers", get teacher-specific subjects
        if username and username != "All Teachers":
            teacher_subjects = get_teacher_subjects(username)
            if teacher_subjects:
                # Return the teacher's subjects
                return ["All Subjects"] + teacher_subjects
        
        # No teacher specified or no subjects found for teacher
        # Check which tables exist in the database and use the appropriate one
        subjects = []
        
        # First check if class_schedules exists (newer schema)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='class_schedules'")
        if cursor.fetchone():
            cursor.execute("SELECT DISTINCT subject FROM class_schedules WHERE subject IS NOT NULL AND subject != '' ORDER BY subject")
            subjects = [row[0] for row in cursor.fetchall()]
            
        # If no subjects found yet, try control_4 (older schema)
        if not subjects:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='control_4'")
            if cursor.fetchone():
                cursor.execute("SELECT DISTINCT subject FROM control_4 WHERE subject != '' ORDER BY subject")
                subjects = [row[0] for row in cursor.fetchall()]
            
        # If still no subjects, try subjects table directly
        if not subjects:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='subjects'")
            if cursor.fetchone():
                cursor.execute("SELECT subject_name FROM subjects ORDER BY subject_name")
                subjects = [row[0] for row in cursor.fetchall()]
                
        return ["All Subjects"] + subjects
            
    except Exception as e:
        print(f"Error getting subjects: {e}")
        return ["All Subjects"]  # Return at least the All Subjects option
    finally:
        conn.close()

# Modified function to add manual attendance record with improved synchronization
def add_manual_attendance(student_name, class_date, subject, start_time, end_time, attended, class_type='lec'):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Format time values to ensure consistency
        start_time = normalize_time_format(start_time)
        end_time = normalize_time_format(end_time)
        
        # Get day of week for the given date
        day_of_week = datetime.strptime(class_date, '%Y-%m-%d').strftime('%A')
        
        # Step 1: Check if the class exists in control_4 table
        cursor.execute("""
            SELECT 1 FROM control_4 
            WHERE day = ? AND subject = ? AND start_time = ? AND end_time = ?
        """, (day_of_week, subject, start_time, end_time))
        
        class_exists = cursor.fetchone()
        
        # If class doesn't exist in schedule, add it
        if not class_exists:
            cursor.execute("""
                INSERT INTO control_4 (day, subject, start_time, end_time, type)
                VALUES (?, ?, ?, ?, ?)
            """, (day_of_week, subject, start_time, end_time, class_type))
            print(f"Added class to schedule: {subject} on {day_of_week} at {start_time} ({class_type})")
        else:
            # Update class type if needed
            cursor.execute("""
                UPDATE control_4
                SET type = ?
                WHERE day = ? AND subject = ? AND start_time = ? AND end_time = ?
            """, (class_type, day_of_week, subject, start_time, end_time))
        
        # Step 2: Insert or update class attendance record
        cursor.execute("""
            INSERT OR REPLACE INTO class_attendance 
                (student_name, class_date, subject, start_time, end_time, attended)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (student_name, class_date, subject, start_time, end_time, 1 if attended else 0))
        
        # Step 3: For attended classes, add a corresponding log entry
        if attended:
            # Generate a timestamp within the class time
            try:
                # Create datetime objects for start and end times
                start_dt = datetime.strptime(f"{class_date} {start_time}", "%Y-%m-%d %I:%M %p")
                end_dt = datetime.strptime(f"{class_date} {end_time}", "%Y-%m-%d %I:%M %p")
                
                # Set attendance time to 15 minutes after class start
                attendance_time = start_dt + timedelta(minutes=15)
                
                # If that's after the end time, use the middle of the class
                if attendance_time > end_dt:
                    attendance_time = start_dt + (end_dt - start_dt) / 2
                
                # Format timestamp for database
                timestamp = attendance_time.strftime("%Y-%m-%d %H:%M:%S")
                
                # Delete any existing log entries for this student, class and date
                # This prevents duplicate entries that might confuse the system
                cursor.execute("""
                    DELETE FROM attendance_log
                    WHERE name = ? AND DATE(timestamp) = ? AND 
                          TIME(timestamp) BETWEEN TIME(?) AND TIME(?)
                """, (
                    student_name,
                    class_date,
                    f"{class_date} {start_time}",
                    f"{class_date} {end_time}"
                ))
                
                # Add new log entry
                cursor.execute("""
                    INSERT INTO attendance_log (name, timestamp, confidence, device_id, day_of_week)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    student_name, 
                    timestamp, 
                    1.0,  # Perfect confidence for manual entries
                    "manual_entry",
                    day_of_week
                ))
                
                print(f"Added attendance log for {student_name} at {timestamp}")
                
            except Exception as e:
                print(f"Error adding attendance log: {e}")
                conn.rollback()
                conn.close()
                return False
        else:
            # If marking as not attended, remove any existing log entries
            cursor.execute("""
                DELETE FROM attendance_log
                WHERE name = ? AND DATE(timestamp) = ? AND 
                      TIME(timestamp) BETWEEN TIME(?) AND TIME(?)
            """, (
                student_name,
                class_date,
                f"{class_date} {start_time}",
                f"{class_date} {end_time}"
            ))
            
            print(f"Removed attendance logs for {student_name} on {class_date} between {start_time} and {end_time}")
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"Error in add_manual_attendance: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

# Modified function to get attendance summary filtered by teacher subjects
def get_attendance_summary(start_date=None, end_date=None, search_term=None, sort_by="student_name", sort_dir="asc", limit=100, offset=0, teacher_subjects=None):
    """Get attendance summary with pagination, search and sorting options"""
    conn = get_db_connection()
    
    # Prepare search condition if provided
    search_condition = ""
    params = []
    
    if search_term:
        search_condition = "AND ca.student_name LIKE ?"
        params.append(f"%{search_term}%")
    
    # Build date filter conditions
    date_condition = ""
    if start_date:
        date_condition += "AND ca.class_date >= ?"
        params.append(start_date)
    
    if end_date:
        date_condition += "AND ca.class_date <= ?"
        params.append(end_date)
    
    # Build subject filter condition
    subject_condition = ""
    if teacher_subjects and "All Subjects" not in teacher_subjects:
        placeholders = ", ".join(["?"] * len(teacher_subjects))
        subject_condition = f"AND ca.subject IN ({placeholders})"
        params.extend(teacher_subjects)
    
    # Main query with proper sorting
    # Make sure the sort_by column is valid to prevent SQL injection
    valid_sort_columns = ["student_name", "attendance_rate", "attended_classes", "total_classes"]
    if sort_by not in valid_sort_columns:
        sort_by = "student_name"
    
    # Validate sort direction
    sort_dir = "DESC" if sort_dir.upper() == "DESC" else "ASC"
    
    # Count total number of students matching criteria (for pagination)
    count_query = f"""
    SELECT COUNT(DISTINCT ca.student_name) as total_count
    FROM class_attendance ca
    WHERE 1=1 {date_condition} {search_condition} {subject_condition}
    """
    
    count_df = pd.read_sql_query(count_query, conn, params=params)
    total_count = count_df['total_count'][0] if not count_df.empty else 0
    
    # Main query with sorting and pagination
    query = f"""
    SELECT 
        ca.student_name, 
        COUNT(CASE WHEN ca.attended = 1 THEN 1 ELSE NULL END) as attended_classes,
        COUNT(*) as total_classes,
        SUM(ca.attended) * 100.0 / COUNT(*) as attendance_rate,
        MIN(ca.class_date) as first_date,
        MAX(ca.class_date) as last_date
    FROM class_attendance ca
    WHERE 1=1 {date_condition} {search_condition} {subject_condition}
    GROUP BY ca.student_name
    ORDER BY {sort_by} {sort_dir}
    LIMIT ? OFFSET ?
    """
    
    # Add pagination parameters
    params.append(limit)
    params.append(offset)
    
    # Execute query
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    # Format the results
    if not df.empty:
        df['attendance_rate'] = df['attendance_rate'].round(1)
        df['first_date'] = pd.to_datetime(df['first_date']).dt.date
        df['last_date'] = pd.to_datetime(df['last_date']).dt.date
    
    return df, total_count

# Modified function to get subject attendance summary
def get_subject_attendance_summary(start_date=None, end_date=None, search_term=None, teacher_subjects=None):
    """Get subject attendance summary with search capability"""
    conn = get_db_connection()
    
    # Prepare parameters and conditions
    params = []
    conditions = []
    
    if start_date:
        conditions.append("ca.class_date >= ?")
        params.append(start_date)
    
    if end_date:
        conditions.append("ca.class_date <= ?")
        params.append(end_date)
    
    if search_term:
        conditions.append("ca.subject LIKE ?")
        params.append(f"%{search_term}%")
    
    # Add filter for teacher's subjects
    if teacher_subjects and "All Subjects" not in teacher_subjects:
        placeholders = ", ".join(["?"] * len(teacher_subjects))
        conditions.append(f"ca.subject IN ({placeholders})")
        params.extend(teacher_subjects)
    
    # Build WHERE clause
    where_clause = " AND ".join(conditions)
    if where_clause:
        where_clause = "WHERE " + where_clause
    
    # Query for subject statistics
    query = f"""
    SELECT 
        ca.subject, 
        COUNT(DISTINCT ca.student_name) as unique_students,
        COUNT(CASE WHEN ca.attended = 1 THEN 1 ELSE NULL END) as attended_count,
        COUNT(*) as total_count,
        SUM(ca.attended) * 100.0 / COUNT(*) as attendance_rate
    FROM class_attendance ca
    {where_clause}
    GROUP BY ca.subject
    ORDER BY attendance_rate DESC
    """
    
    # Execute query
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    # Format the results
    if not df.empty:
        df['attendance_rate'] = df['attendance_rate'].round(1)
    
    return df

# New function to get monthly attendance trends with subject filtering
def get_monthly_attendance_trends(start_date=None, end_date=None, teacher_subjects=None):
    """Get attendance trend data aggregated by month"""
    conn = get_db_connection()
    
    # Prepare conditions and parameters
    conditions = []
    params = []
    
    if start_date:
        conditions.append("ca.class_date >= ?")
        params.append(start_date)
    
    if end_date:
        conditions.append("ca.class_date <= ?")
        params.append(end_date)
    
    # Add filter for teacher's subjects
    if teacher_subjects and "All Subjects" not in teacher_subjects:
        placeholders = ", ".join(["?"] * len(teacher_subjects))
        conditions.append(f"ca.subject IN ({placeholders})")
        params.extend(teacher_subjects)
    
    # Build WHERE clause
    where_clause = " AND ".join(conditions)
    if where_clause:
        where_clause = "WHERE " + where_clause
    
    # Query for monthly trends
    query = f"""
    SELECT 
        strftime('%Y-%m', ca.class_date) as month,
        COUNT(DISTINCT ca.student_name) as active_students,
        COUNT(*) as total_classes,
        SUM(ca.attended) as attended_classes,
        SUM(ca.attended) * 100.0 / COUNT(*) as attendance_rate
    FROM class_attendance ca
    {where_clause}
    GROUP BY month
    ORDER BY month
    """
    
    # Execute query
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    # Format results
    if not df.empty:
        df['attendance_rate'] = df['attendance_rate'].round(1)
        # Add month name for display
        df['month_name'] = pd.to_datetime(df['month'] + '-01').dt.strftime('%b %Y')
    
    return df

# New function to get top and bottom performers with subject filtering
def get_attendance_outliers(start_date=None, end_date=None, limit=5, teacher_subjects=None):
    """Get top and bottom performers based on attendance rate"""
    conn = get_db_connection()
    
    # Prepare conditions and parameters
    conditions = []
    params = []
    
    if start_date:
        conditions.append("ca.class_date >= ?")
        params.append(start_date)
    
    if end_date:
        conditions.append("ca.class_date <= ?")
        params.append(end_date)
    
    # Add filter for teacher's subjects
    if teacher_subjects and "All Subjects" not in teacher_subjects:
        placeholders = ", ".join(["?"] * len(teacher_subjects))
        conditions.append(f"ca.subject IN ({placeholders})")
        params.extend(teacher_subjects)
    
    # Build WHERE clause
    where_clause = " AND ".join(conditions)
    if where_clause:
        where_clause = "WHERE " + where_clause
    
    # Query for top performers
    top_query = f"""
    SELECT 
        ca.student_name, 
        COUNT(CASE WHEN ca.attended = 1 THEN 1 ELSE NULL END) as attended_classes,
        COUNT(*) as total_classes,
        SUM(ca.attended) * 100.0 / COUNT(*) as attendance_rate
    FROM class_attendance ca
    {where_clause}
    GROUP BY ca.student_name
    HAVING COUNT(*) > 3
    ORDER BY attendance_rate DESC
    LIMIT {limit}
    """
    
    # Query for bottom performers
    bottom_query = f"""
    SELECT 
        ca.student_name, 
        COUNT(CASE WHEN ca.attended = 1 THEN 1 ELSE NULL END) as attended_classes,
        COUNT(*) as total_classes,
        SUM(ca.attended) * 100.0 / COUNT(*) as attendance_rate
    FROM class_attendance ca
    {where_clause}
    GROUP BY ca.student_name
    HAVING COUNT(*) > 3
    ORDER BY attendance_rate ASC
    LIMIT {limit}
    """
    
    # Execute queries
    top_df = pd.read_sql_query(top_query, conn, params=params)
    bottom_df = pd.read_sql_query(bottom_query, conn, params=list(params))  # Copy params list
    
    conn.close()
    
    # Format results
    for df in [top_df, bottom_df]:
        if not df.empty:
            df['attendance_rate'] = df['attendance_rate'].round(1)
    
    return top_df, bottom_df

# Fix the create_trend_chart function to use correct Plotly properties
def create_trend_chart(df):
    """Create attendance trend chart from monthly data"""
    if df.empty:
        return None
    
    fig = go.Figure()
    
    # Add attendance rate line
    fig.add_trace(go.Scatter(
        x=df['month_name'],
        y=df['attendance_rate'],
        mode='lines+markers',
        name='Attendance Rate (%)',
        line=dict(color='#1E88E5', width=3),
        marker=dict(size=8),
        yaxis='y'
    ))
    
    # Add active students bars
    fig.add_trace(go.Bar(
        x=df['month_name'],
        y=df['active_students'],
        name='Active Students',
        marker_color='rgba(0, 128, 0, 0.6)',
        yaxis='y2'
    ))
    
    # Update layout with dual y-axes - FIX: using proper plotly property names
    fig.update_layout(
        title='Monthly Attendance Trends',
        xaxis=dict(title=''),
        yaxis=dict(
            title='Attendance Rate (%)',
            side='left',
            range=[0, 100],
            # FIX: Use tickfont instead of titlefont for y-axis
            tickfont=dict(color='#1E88E5'),
            # FIX: Title font is set in the title object
            title_font=dict(color='#1E88E5')
        ),
        yaxis2=dict(
            title='Number of Students',
            side='right',
            overlaying='y',
            # FIX: Use tickfont instead of titlefont for y-axis
            tickfont=dict(color='green'),
            # FIX: Title font is set in the title object
            title_font=dict(color='green')
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=20, r=20, t=50, b=100),
        height=400
    )
    
    # Add reference line for 80% attendance
    fig.add_shape(
        type="line",
        x0=0,
        x1=1,
        xref="paper",
        y0=80,
        y1=80,
        line=dict(
            color="red",
            width=1,
            dash="dash",
        )
    )
    
    fig.add_annotation(
        x=0.98,
        y=82,
        xref="paper",
        text="80% Target",
        showarrow=False,
        font=dict(size=10, color="red")
    )
    
    return fig

# Change professor page heading colors from red to purple

def show_subject_attendance(subject_id, subject_name):
    """
    Display attendance data for a specific subject
    
    Args:
        subject_id: ID of the subject to display
        subject_name: Name of the subject to display
    """
    st.markdown(f"## {subject_name} Attendance")
    
    # Get date range for filtering
    start_date = st.session_state.get('start_date', datetime.now().date() - timedelta(days=90))
    end_date = st.session_state.get('end_date', datetime.now().date())
    
    # Format dates for query
    start_date_str = start_date.strftime('%Y-%m-%d') if isinstance(start_date, datetime.date) else start_date
    end_date_str = end_date.strftime('%Y-%m-%d') if isinstance(end_date, datetime.date) else end_date
    
    # Query attendance data for this subject
    conn = get_db_connection()
    try:
        # Get attendance summary
        query = """
        SELECT 
            ca.student_name, 
            COUNT(ca.id) as total_classes,
            SUM(ca.attended) as attended_classes,
            SUM(ca.attended) * 100.0 / COUNT(ca.id) as attendance_rate
        FROM 
            class_attendance ca
        WHERE 
            ca.subject = ? AND
            ca.class_date BETWEEN ? AND ?
        GROUP BY 
            ca.student_name
        ORDER BY 
            attendance_rate DESC
        """
        
        attendance_df = pd.read_sql_query(query, conn, params=(subject_name, start_date_str, end_date_str))
        
        if attendance_df.empty:
            st.info(f"No attendance records found for {subject_name} between {start_date_str} and {end_date_str}.")
        else:
            # Calculate overall stats
            total_students = len(attendance_df)
            avg_attendance = attendance_df['attendance_rate'].mean()
            perfect_attendance = len(attendance_df[attendance_df['attendance_rate'] >= 99.9])
            low_attendance = len(attendance_df[attendance_df['attendance_rate'] < 75])
            
            # Display metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Students", total_students)
            with col2:
                st.metric("Average Attendance", f"{avg_attendance:.1f}%")
            with col3:
                st.metric("Perfect Attendance", perfect_attendance)
            with col4:
                st.metric("Low Attendance (<75%)", low_attendance)
            
            # Show attendance distribution
            st.subheader("Attendance Distribution")
            
            # Create attendance ranges
            bins = [0, 50, 75, 90, 100]
            labels = ['< 50%', '50-75%', '75-90%', '> 90%']
            attendance_df['range'] = pd.cut(attendance_df['attendance_rate'], bins=bins, labels=labels)
            
            # Count students in each range
            range_counts = attendance_df['range'].value_counts().reindex(labels, fill_value=0)
            
            # Create bar chart
            fig = px.bar(
                x=range_counts.index, 
                y=range_counts.values,
                labels={'x': 'Attendance Range', 'y': 'Number of Students'},
                color=range_counts.values,
                color_continuous_scale=['#f44336', '#ff9800', '#4caf50', '#2196f3'],
                text=range_counts.values
            )
            fig.update_traces(textposition='outside')
            fig.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)
            
            # Show student attendance table
            st.subheader("Student Attendance Records")
            
            # Format the DataFrame for display
            display_df = attendance_df.copy()
            display_df['attendance_rate'] = display_df['attendance_rate'].round(1).astype(str) + '%'
            display_df['attendance'] = display_df['attended_classes'].astype(str) + '/' + display_df['total_classes'].astype(str)
            
            # Create a styled dataframe
            st.dataframe(
                display_df[['student_name', 'attendance', 'attendance_rate']],
                column_config={
                    'student_name': st.column_config.TextColumn('Student'),
                    'attendance': st.column_config.TextColumn('Classes Attended'),
                    'attendance_rate': st.column_config.TextColumn('Attendance Rate')
                },
                hide_index=True,
                use_container_width=True
            )
            
            # Add download button
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                attendance_df.to_excel(writer, sheet_name=f'{subject_name} Attendance', index=False)
                
            st.download_button(
                label="📊 Download Attendance Data",
                data=buffer,
                file_name=f"{subject_name}_attendance.xlsx",
                mime="application/vnd.ms-excel"
            )
            
    except Exception as e:
        st.error(f"Error retrieving attendance data: {e}")
    finally:
        conn.close()
    
    # Add close button
    if st.button("↩️ Back to Subjects", key="back_from_subject"):
        del st.session_state['selected_subject_id']
        del st.session_state['selected_subject_name']
        st.rerun()

def show_report():
    """Show attendance report for professors"""
    # Get username and ensure we have a valid value
    username = st.session_state.get('username', 'Unknown')
    
    # Guard against "Unknown" username by redirecting to login
    if username == 'Unknown':
        st.error("Your session has expired or is invalid. Please login again.")
        
        # Add a login button
        if st.button("Return to Login"):
            # Clear session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            # Clear query params
            st.query_params.clear()
            st.rerun()
            
        return
    
    # Apply consistent padding immediately
    ensure_consistent_padding()
    
    st.title("Teacher Dashboard")
    
    # NEW: Ensure assignments are synced
    from src.database_utils import sync_teacher_subject_assignments
    sync_teacher_subject_assignments()
    
    # Get teacher's subjects with improved schema detection
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    assigned_subjects = None
    
    try:
        # Check which columns actually exist in the subjects table
        cursor.execute("PRAGMA table_info(subjects)")
        available_columns = {col[1].lower(): col[1] for col in cursor.fetchall()}
        print(f"Available columns in subjects table: {available_columns}")
        
        # Get subject table schema info - only include columns that actually exist
        id_col = available_columns.get('subject_id', available_columns.get('id', 'id'))
        name_col = available_columns.get('subject_name', available_columns.get('name', 'name'))
        
        # Build SELECT part dynamically, only including columns that exist
        select_columns = [f"s.{id_col} as subject_id", f"s.{name_col} as subject_name"]
        
        # Only add optional columns if they exist
        if 'course_code' in available_columns:
            select_columns.append("s.course_code")
        else:
            select_columns.append("'N/A' as course_code")  # Default value if column missing
            
        if 'credit_hours' in available_columns:
            select_columns.append("s.credit_hours")
        else:
            select_columns.append("3 as credit_hours")  # Default value if column missing
            
        if 'description' in available_columns:
            select_columns.append("s.description")
        else:
            select_columns.append("'' as description")  # Default value if column missing
        
        # Add schedule and room placeholders
        select_columns.append("NULL as schedule")
        select_columns.append("NULL as room")
        
        # First try professor_subject_assignments table with dynamic column selection
        query = f"""
        SELECT {', '.join(select_columns)}
        FROM subjects s
        JOIN professor_subject_assignments psa ON s.{id_col} = psa.subject_id
        WHERE psa.professor_username = ?
        ORDER BY s.{name_col}
        """
        
        print(f"Executing query: {query}")
        assigned_subjects = pd.read_sql_query(query, conn, params=(username,))
        
        # If no results, try teacher_subjects table with the same dynamic columns
        if assigned_subjects.empty:
            query = f"""
            SELECT {', '.join(select_columns)}
            FROM subjects s
            JOIN teacher_subjects ts ON s.{id_col} = ts.subject_id
            WHERE ts.teacher_name = ?
            ORDER BY s.{name_col}
            """
            print(f"Executing fallback query: {query}")
            assigned_subjects = pd.read_sql_query(query, conn, params=(username,))
    except Exception as e:
        st.error(f"Error querying subjects: {e}")
    finally:
        conn.close()
    
    # Auto-assign a subject if none found
    if assigned_subjects is None or assigned_subjects.empty:
        st.warning("No subjects assigned to you. Please contact an administrator.")
        
        # Add auto-assign button
        if st.button("🔄 Assign Default Subject", key="auto_assign"):
            try:
                conn = sqlite3.connect(DATABASE_PATH)
                cursor = conn.cursor()
                
                # First check if subjects table exists and has data
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='subjects'")
                if cursor.fetchone():
                    # Get first available subject
                    cursor.execute("SELECT * FROM subjects LIMIT 1")
                    subject = cursor.fetchone()
                    
                    if subject:
                        # Get the column index for ID
                        cursor.execute("PRAGMA table_info(subjects)")
                        columns = {col[1].lower(): idx for idx, col in enumerate(cursor.fetchall())}
                        id_idx = columns.get('subject_id', columns.get('id', 0))
                        subject_id = subject[id_idx]
                        
                        # Create assignment tables if they don't exist
                        cursor.execute("""
                        CREATE TABLE IF NOT EXISTS professor_subject_assignments (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            professor_username TEXT NOT NULL,
                            subject_id INTEGER NOT NULL,
                            assigned_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            UNIQUE(professor_username, subject_id)
                        )
                        """)
                        
                        cursor.execute("""
                        CREATE TABLE IF NOT EXISTS teacher_subjects (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            subject_id INTEGER,
                            teacher_name TEXT,
                            UNIQUE(subject_id, teacher_name)
                        )
                        """)
                        
                        # Assign this subject to the current professor
                        cursor.execute("""
                        INSERT OR IGNORE INTO professor_subject_assignments 
                        (professor_username, subject_id) VALUES (?, ?)
                        """, (username, subject_id))
                        
                        cursor.execute("""
                        INSERT OR IGNORE INTO teacher_subjects
                        (teacher_name, subject_id) VALUES (?, ?)
                        """, (username, subject_id))
                        
                        conn.commit()
                        st.success("Default subject assigned successfully! Refreshing...")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("No subjects found in database. Please create subjects first.")
                else:
                    st.error("Subjects table does not exist. Database may need repair.")
            except Exception as e:
                st.error(f"Error auto-assigning subject: {e}")
            finally:
                if 'conn' in locals():
                    conn.close()
        
        # Also show repair tool link
        st.markdown("If issues persist, use the database repair tool: ")
        if st.button("🔧 Repair Database Schema"):
            from src.schema_repair import show_schema_repair_tool
            show_schema_repair_tool()
        
        return  # Exit function early
    
    # Rest of the function continues with assigned subjects displayed...
    
    # Display assigned subjects in a nice format
    st.subheader("Your Assigned Subjects")
    
    # Create a better looking display for subjects
    for i, subject in assigned_subjects.iterrows():
        with st.container():
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"""
                <div style="padding: 15px; border-radius: 5px; margin-bottom: 10px; 
                          background-color: #f0f2f6; border-left: 5px solid #1E88E5;">
                    <h3 style="margin-top: 0; color: #1E88E5;">{subject['subject_name']}</h3>
                    <p><strong>Course Code:</strong> {subject['course_code']}</p>
                    <p><strong>Credit Hours:</strong> {subject['credit_hours']}</p>
                    <p><strong>Schedule:</strong> {subject['schedule'] if not pd.isna(subject['schedule']) else "No schedule set"}</p>
                    <p><strong>Room:</strong> {subject['room'] if not pd.isna(subject['room']) else "No room assigned"}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                # Add a button to view attendance for this subject
                if st.button("View Attendance", key=f"view_{subject['subject_id']}"):
                    st.session_state['selected_subject_id'] = subject['subject_id']
                    st.session_state['selected_subject_name'] = subject['subject_name']
    
    # If a subject is selected, show its attendance
    if 'selected_subject_id' in st.session_state:
        show_subject_attendance(st.session_state['selected_subject_id'], st.session_state['selected_subject_name'])

    # Apply global CSS to ensure consistency
    apply_global_css()
    
    # Add extra padding enforcement for professor view
    enforce_fixed_padding()
    
    # Force override any page-specific padding that might conflict
    # PLUS: Add standardized heading styles with TEAL color scheme
    # AND: Match username color to heading color scheme
    st.markdown("""
    <style>
    /* FORCED PADDING FOR PROFESSOR PAGE - Maximum specificity */
    body .main .block-container,
    .main .block-container,
    div.block-container,
    [data-testid="stAppViewBlockContainer"] div.block-container,
    #root > div:nth-child(1) > div > div > div > div > div > section > div > div > div > div > div.block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        padding-left: 80px !important;
        padding-right: 80px !important;
        max-width: unset !important;
    }
    
    /* STANDARDIZE ALL HEADINGS WITH TEAL COLOR SCHEME */
    /* Override Streamlit's default heading styles */
    h1, h2, h3, h4, .main h1, .main h2, .main h3, .main h4,
    [data-testid="stHeader"] {
        color: #008080 !important; /* Teal color for professor view */
        font-weight: bold !important;
    }
    
    /* Apply specific sizes to match dashboard title */
    h1, .main h1 {
        font-size: 1.8rem !important;
    }
    
    h2, .main h2, [data-testid="stHeader"] {
        font-size: 1.5rem !important;
    }
    
    h3, .main h3 {
        font-size: 1.3rem !important;
    }
    
    h4, .main h4 {
        font-size: 1.1rem !important;
    }
    
    /* Apply styling to Streamlit's native header elements */
    .css-10trblm, .css-16idsys p {
        color: #008080 !important; /* Teal color for professor view */
        font-weight: bold !important;
    }
    
    /* Style subheader specifically */
    .css-10trblm.e16nr0p33 {
        font-size: 1.3rem !important;
        color: #008080 !important; /* Teal color for professor view */
        font-weight: bold !important;
        margin-top: 1rem !important;
    }
    
    /* Consistent spacing between sections */
    .main .block-container > div > div[data-testid="stVerticalBlock"] > div[data-stale="false"] {
        margin-top: 1rem !important;
    }
    
    /* Style for the title specifically */
    .st-emotion-cache-10trblm h1 {
        color: #008080 !important; /* Teal color for professor view */
        font-weight: bold !important;
        font-size: 1.8rem !important;
    }
    
    /* MAKE USERNAME COLOR MATCH THE HEADING COLOR */
    .username-text, .username-container .username-text {
        color: #008080 !important; /* Teal color for professor view */
        font-weight: bold !important;
        font-size: 1.1rem !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # REMOVED: st.title("Attendance Management Dashboard")
    
    # Get the current user's username and role
    username = st.session_state.get('username', '')
    user_role = st.session_state.get('user_role', '')
    
    # Get teacher's subjects
    teacher_subjects = ["All Subjects"]
    if user_role == 'admin' or user_role == 'professor':
        subjects_list = get_teacher_subjects(username)
        # Fix: Check if the list is empty, not using DataFrame .empty property
        if not subjects_list:
            teacher_subjects = ["All Subjects"]
        else:
            teacher_subjects = ["All Subjects"] + subjects_list
    
    # REMOVED: st.write(f"Viewing attendance data for: **<span class='username-text'>{username}</span>**", unsafe_allow_html=True)
    # REMOVED: st.write(f"Subjects: {', '.join([s for s in teacher_subjects if s != 'All Subjects'])}")
    
    # Date filters - moved out of sidebar for professor view
    if user_role == 'professor':
        # Show date filters directly in the main content area for professors
        st.header("Filter Options")
        filter_col1, filter_col2 = st.columns(2)
        with filter_col1:
            start_date = st.date_input(
                "Start Date",
                value=datetime.now().date() - timedelta(days=90),
                max_value=datetime.now().date()
            )
        with filter_col2:
            end_date = st.date_input(
                "End Date",
                value=datetime.now().date(),
                max_value=datetime.now().date()
            )
        
        # Format dates for database queries
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        # REMOVED: Refresh button
        # if st.button("🔄 Refresh Data", use_container_width=True):
        #    st.rerun()
    else:
        # Keep sidebar for admins
        with st.sidebar:
            st.header("Filter Options")
            
            # Date range selector
            st.subheader("Date Range")
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input(
                    "Start Date",
                    value=datetime.now().date() - timedelta(days=90),
                    max_value=datetime.now().date()
                )
            with col2:
                end_date = st.date_input(
                    "End Date",
                    value=datetime.now().date(),
                    max_value=datetime.now().date()
                )
            
            # Format dates for database queries
            start_date_str = start_date.strftime('%Y-%m-%d')
            end_date_str = end_date.strftime('%Y-%m-%d')
            
            # Add refresh button
            if st.button("🔄 Refresh Data", use_container_width=True):
                st.rerun()
    
    # Add tabs for different report sections
    tabs = st.tabs(["Attendance Summary", "Class Attendance", "Raw Attendance Logs", "Manual Entry"])
    
    # Get list of all students for filtering
    students = ["All Students"] + get_registered_students()
    subjects = teacher_subjects  # Now using teacher-specific subjects
    
    # Tab 1: Enhanced Attendance Summary with beautiful visualizations
    with tabs[0]:
        st.header("Attendance Summary Statistics")
        
        # Get overall attendance metrics - filtered by teacher subjects
        monthly_trends = get_monthly_attendance_trends(start_date_str, end_date_str, teacher_subjects=teacher_subjects)
        total_attended = monthly_trends['attended_classes'].sum() if not monthly_trends.empty else 0
        total_classes = monthly_trends['total_classes'].sum() if not monthly_trends.empty else 0
        overall_rate = total_attended / total_classes * 100 if total_classes > 0 else 0
        
        # Create a row with two columns for overall metrics and gauge chart
        col1, col2 = st.columns([3, 2])
        
        # Column 1: Overall metrics in a more visual format
        with col1:
            st.subheader("Overall Attendance")
            
            # Create a nice metric row
            metric_cols = st.columns(3)
            with metric_cols[0]:
                st.metric("Total Students", monthly_trends['active_students'].max() if not monthly_trends.empty else 0)
            with metric_cols[1]:
                st.metric("Classes Attended", f"{total_attended}/{total_classes}")
            with metric_cols[2]:
                st.metric("Attendance Rate", f"{overall_rate:.1f}%")
            
            # Add a progress bar showing overall attendance with transparent background
            st.markdown(f"""
            <div style="margin-top: 20px;">
                <p style="font-weight: bold; margin-bottom: 5px;">Overall Progress</p>
                <div style="display: flex; align-items: center; gap: 10px;">
                    <div style="flex-grow: 1; height: 20px; background-color: rgba(238, 238, 238, 0.5); border-radius: 10px; overflow: hidden;">
                        <div style="width: {overall_rate}%; height: 100%; background: linear-gradient(to right, #4CAF50, #8BC34A);"></div>
                    </div>
                    <div style="width: 60px; text-align: right;">
                        <span style="font-weight: bold;">{overall_rate:.1f}%</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Column 2: Create and display the attendance gauge chart
        with col2:
            if total_classes > 0:
                # Create the gauge chart - THIS WAS MISSING
                gauge_chart = create_attendance_gauge(overall_rate)
                st.plotly_chart(gauge_chart, use_container_width=True)
        
        # Create a divider
        st.markdown("<hr style='margin: 25px 0; opacity: 0.3;'>", unsafe_allow_html=True)
        
        # Get top performers - filtered by teacher subjects
        top_df, _ = get_attendance_outliers(start_date_str, end_date_str, limit=3, teacher_subjects=teacher_subjects)
        
        # Display top performers section with reduced height
        st.subheader("Top Students by Attendance")
        
        # Custom CSS for cards with improved styling and reduced size
        st.markdown("""
        <style>
        .performer-card {
            padding: 0.9rem;  /* Reduced padding */
            border-radius: 8px;  /* Smaller radius */
            border: none;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);  /* Lighter shadow */
            transition: transform 0.3s, box-shadow 0.3s;
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.8), rgba(248, 249, 250, 0.8));  /* More transparent */
            margin-bottom: 0.75rem;  /* Reduced margin */
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
            height: 100%;
        }
        .performer-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
        }
        .performer-avatar {
            width: 55px;  /* Smaller avatar */
            height: 55px;  /* Smaller avatar */
            border-radius: 50%;
            background-color: #1976D2;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 22px;  /* Smaller font */
            font-weight: bold;
            margin-bottom: 0.75rem;
        }
        .performer-medal {
            font-size: 1.6rem;  /* Smaller medals */
            margin-bottom: 0.3rem;  /* Reduced margin */
            filter: drop-shadow(0 1px 2px rgba(0,0,0,0.2));  /* Lighter shadow */
        }
        .progress-outer {
            width: 100%;
            height: 8px;  /* Thinner progress bar */
            background-color: rgba(238, 238, 238, 0.5);  /* More transparent */
            border-radius: 8px;  /* Smaller radius */
            overflow: hidden;
            margin-top: 0.4rem;  /* Reduced margin */
        }
        .progress-inner {
            height: 100%;
            border-radius: 8px;  /* Smaller radius */
        }
        .progress-perfect {
            background: linear-gradient(to right, #4CAF50, #8BC34A);
        }
        .progress-high {
            background: linear-gradient(to right, #1976D2, #64B5F6);
        }
        .attendance-badge {
            padding: 3px 6px;  /* Smaller padding */
            border-radius: 16px;  /* Smaller radius */
            font-size: 0.7rem;  /* Smaller font */
            font-weight: bold;
            color: white;
            display: inline-block;
            margin-top: 5px;  /* Reduced margin */
        }
        .perfect-badge {
            background-color: #4CAF50;
        }
        .high-badge {
            background-color: #1976D2;
        }
        .card-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            grid-gap: 15px;  /* Reduced gap */
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Display the top performers cards - keeping the existing implementation but with updated CSS
        if not top_df.empty:
            # Count how many perfect 100% attendance students
            perfect_students = top_df[top_df['attendance_rate'] == 100.0]
            has_perfect = len(perfect_students) > 0
            
            # Start the grid container
            st.markdown('<div class="card-grid">', unsafe_allow_html=True)
            
            # For each of the top students (limited to 3)
            for i, (_, row) in enumerate(top_df.iterrows()):
                if i < 3:  # Show only up to 3 students
                    # ... existing card creation code ...
                    is_perfect = row['attendance_rate'] == 100.0
                    
                    # Determine medal emoji (all 3 get medals now)
                    medals = ["🥇", "🥈", "🥉"]
                    medal = f'<div class="performer-medal">{medals[i]}</div>'
                    
                    # Set CSS classes based on attendance
                    avatar_class = "performer-avatar perfect-attendance" if is_perfect else "performer-avatar high-attendance"
                    progress_class = "progress-inner progress-perfect" if is_perfect else "progress-inner progress-high"
                    badge_class = "attendance-badge perfect-badge" if is_perfect else "attendance-badge high-badge"
                    badge_text = "PERFECT" if is_perfect else f"{row['attendance_rate']:.1f}%"
                    
                    # Create card with appropriate styling
                    st.markdown(f"""
                    <div class="performer-card">
                        {medal}
                        <div class="{avatar_class}">{row['student_name'][0].upper()}</div>
                        <div class="performer-name">{row['student_name']}</div>
                        <div class="performer-stats">
                            <div>Classes: <strong>{row['attended_classes']}/{row['total_classes']}</strong></div>
                            <div class="progress-outer">
                                <div class="{progress_class}" style="width: {row['attendance_rate']}%;"></div>
                            </div>
                            <div class="{badge_class}">{badge_text}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Close the grid container
            st.markdown('</div>', unsafe_allow_html=True)
            
            # If there are perfect attendance students, show recognition message
            if has_perfect:
                perfect_names = ", ".join(perfect_students['student_name'].tolist())
                if len(perfect_students) > 1:
                    st.success(f"🌟 {len(perfect_students)} students have perfect attendance: {perfect_names}")
                else:
                    st.success(f"🌟 {perfect_names} has perfect attendance!")
        else:
            st.info("No attendance data available to determine top performers")
        
        # Create a divider with reduced margin
        st.markdown("<hr style='margin: 20px 0; opacity: 0.3;'>", unsafe_allow_html=True)
        
        # Add student selector for individual analysis
        st.subheader("Individual Student Analysis")
        selected_student = st.selectbox(
            "Select a student to view detailed attendance", 
            students, 
            key="student_selector"
        )
        
        # Store the selected student in session state for the visualizations to use
        st.session_state.selected_student = selected_student
        
        if selected_student != "All Students":
            # Create weekly attendance heatmap
            heatmap_chart = create_weekly_heatmap(selected_student, weeks=4)
            st.plotly_chart(heatmap_chart, use_container_width=True)
        
        # Export to Excel button
        st.subheader("Download Reports")
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            # Export all data
            all_students_df, _ = get_attendance_summary(
                start_date_str, end_date_str, None, 
                "attendance_rate", "desc", 
                limit=10000, offset=0,
                teacher_subjects=teacher_subjects
            )
            all_students_df.columns = ['Student', 'Classes Attended', 'Total Classes', 'Attendance Rate (%)', 'First Date', 'Last Date']
            all_students_df.to_excel(writer, sheet_name='Student Summary', index=False)
            
            # Get subject data
            subjects_df = get_subject_attendance_summary(start_date_str, end_date_str, teacher_subjects=teacher_subjects)
            if not subjects_df.empty:
                subject_table = subjects_df[['subject', 'unique_students', 'attended_count', 'total_count', 'attendance_rate']]
                subject_table.columns = ['Subject', 'Students', 'Classes Attended', 'Total Classes', 'Attendance Rate (%)']
                subject_table.to_excel(writer, sheet_name='Subject Summary', index=False)
            
            if not monthly_trends.empty:
                monthly_trends.to_excel(writer, sheet_name='Monthly Trends', index=False)
        
        st.download_button(
            label="📊 Download Complete Report",
            data=buffer,
            file_name=f'attendance_summary_{start_date_str}_to_{end_date_str}.xlsx',
            mime='application/vnd.ms-excel'
        )

    # Tab 2: Class Attendance - Update to filter by teacher subjects
    with tabs[1]:
        st.header("Class Attendance Records")
        
        # Add student and subject filters specific to this tab
        col1, col2 = st.columns(2)
        with col1:
            selected_student = st.selectbox("Filter by Student", students, key="class_student")
        with col2:
            selected_subject = st.selectbox("Filter by Subject", subjects, key="class_subject")
        
        # Get class attendance data
        class_df = get_class_attendance_data(
            start_date_str, 
            end_date_str, 
            selected_student if selected_student != "All Students" else None,
            selected_subject if selected_subject != "All Subjects" else None,
            teacher_subjects if selected_subject == "All Subjects" else None
        )
        
        if not class_df.empty:
            # Calculate attendance rate
            attendance_rate = class_df['attended'].mean() * 100
            
            # Display attendance rate
            st.metric("Class Attendance Rate", f"{attendance_rate:.1f}%")
            
            # Show the data in a table
            table_df = class_df[['student_name', 'class_date', 'subject', 'start_time', 'end_time', 'attended_status']]
            table_df.columns = ['Student', 'Date', 'Subject', 'Start Time', 'End Time', 'Attended']
            
            # Apply style to highlight attended/absent
            st.dataframe(
                table_df,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "Attended": st.column_config.TextColumn(
                        "Attended",
                        help="Whether the student attended the class",
                        width="medium"
                    )
                }
            )
            
            # Export to Excel button
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                table_df.to_excel(writer, sheet_name='Class Attendance', index=False)
            st.download_button(
                label="📊 Download Class Attendance",
                data=buffer,
                file_name=f'class_attendance_{start_date_str}_to_{end_date_str}.xlsx',
                mime='application/vnd.ms-excel'
            )
        else:
            st.info("No class attendance data found for the selected filters.")

    # Tab 3: Raw Attendance Logs
    with tabs[2]:
        st.header("Raw Attendance Logs")
        
        # Add student filter specific to this tab
        selected_student = st.selectbox("Filter by Student", students, key="raw_student")
        
        # Get attendance data with filters
        df = get_attendance_data(
            start_date_str, 
            end_date_str, 
            selected_student if selected_student != "All Students" else None,
            1000  # Limit to 1000 records for performance
        )
        
        if not df.empty:
            # Format the data for display
            display_df = df[['name', 'date', 'time', 'confidence', 'device_id']]
            display_df.columns = ['Student', 'Date', 'Time', 'Confidence', 'Device']
            
            # Show the data in a table
            st.dataframe(display_df, hide_index=True, use_container_width=True)
            
            # Export to Excel button
            buffer = io.Bytes.IO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                display_df.to_excel(writer, sheet_name='Attendance Logs', index=False)
            st.download_button(
                label="📊 Download Raw Logs",
                data=buffer,
                file_name=f'attendance_logs_{start_date_str}_to_{end_date_str}.xlsx',
                mime='application/vnd.ms-excel'
            )
            
            # Show record count and warning if limited
            record_count = len(df)
            st.write(f"Showing {record_count} records")
            if record_count >= 1000:
                st.warning("Results limited to 1000 records. Use date filters to narrow down results.")
        else:
            st.info("No attendance logs found for the selected filters.")

    # Tab 4: Manual Entry
    with tabs[3]:
        st.header("Manual Attendance Entry")
        st.write("Use this form to manually record attendance for a student")
        
        # Create the form
        with st.form("manual_attendance_form"):
            # Student selection
            student_name = st.selectbox("Student", get_registered_students())
            
            # Date selection (defaulting to today)
            class_date = st.date_input("Class Date", value=datetime.now().date())
            
            # Subject and class type selection
            col1, col2 = st.columns([3, 1])
            with col1:
                subject = st.selectbox("Subject", get_subjects())
            with col2:
                class_type = st.selectbox("Type", ["lec", "sec"], format_func=lambda x: "Lecture" if x == "lec" else "Section")
            
            # Time selection
            col1, col2 = st.columns(2)
            with col1:
                start_hour = st.selectbox("Start Hour", list(range(1, 13)), index=8)
                start_minute = st.selectbox("Start Minute", [0, 15, 30, 45])
                start_period = st.selectbox("AM/PM", ["AM", "PM"])
                start_time = f"{start_hour}:{start_minute:02d} {start_period}"
            with col2:
                end_hour = st.selectbox("End Hour", list(range(1, 13)), index=9)
                end_minute = st.selectbox("End Minute", [0, 15, 30, 45])
                end_period = st.selectbox("AM/PM", ["AM", "PM"], key="end_period")
                end_time = f"{end_hour}:{end_minute:02d} {end_period}"
            
            # Attendance status
            attended = st.radio("Attendance Status", ["Present", "Absent"], horizontal=True)
            attended_val = attended == "Present"
            
            # Submit button
            submitted = st.form_submit_button("Record Attendance")
            
            if submitted:
                # Convert date to string format
                class_date_str = class_date.strftime('%Y-%m-%d')
                
                try:
                    # Add the attendance record
                    success = add_manual_attendance(
                        student_name,
                        class_date_str,
                        subject,
                        start_time,
                        end_time,
                        attended_val,
                        class_type
                    )
                    
                    if success:
                        st.success(f"Successfully recorded attendance for {student_name}: {'Present' if attended_val else 'Absent'} " +
                                 f"({class_type})")
                    else:
                        st.error("Failed to record attendance")
                except Exception as e:
                    st.error(f"Error recording attendance: {e}")
