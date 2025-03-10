import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sqlite3
import io
from real_time_prediction import create_or_add_to_collection
from time_format_utils import normalize_time_format

# Constants
DATABASE_PATH = 'attendance_system.db'
CHROMA_STORE_PATH = "./store"

# Function to get a connection to the SQLite database
def get_db_connection():
    return sqlite3.connect(DATABASE_PATH)

# Function to get attendance data with filtering options
def get_attendance_data(start_date=None, end_date=None, student_name=None, limit=1000):
    conn = get_db_connection()
    
    query_parts = ["SELECT name, timestamp, confidence, device_id FROM attendance_log"]
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
    conn.close()
    
    # Convert timestamp to datetime for better display
    if not df.empty:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = df['timestamp'].dt.date
        df['time'] = df['timestamp'].dt.strftime('%I:%M %p')
    
    return df

# Function to get class attendance data
def get_class_attendance_data(start_date=None, end_date=None, student_name=None, subject=None):
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

# Function to get list of subjects from the database
def get_subjects():
    conn = get_db_connection()
    query = "SELECT DISTINCT subject FROM control_4 WHERE subject != '' ORDER BY subject"
    df = pd.read_sql(query, conn)
    conn.close()
    return df['subject'].tolist()

# Function to add manual attendance record for a student
def add_manual_attendance(student_name, class_date, subject, start_time, end_time, attended):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Format time values to ensure consistency
    start_time = normalize_time_format(start_time)
    end_time = normalize_time_format(end_time)
    
    # Insert or update class attendance record
    query = """
    INSERT OR REPLACE INTO class_attendance 
        (student_name, class_date, subject, start_time, end_time, attended)
    VALUES (?, ?, ?, ?, ?, ?)
    """
    
    cursor.execute(query, (student_name, class_date, subject, start_time, end_time, attended))
    
    # If attended, also add a log entry
    if attended:
        # Generate a timestamp within the class time
        try:
            date_str = class_date
            
            # Create datetime objects for start and end times
            start_dt = datetime.strptime(f"{date_str} {start_time}", "%Y-%m-%d %I:%M %p")
            end_dt = datetime.strptime(f"{date_str} {end_time}", "%Y-%m-%d %I:%M %p")
            
            # Set attendance time to 15 minutes after class start
            attendance_time = start_dt + timedelta(minutes=15)
            
            # If that's after the end time, use the middle of the class
            if attendance_time > end_dt:
                attendance_time = start_dt + (end_dt - start_dt) / 2
            
            # Format timestamp for database
            timestamp = attendance_time.strftime("%Y-%m-%d %H:%M:%S")
            
            # Add log entry
            cursor.execute("""
                INSERT INTO attendance_log (name, timestamp, confidence, device_id, day_of_week)
                VALUES (?, ?, ?, ?, ?)
            """, (
                student_name, 
                timestamp, 
                1.0,  # Perfect confidence for manual entries
                "manual_entry",
                datetime.strptime(class_date, "%Y-%m-%d").strftime('%A')
            ))
        except Exception as e:
            print(f"Error adding attendance log: {e}")
    
    conn.commit()
    conn.close()
    
    return True

# Function to get attendance summary data with enhanced performance for large student counts
def get_attendance_summary(start_date=None, end_date=None, search_term=None, sort_by="student_name", sort_dir="asc", limit=100, offset=0):
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
    WHERE 1=1 {date_condition} {search_condition}
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
    WHERE 1=1 {date_condition} {search_condition}
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

# Function to get subject attendance summary with enhanced performance
def get_subject_attendance_summary(start_date=None, end_date=None, search_term=None):
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

# New function to get monthly attendance trends
def get_monthly_attendance_trends(start_date=None, end_date=None):
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

# New function to get top and bottom performers
def get_attendance_outliers(start_date=None, end_date=None, limit=5):
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
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
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

def show_report():
    st.title("Attendance Management Dashboard")
    st.write("Comprehensive attendance reports and management tools for administrators")

    # Add tabs for different report sections
    tabs = st.tabs(["Attendance Summary", "Class Attendance", "Raw Attendance Logs", "Manual Entry"])
    
    # Get list of all students for filtering
    students = ["All Students"] + get_registered_students()
    subjects = ["All Subjects"] + get_subjects()
    
    # Date filters that apply to all tabs
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

    # Tab 1: Enhanced Attendance Summary
    with tabs[0]:
        st.header("Attendance Summary Statistics")
        
        # Create attendance trends visualization
        monthly_trends = get_monthly_attendance_trends(start_date_str, end_date_str)
        if not monthly_trends.empty:
            trend_chart = create_trend_chart(monthly_trends)
            if trend_chart:
                st.plotly_chart(trend_chart, use_container_width=True)
        
        # Get overall attendance metrics
        total_attended = monthly_trends['attended_classes'].sum() if not monthly_trends.empty else 0
        total_classes = monthly_trends['total_classes'].sum() if not monthly_trends.empty else 0
        overall_rate = total_attended / total_classes * 100 if total_classes > 0 else 0
        
        # Create metrics row in a more prominent way
        st.subheader("Overall Attendance")
        metric_cols = st.columns(4)
        with metric_cols[0]:
            st.metric("Total Students", monthly_trends['active_students'].max() if not monthly_trends.empty else 0)
        with metric_cols[1]:
            st.metric("Classes Attended", total_attended)
        with metric_cols[2]:
            st.metric("Total Classes", total_classes)
        with metric_cols[3]:
            st.metric("Overall Rate", f"{overall_rate:.1f}%")
        
        # Get top performers
        top_df, _ = get_attendance_outliers(start_date_str, end_date_str, limit=6)  # Increased limit
        
        # Display top performers as cards with updated style
        st.subheader("Top Students by Attendance")
        
        # Custom CSS for cards with improved styling
        st.markdown("""
        <style>
        .performer-card {
            padding: 1.25rem;
            border-radius: 12px;
            border: none;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s, box-shadow 0.3s;
            background: linear-gradient(135deg, #ffffff, #f8f9fa);
            margin-bottom: 1rem;
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
            height: 100%;
        }
        .performer-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
        }
        .performer-avatar {
            width: 70px;
            height: 70px;
            border-radius: 50%;
            background-color: #1976D2;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 28px;
            font-weight: bold;
            margin-bottom: 1rem;
            box-shadow: 0 4px 8px rgba(25, 118, 210, 0.3);
        }
        .perfect-attendance {
            background: linear-gradient(135deg, #4CAF50, #8BC34A);
        }
        .high-attendance {
            background: linear-gradient(135deg, #1976D2, #64B5F6);
        }
        .performer-name {
            font-weight: bold;
            font-size: 1.2rem;
            color: #333;
            margin: 0.5rem 0;
        }
        .performer-stats {
            width: 100%;
            margin-top: 0.75rem;
        }
        .performer-medal {
            font-size: 2rem;
            margin-bottom: 0.5rem;
            filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2));
        }
        .progress-outer {
            width: 100%;
            height: 10px;
            background-color: #eee;
            border-radius: 10px;
            overflow: hidden;
            margin-top: 0.5rem;
        }
        .progress-inner {
            height: 100%;
            border-radius: 10px;
        }
        .progress-perfect {
            background: linear-gradient(to right, #4CAF50, #8BC34A);
        }
        .progress-high {
            background: linear-gradient(to right, #1976D2, #64B5F6);
        }
        .attendance-badge {
            padding: 4px 8px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: bold;
            color: white;
            display: inline-block;
            margin-top: 8px;
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
            grid-gap: 20px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Create cards for top performers in a grid
        if not top_df.empty:
            # Count how many perfect 100% attendance students
            perfect_students = top_df[top_df['attendance_rate'] == 100.0]
            has_perfect = len(perfect_students) > 0
            
            # Start the grid container
            st.markdown('<div class="card-grid">', unsafe_allow_html=True)
            
            # For each of the top students (up to 6)
            for i, (_, row) in enumerate(top_df.iterrows()):
                if i < 6:  # Show up to 6 students
                    is_perfect = row['attendance_rate'] == 100.0
                    
                    # Determine medal emoji (only first 3 get medals)
                    medal = ""
                    if i < 3:
                        medals = ["🥇", "🥈", "🥉"]
                        medal = f'<div class="performer-medal">{medals[i]}</div>'
                    
                    # Set CSS classes based on attendance
                    avatar_class = "performer-avatar perfect-attendance" if is_perfect else "performer-avatar high-attendance"
                    progress_class = "progress-inner progress-perfect" if is_perfect else "progress-inner progress-high"
                    badge_class = "attendance-badge perfect-badge" if is_perfect else "attendance-badge high-badge"
                    badge_text = "PERFECT ATTENDANCE" if is_perfect else f"{row['attendance_rate']:.1f}% ATTENDANCE"
                    
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
                    st.success(f"🌟 Congratulations to {perfect_names} for having perfect attendance!")
                else:
                    st.success(f"🌟 Congratulations to {perfect_names} for having perfect attendance!")
        else:
            st.info("No attendance data available to determine top performers")
        
        # Export to Excel button
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            # Export all data
            all_students_df, _ = get_attendance_summary(
                start_date_str, end_date_str, None, 
                "attendance_rate", "desc", 
                limit=10000, offset=0
            )
            
            # Get subject data
            subjects_df = get_subject_attendance_summary(start_date_str, end_date_str)
            
            # Export to Excel
            all_students_df.columns = ['Student', 'Classes Attended', 'Total Classes', 'Attendance Rate (%)', 'First Date', 'Last Date']
            all_students_df.to_excel(writer, sheet_name='Student Summary', index=False)
            
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

    # Tab 2: Class Attendance
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
            selected_subject if selected_subject != "All Subjects" else None
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
            buffer = io.BytesIO()
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
            
            # Subject selection
            subject = st.selectbox("Subject", get_subjects())
            
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
                try:
                    # Convert date to string format
                    class_date_str = class_date.strftime('%Y-%m-%d')
                    
                    # Add the attendance record
                    success = add_manual_attendance(
                        student_name,
                        class_date_str,
                        subject,
                        start_time,
                        end_time,
                        attended_val
                    )
                    
                    if success:
                        st.success(f"Successfully recorded attendance for {student_name}: {'Present' if attended_val else 'Absent'}")
                    else:
                        st.error("Failed to record attendance")
                except Exception as e:
                    st.error(f"Error recording attendance: {e}")