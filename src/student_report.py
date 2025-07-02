import streamlit as st
import pandas as pd
import sqlite3
from database_utils import execute_query, execute_query_df
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import time
import random
import math
from streamlit.components.v1 import html
try:
    from time_format_utils import convert_to_ampm_format, normalize_time_format, time_between
except ImportError:
    from .time_format_utils import convert_to_ampm_format, normalize_time_format, time_between
from global_css_handler import apply_global_css  # Only import what we need

# Import centralized database initialization
try:
    from db_init import initialize_database, check_database_integrity
except ImportError:
    from .db_init import initialize_database, check_database_integrity

# Constants
DATABASE_PATH = 'attendance_system.db'

# Initialize database tables on import
initialize_database()

# Remove the initial CSS block that's being duplicated
# CSS will now be applied from global_css_handler.py

def get_db_connection():
    """Get a connection to the SQLite database"""
    return sqlite3.connect(DATABASE_PATH)

def get_student_attendance(student_name, date=None, detailed=False):
    """
    Get a student's attendance records for a specific date or all dates
    
    Args:
        student_name (str): Name of the student
        date (str, optional): Date in format 'YYYY-MM-DD' or None for all dates
        detailed (bool): Whether to include all columns or just basic info
    
    Returns:
        pandas.DataFrame: DataFrame containing attendance records
    """
    # Security check: Only allow the current user to view their own attendance
    if student_name != st.session_state.get('username') and st.session_state.get('user_role') not in ['admin', 'professor']:
        st.error("You can only view your own attendance records")
        return pd.DataFrame()  # Return empty dataframe
    
    conn = get_db_connection()
    
    if date:
        # Format for SQLite date filtering
        date_start = f"{date} 00:00:00"
        date_end = f"{date} 23:59:59"
        
        query = """
        SELECT ar.*, sp.name as student_name
        FROM attendance_records_enhanced ar
        JOIN student_profiles_enhanced sp ON ar.student_id = sp.student_id
        WHERE sp.name = ? AND ar.timestamp BETWEEN ? AND ?
        ORDER BY ar.timestamp DESC  # Explicitly sort by newest first
        """
        df = pd.read_sql(query, conn, params=(student_name, date_start, date_end))
    else:
        query = """
        SELECT ar.*, sp.name as student_name
        FROM attendance_records_enhanced ar
        JOIN student_profiles_enhanced sp ON ar.student_id = sp.student_id
        WHERE sp.name = ?
        ORDER BY ar.timestamp DESC  # Explicitly sort by newest first
        """
        df = pd.read_sql(query, conn, params=(student_name,))
    
    conn.close()
    
    if not df.empty:
        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Create a clean time column
        df['time'] = df['timestamp'].dt.strftime('%H:%M:%S')
        
        # Create a date column
        df['date'] = df['timestamp'].dt.strftime('%Y-%m-%d')
    
    return df

def get_schedule_for_day(day_name, student_name=None):
    """
    Get the subject schedule for a specific day, optionally filtered by student enrollment
    
    Args:
        day_name (str): Name of the day (e.g., 'Sunday', 'Monday')
        student_name (str, optional): Filter schedule by student's enrolled subjects
    
    Returns:
        pandas.DataFrame: DataFrame containing schedule for the day
    """
    conn = get_db_connection()
    
    if student_name:
        # Get schedule only for subjects the student is enrolled in, using their section
        query = """
        SELECT 
            s.subject_name as subject, 
            cs.class_type as type, 
            cs.start_time, 
            cs.end_time,
            cs.room_number as room,
            t.name as professor_name
        FROM class_schedules_enhanced cs
        JOIN subjects_enhanced s ON cs.subject_id = s.subject_id
        JOIN teachers_enhanced t ON cs.teacher_id = t.teacher_id
        JOIN students_enhanced st ON cs.section = st.section
        WHERE cs.day_of_week = ? 
          AND st.name = ?
          AND cs.status = 'active'
          AND s.subject_name != ''
        ORDER BY cs.start_time
        """
        df = execute_query_df(query, (day_name, student_name))
    else:
        # Get all schedule for the day (original behavior)
        query = """
        SELECT 
            s.subject_name as subject, 
            cs.class_type as type, 
            cs.start_time, 
            cs.end_time,
            cs.room_number as room,
            t.name as professor_name
        FROM class_schedules_enhanced cs
        JOIN subjects_enhanced s ON cs.subject_id = s.subject_id
        JOIN teachers_enhanced t ON cs.teacher_id = t.teacher_id
        WHERE cs.day_of_week = ? AND s.subject_name != '' AND cs.status = 'active'
        ORDER BY cs.start_time
        """
        df = execute_query_df(query, (day_name,))
    
    conn.close()
    return df

def get_attendance_history(student_name, days=7):
    """Get attendance history for the past N days"""
    conn = get_db_connection()
    
    # Calculate date range
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days-1)
    
    # Format for SQLite
    start_str = f"{start_date} 00:00:00"
    end_str = f"{end_date} 23:59:59"
    
    # SQL query to get daily attendance counts
    query = """
    SELECT 
        date(timestamp) as date,
        COUNT(DISTINCT strftime('%H', timestamp)) as hours_present,
        COUNT(*) as detection_count
    FROM attendance_records
    WHERE name = ? AND timestamp BETWEEN ? AND ?
    GROUP BY date(timestamp)
    ORDER BY date(timestamp)
    """
    
    df = pd.read_sql(query, conn, params=(student_name, start_str, end_str))
    conn.close()
    
    # Create full date range with zeros for missing dates
    all_dates = pd.date_range(start=start_date, end=end_date, freq='D')
    date_df = pd.DataFrame({'date': all_dates})
    date_df['date'] = date_df['date'].dt.strftime('%Y-%m-%d')
    
    # Merge with attendance data
    result = pd.merge(date_df, df, on='date', how='left')
    
    # Fix the FutureWarning by explicitly inferring object types after filling NAs
    result = result.fillna(0)
    result = result.infer_objects(copy=False)  # Explicitly infer proper types instead of silent downcasting
    
    # Ensure integer types
    result[['hours_present', 'detection_count']] = result[['hours_present', 'detection_count']].astype(int)
    
    return result

def check_attendance(student_name, date, start_time, end_time):
    """
    Check if student attended a class during the specified time period
    using the attendance_records table instead of the non-existent class_attendance table
    
    Args:
        student_name (str): Name of the student
        date (str): Date in format 'YYYY-MM-DD'
        start_time (str): Class start time (e.g., '9:00 AM')
        end_time (str): Class end time (e.g., '11:00 AM')
    
    Returns:
        bool: True if student attended, False otherwise
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Normalize time formats to ensure consistency
    start_time = normalize_time_format(start_time)
    end_time = normalize_time_format(end_time)
    
    try:
        # Check if class_attendance table exists - if so, use it
        execute_query("SELECT name FROM sqlite_master WHERE type='table' AND name='class_attendance'")
        if cursor.fetchone():
            # Use the class_attendance table if it exists
            query = """
            SELECT attended
            FROM class_attendance
            WHERE student_name = ?
              AND class_date = ?
              AND start_time = ?
              AND end_time = ?
            """
            execute_query(query, (student_name, date, start_time, end_time))
            result = cursor.fetchone()
            
            if result is not None:
                # If we found a record, return its attendance status
                return result[0] == 1
        
        # If class_attendance table doesn't exist or no record found,
        # fall back to using attendance_records table
        
        # Format for SQLite date filtering
        date_start = f"{date}"
        
        # Query the attendance_records_enhanced table directly
        query = """
        SELECT COUNT(*) as count 
        FROM attendance_records_enhanced ar
        JOIN students_enhanced s ON ar.student_id = s.student_id
        WHERE s.name = ? 
          AND ar.attendance_date = ?
          AND ar.status = 'present'
        """
        
        execute_query(query, (student_name, date))
        result = cursor.fetchone()
        attended = result[0] > 0
        
        return attended
    except Exception as e:
        print(f"Error checking attendance: {e}")
        return False
    finally:
        conn.close()

def check_attendance_for_subject(student_name, date, subject_name):
    """
    Check if student attended a specific subject on a given date
    
    Args:
        student_name (str): Name of the student
        date (str): Date in format 'YYYY-MM-DD'
        subject_name (str): Name of the subject
    
    Returns:
        bool: True if student attended, False otherwise
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Query the attendance_records_enhanced table for specific subject
        query = """
        SELECT COUNT(*) as count 
        FROM attendance_records_enhanced ar
        JOIN students_enhanced s ON ar.student_id = s.student_id
        JOIN subjects_enhanced se ON ar.subject_id = se.subject_id
        WHERE s.name = ? 
          AND ar.attendance_date = ?
          AND se.subject_name = ?
          AND ar.status = 'present'
        """
        
        cursor.execute(query, (student_name, date, subject_name))
        result = cursor.fetchone()
        attended = result[0] > 0
        
        return attended
    except Exception as e:
        return False
    finally:
        conn.close()

def get_attendance_count_by_hour(student_name, date):
    """Get attendance count by hour for the given date"""
    conn = get_db_connection()
    
    # Format for SQLite
    date_start = f"{date} 00:00:00"
    date_end = f"{date} 23:59:59"
    
    query = """
    SELECT 
        strftime('%H', timestamp) as hour,
        COUNT(*) as count
    FROM attendance_records
    WHERE name = ? AND timestamp BETWEEN ? AND ?
    GROUP BY strftime('%H', timestamp)
    ORDER BY hour
    """
    
    df = pd.read_sql(query, conn, params=(student_name, date_start, date_end))
    conn.close()
    
    # Create full hour range (8-20)
    hour_range = list(range(8, 21))
    hour_df = pd.DataFrame({'hour': [str(h).zfill(2) for h in hour_range]})
    
    # Merge with attendance data
    result = pd.merge(hour_df, df, on='hour', how='left')
    result = result.fillna(0)
    result['count'] = result['count'].astype(int)
    
    # Add formatted hour for display
    result['hour_display'] = result['hour'].apply(lambda h: f"{h}:00")
    
    return result

def get_time_until(time_obj):
    """Calculate time until a specific time today"""
    now = datetime.now()
    target = datetime.combine(now.date(), time_obj)
    
    if target < now:
        return "Started"
    
    diff = target - now
    
    hours, remainder = divmod(diff.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    else:
        return f"{minutes}m {seconds}s"

def create_timeline_chart(schedule_df, current_time_obj, student_name, date_str):
    """Create an interactive timeline chart of the day's schedule"""
    # Prepare data
    classes = []
    
    for _, row in schedule_df.iterrows():
        subject = row['subject']
        subject_type = "Lecture" if row['type'] == 'lec' else "Section"
        
        # Ensure times are in AM/PM format
        start_time = normalize_time_format(row['start_time'])
        end_time = normalize_time_format(row['end_time'])
        
        # Convert AM/PM times to datetime for plotting
        try:
            # Try to parse as AM/PM format first
            start_dt = datetime.strptime(f"2023-01-01 {start_time}", "%Y-%m-%d %I:%M %p")
            end_dt = datetime.strptime(f"2023-01-01 {end_time}", "%Y-%m-%d %I:%M %p")
            
            # Also create time objects for comparison
            start_time_obj = datetime.strptime(start_time, '%I:%M %p').time()
            end_time_obj = datetime.strptime(end_time, '%I:%M %p').time()
        except ValueError:
            # If format doesn't match, try alternate format
            try:
                # Get normalized AM/PM format strings
                start_time = normalize_time_format(start_time)
                end_time = normalize_time_format(end_time)
                
                start_dt = datetime.strptime(f"2023-01-01 {start_time}", "%Y-%m-%d %I:%M %p")
                end_dt = datetime.strptime(f"2023-01-01 {end_time}", "%Y-%m-%d %I:%M %p")
                
                # Create time objects for comparison  
                start_time_obj = datetime.strptime(start_time, '%I:%M %p').time()
                end_time_obj = datetime.strptime(end_time, '%I:%M %p').time()
            except ValueError:
                # If still fails, skip this entry
                continue
        
        # Check attendance
        attended = check_attendance_for_subject(student_name, date_str, subject)
        
        # Check if class is current, past, or upcoming
        if current_time_obj >= end_time_obj:
            # Past classes - green if attended, red if absent
            status = "Attended" if attended else "Missed"
            color = "#4CAF50" if attended else "#f44336"  # Green for attended, Red for missed
        elif current_time_obj >= start_time_obj:
            # Current class - always orange
            status = "Current"
            color = "#FF9800"  # Orange
        else:
            # Upcoming class - always blue
            status = "Upcoming"
            color = "#2196F3"  # Blue
        
        # Add to classes list
        classes.append({
            'Subject': f"{subject} ({subject_type})",
            'Start': start_dt,
            'End': end_dt,
            'Status': status,
            'Attended': "Yes" if attended and status != "Upcoming" else "No" if status != "Upcoming" else "",
            'Color': color
        })
    
    if not classes:
        return None
    
    # Convert to DataFrame
    df = pd.DataFrame(classes)
    
    # Create figure with custom colors
    fig = px.timeline(
        df, 
        x_start="Start", 
        x_end="End", 
        y="Subject",
        color="Status",
        color_discrete_map={
            "Attended": "#4CAF50",  # Green for attended
            "Missed": "#f44336",    # Red for missed
            "Current": "#FF9800",   # Orange for current
            "Upcoming": "#2196F3"   # Blue for upcoming
        },
        hover_data=["Status", "Attended"]
    )
    
    # Calculate dynamic height based on number of classes
    # Minimum height of 300px, then add 50px per class after 4 classes
    dynamic_height = max(300, 300 + (max(0, len(classes) - 4) * 50))
    
    # Update layout with dynamic height
    fig.update_layout(
        title="Today's Schedule Timeline",
        xaxis=dict(
            title="Time",
            tickformat="%I:%M %p",  # Use AM/PM format
            dtick=3600000,  # 1 hour in milliseconds
            range=[
                datetime.strptime("2023-01-01 08:00 AM", "%Y-%m-%d %I:%M %p"),
                datetime.strptime("2023-01-01 08:00 PM", "%Y-%m-%d %I:%M %p")
            ]
        ),
        yaxis=dict(
            title="",
            # Disable autorange to ensure all labels are visible
            autorange=True
        ),
        legend_title="Class Status",
        height=dynamic_height,  # Dynamic height based on number of classes
        margin=dict(l=10, r=10, t=40, b=10),
        # Make sure text doesn't get cut off
        uniformtext=dict(minsize=10, mode='show')
    )
    
    # Add vertical line for current time
    current_dt = datetime.strptime(f"2023-01-01 {current_time_obj.strftime('%I:%M %p')}", "%Y-%m-%d %I:%M %p")
    fig.add_vline(x=current_dt, line_width=2, line_dash="dash", line_color="red")
    
    # Add legend explanation
    fig.add_annotation(
        x=0.02, 
        y=1.15, 
        xref="paper", 
        yref="paper",
        text="✅ Attended classes are green | ❌ Missed classes are red | 🟠 Current class is orange | 🔵 Upcoming classes are blue",
        showarrow=False,
        font=dict(size=10),
        align="left"
    )
    
    return fig

def create_attendance_history_chart(history_df):
    """Create an attendance history chart"""
    fig = go.Figure()
    
    # Add bar chart for detection count
    fig.add_trace(go.Bar(
        x=history_df['date'],
        y=history_df['detection_count'],
        name='Detections',
        marker_color='rgba(108, 125, 209, 0.7)',
        hovertemplate='Date: %{x}<br>Detections: %{y}<extra></extra>'
    ))
    
    # Add line chart for hours present
    fig.add_trace(go.Scatter(
        x=history_df['date'],
        y=history_df['hours_present'],
        name='Hours Present',
        mode='lines+markers',
        marker=dict(size=8, color='#FF9800'),
        line=dict(width=2, color='#FF9800'),
        hovertemplate='Date: %{x}<br>Hours Present: %{y}<extra></extra>'
    ))
    
    # Update layout
    fig.update_layout(
        title='Your Attendance History',
        xaxis_title='Date',
        yaxis_title='Count',
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        height=300,
        margin=dict(l=10, r=10, t=40, b=10)
    )
    
    return fig

def create_hourly_attendance_chart(hourly_df):
    """Create hourly attendance chart"""
    fig = go.Figure()
    
    # Add the bar chart
    fig.add_trace(go.Bar(
        x=hourly_df['hour_display'],
        y=hourly_df['count'],
        marker_color='rgba(108, 125, 209, 0.7)',
        hovertemplate='Hour: %{x}<br>Detections: %{y}<extra></extra>'
    ))
    
    # Update layout
    fig.update_layout(
        title='Today\'s Attendance by Hour',
        xaxis_title='Hour of Day',
        yaxis_title='Detection Count',
        height=300,
        margin=dict(l=10, r=10, t=40, b=10)
    )
    
    return fig

def get_dynamic_time_card_html(subject, subject_type, start_time, end_time, is_current, is_past, attended, show_attendance, time_status, time_color, card_id):
    """Create a class card with dynamic time updates using an HTML component"""
    
    # Determine if we need a countdown timer
    needs_countdown = not is_current and not is_past
    
    # Parse the start time
    try:
        # Try AM/PM format
        start_time_parts = start_time.split(' ')
        if len(start_time_parts) == 2:  # AM/PM format
            time_part = start_time_parts[0]
            am_pm = start_time_parts[1]
            time_hours, time_minutes = time_part.split(':')
            military_hour = int(time_hours)
            if am_pm == 'PM' and military_hour < 12:
                military_hour += 12
            elif am_pm == 'AM' and military_hour == 12:
                military_hour = 0
        else:  # 24-hour format
            time_hours, time_minutes = start_time.split(':')
            military_hour = int(time_hours)
    except Exception as e:
        print(f"Error parsing time: {e}")
        military_hour = 0
        time_minutes = 0
    
    # Generate the same card HTML but now with inline JavaScript if it's an upcoming class
    if is_current:
        # Current class card
        card_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                .class-card {{
                    padding: 15px; 
                    border-radius: 10px;
                    border: 2px solid #FF9800;
                    background-color: white;
                    text-align: center;
                    box-shadow: 0 4px 10px rgba(255, 152, 0, 0.2);
                    height: 100%;
                }}
                .header-banner {{
                    background-color: #FF9800;
                    color: white;
                    padding: 8px;
                    margin: -15px -15px 10px -15px;
                    border-radius: 10px 10px 0 0;
                    text-align: center;
                }}
                h3 {{
                    margin: 0;
                    color: black;
                    font-size: 1.2em;
                    text-align: center;
                    font-weight: 600;
                }}
                .attendance-badge {{
                    margin-top: 12px;
                    padding: 8px;
                    border-radius: 6px;
                    background-color: {"#4CAF50" if attended else "#f44336"};
                    border: none;
                    text-align: center;
                }}
                .badge-text {{
                    margin: 0;
                    font-weight: bold;
                    color: white;
                    font-size: 1.1em;
                    text-shadow: 0 1px 1px rgba(0,0,0,0.2);
                }}
            </style>
        </head>
        <body>
            <div class="class-card">
                <div class="header-banner">
                    <strong style="font-size:1.1em;">📌 CURRENT CLASS</strong>
                </div>
                <h3>{subject}</h3>
                <p style="color:black; margin:4px 0; text-align:center;">
                    <strong>({'Lecture' if subject_type == 'lec' else 'Section'})</strong>
                </p>
                <p style="font-size:1.1em; margin:10px 0; text-align:center; color:#333333;"><strong>⏰ {start_time} - {end_time}</strong></p>
                <p style="margin:0; color:{time_color}; font-weight:bold; text-align:center;">
                    <span>{time_status}</span>
                </p>
                {f'''
                <div class="attendance-badge">
                    <p class="badge-text">{"✅ ATTENDED" if attended else "❌ ABSENT"}</p>
                </div>''' if show_attendance else ''}
            </div>
        </body>
        </html>
        """
    elif is_past:
        # Past class
        attendance_color = '#2E7D32' if attended else '#C62828'
        card_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                .class-card {{
                    padding: 15px; 
                    border-radius: 10px;
                    border: 2px solid {attendance_color};
                    background-color: white;
                    text-align: center;
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                    height: 100%;
                }}
                h3 {{
                    margin: 0;
                    color: black;
                    font-size: 1.3em;
                    font-weight: 600;
                }}
                .attendance-badge {{
                    margin-top: 12px;
                    padding: 8px;
                    border-radius: 6px;
                    background-color: {"#4CAF50" if attended else "#f44336"};
                    border: none;
                }}
                .badge-text {{
                    margin: 0;
                    font-weight: bold;
                    color: white;
                    font-size: 1.1em;
                    text-shadow: 0 1px 1px rgba(0,0,0,0.2);
                }}
            </style>
        </head>
        <body>
            <div class="class-card">
                <h3>{subject}</h3>
                <p style="color:black; margin:4px 0;">
                    <strong>({'Lecture' if subject_type == 'lec' else 'Section'})</strong>
                </p>
                <p style="font-size:1.1em; margin:10px 0; color:#333333;"><strong>⏰ {start_time} - {end_time}</strong></p>
                <p style="margin:0; color:#555555; font-weight:500;">
                    <span>{time_status}</span>
                </p>
                <div class="attendance-badge">
                    <p class="badge-text">{"✅ ATTENDED" if attended else "❌ ABSENT"}</p>
                </div>
            </div>
        </body>
        </html>
        """
    else:
        # Upcoming class with JavaScript countdown
        card_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                .class-card {{
                    padding: 15px; 
                    border-radius: 10px;
                    border: 1px solid #2196F3;
                    background-color: white;
                    text-align: center;
                    box-shadow: 0 2px 8px rgba(33, 150, 243, 0.15);
                    height: 100%;
                }}
                h3 {{
                    margin: 0;
                    color: black;
                    font-size: 1.3em;
                    font-weight: 600;
                }}
            </style>
            <script>
                // Wait for the document to be ready
                document.addEventListener("DOMContentLoaded", function() {{
                    // Function to update the countdown
                    function updateCountdown() {{
                        const now = new Date();
                        const today = new Date(now.getFullYear(), now.getMonth(), now.getDate(), {military_hour}, {time_minutes}, 0);
                        
                        // If target is in the past, don't show countdown
                        if (today < now) {{
                            document.getElementById("countdown").textContent = "Started";
                            document.getElementById("countdown").style.color = "#FF9800";
                            return;
                        }}
                        
                        // Calculate time difference
                        const diff = today - now;
                        const hours = Math.floor(diff / (1000 * 60 * 60));
                        const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
                        const seconds = Math.floor((diff % (1000 * 60)) / 1000);
                        
                        // Format the countdown text
                        const countdownText = hours > 0 
                            ? `${{hours}}h ${{minutes}}m ${{seconds}}s` 
                            : `${{minutes}}m ${{seconds}}s`;
                        
                        // Update the element
                        document.getElementById("countdown").textContent = countdownText;
                        
                        // Check if class has started
                        if (diff <= 0) {{
                            document.getElementById("status").textContent = "CLASS IN PROGRESS";
                            document.getElementById("status").style.color = "#FF9800";
                            return;
                        }}
                        
                        // Call this function again in 1 second
                        setTimeout(updateCountdown, 1000);
                    }}
                    
                    // Start the countdown immediately
                    updateCountdown();
                }});
            </script>
        </head>
        <body>
            <div class="class-card">
                <h3>{subject}</h3>
                <p style="color:black; margin:4px 0;">
                    <strong>({'Lecture' if subject_type == 'lec' else 'Section'})</strong>
                </p>
                <p style="font-size:1.1em; margin:10px 0; color:#333333;"><strong>⏰ {start_time} - {end_time}</strong></p>
                <p style="margin:0; color:#0277BD; font-weight:bold;">
                    <span id="status">Starts in <span id="countdown">{time_status.replace('Starts in ', '')}</span></span>
                </p>
            </div>
        </body>
        </html>
        """
    
    return card_html

# Add this function for dynamic welcome message
def welcome_countdown_html(student_name, next_class=None, missed_count=0, attended_all=False, no_classes=False):
    """Create HTML for a welcome message with dynamic countdown if there's a next class"""
    
    if next_class is not None:
        # Parse the next class time
        start_time = next_class['start_time']
        subject = next_class['subject']
        
        try:
            # Try AM/PM format
            start_time_parts = start_time.split(' ')
            if len(start_time_parts) == 2:  # AM/PM format
                time_part = start_time_parts[0]
                am_pm = start_time_parts[1]
                time_hours, time_minutes = time_part.split(':')
                military_hour = int(time_hours)
                if am_pm == 'PM' and military_hour < 12:
                    military_hour += 12
                elif am_pm == 'AM' and military_hour == 12:
                    military_hour = 0
            else:  # 24-hour format
                time_hours, time_minutes = start_time.split(':')
                military_hour = int(time_hours)
        except Exception as e:
            print(f"Error parsing time: {e}")
            military_hour = 0
            time_minutes = 0
        
        if missed_count > 0:
            message_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <script>
                    document.addEventListener("DOMContentLoaded", function() {{
                        function updateWelcomeCountdown() {{
                            const now = new Date();
                            const today = new Date(now.getFullYear(), now.getMonth(), now.getDate(), {military_hour}, {time_minutes}, 0);
                            
                            if (today < now) {{
                                document.getElementById("next-class-time").textContent = "now";
                                return;
                            }}
                            
                            const diff = today - now;
                            const hours = Math.floor(diff / (1000 * 60 * 60));
                            const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
                            const seconds = Math.floor((diff % (1000 * 60)) / 1000);
                            
                            const countdownText = hours > 0 
                                ? `${{hours}}h ${{minutes}}m ${{seconds}}s` 
                                : `${{minutes}}m ${{seconds}}s`;
                            
                            document.getElementById("next-class-time").textContent = countdownText;
                            setTimeout(updateWelcomeCountdown, 1000);
                        }}
                        updateWelcomeCountdown();
                    }});
                </script>
            </head>
            <body>
                <div style="background-color: #FFF3E0; color: #E65100; padding: 15px; border-radius: 5px; border-left: 5px solid #FF9800;">
                    <div style="font-size: 16px; font-weight: bold;">
                        👋 Welcome {student_name}. You missed {missed_count} {'class' if missed_count == 1 else 'classes'} today. 
                        Your next class is <strong>{subject}</strong> and starts in <span id="next-class-time">calculating...</span>
                    </div>
                </div>
            </body>
            </html>
            """
        else:
            message_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <script>
                    document.addEventListener("DOMContentLoaded", function() {{
                        function updateWelcomeCountdown() {{
                            const now = new Date();
                            const today = new Date(now.getFullYear(), now.getMonth(), now.getDate(), {military_hour}, {time_minutes}, 0);
                            
                            if (today < now) {{
                                document.getElementById("next-class-time").textContent = "now";
                                return;
                            }}
                            
                            const diff = today - now;
                            const hours = Math.floor(diff / (1000 * 60 * 60));
                            const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
                            const seconds = Math.floor((diff % (1000 * 60)) / 1000);
                            
                            const countdownText = hours > 0 
                                ? `${{hours}}h ${{minutes}}m ${{seconds}}s` 
                                : `${{minutes}}m ${{seconds}}s`;
                            
                            document.getElementById("next-class-time").textContent = countdownText;
                            setTimeout(updateWelcomeCountdown, 1000);
                        }}
                        updateWelcomeCountdown();
                    }});
                </script>
            </head>
            <body>
                <div style="background-color: #E3F2FD; color: #0D47A1; padding: 15px; border-radius: 5px; border-left: 5px solid #2196F3;">
                    <div style="font-size: 16px; font-weight: bold;">
                        👋 Welcome {student_name}! Your next class is <strong>{subject}</strong> and starts in <span id="next-class-time">calculating...</span>
                    </div>
                </div>
            </body>
            </html>
            """
    elif attended_all:
        message_html = f"""
        <div style="background-color: #E8F5E9; color: #2E7D32; padding: 15px; border-radius: 5px; border-left: 5px solid #4CAF50;">
            <div style="font-size: 16px; font-weight: bold;">
                👋 Well done, {student_name}! You have attended all your classes for today. ✅
            </div>
        </div>
        """
    elif missed_count > 0:
        message_html = f"""
        <div style="background-color: #FFEBEE; color: #C62828; padding: 15px; border-radius: 5px; border-left: 5px solid #F44336;">
            <div style="font-size: 16px; font-weight: bold;">
                👋 Welcome {student_name}. You have no more classes today, but you missed {missed_count} {'class' if missed_count == 1 else 'classes'} today.
            </div>
        </div>
        """
    else:
        message_html = f"""
        <div style="background-color: #E3F2FD; color: #0D47A1; padding: 15px; border-radius: 5px; border-left: 5px solid #2196F3;">
            <div style="font-size: 16px; font-weight: bold;">
                👋 Welcome {student_name}! There were no classes scheduled for today.
            </div>
        </div>
        """
    
    return message_html

# Update the show_student_report function to use these new components
# In the section where you show welcome message:

# Enhance attendance summary and add attendance history visualization

# Add a new function to get weekly and monthly attendance data
def get_extended_attendance_history(student_name, days=30):
    """
    Get extended attendance history for visualization using enhanced schema
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Calculate date range
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    
    # Format for SQLite
    start_str = f"{start_date}"
    end_str = f"{end_date}"
    
    try:
        # Use enhanced schema to get attendance history
        query = """
        WITH daily_attendance AS (
            -- Get attendance data by day and subject using enhanced tables
            SELECT 
                ar.attendance_date as date,
                se.subject_name as subject,
                COUNT(CASE WHEN ar.status = 'present' THEN 1 END) as attended_classes,
                COUNT(*) as total_classes
            FROM attendance_records_enhanced ar
            JOIN students_enhanced s ON ar.student_id = s.student_id
            JOIN subjects_enhanced se ON ar.subject_id = se.subject_id
            WHERE s.name = ? 
              AND ar.attendance_date BETWEEN ? AND ?
            GROUP BY ar.attendance_date, se.subject_name
        ),
        daily_totals AS (
            -- Get total attendance data per day
            SELECT 
                date,
                SUM(attended_classes) as attended_classes,
                SUM(total_classes) as total_classes
            FROM daily_attendance
            GROUP BY date
        )
        -- Return the aggregated data
        SELECT 
            dt.date,
            'Overall' as subject,
            dt.attended_classes,
            dt.total_classes,
            0 as hours_present,
            0 as detection_count
        FROM daily_totals dt
        ORDER BY dt.date
        """
        
        df = pd.read_sql_query(query, conn, params=(student_name, start_str, end_str))
        
        if df.empty:
            # Create empty DataFrame with expected structure
            df = pd.DataFrame(columns=[
                'date', 'subject', 'attended_classes', 'total_classes', 'hours_present', 'detection_count'
            ])
        
    except Exception as e:
        print(f"Error in get_extended_attendance_history: {e}")
        # Return empty DataFrame with expected structure
        df = pd.DataFrame(columns=[
            'date', 'subject', 'attended_classes', 'total_classes', 'hours_present', 'detection_count'
        ])
        if not df.empty:
            # Get class schedule info
            cursor.execute("""
            SELECT DISTINCT s.subject_name
            FROM class_schedules_enhanced cs
            JOIN subjects_enhanced s ON cs.subject_id = s.subject_id
            LIMIT 5
            """)
            subjects = [row[0] for row in cursor.fetchall()]
            
            # Add a default subject if none found
            if not subjects:
                subjects = ["Default Subject"]
            
            # Add the missing columns with estimated values
            df['subject'] = subjects[0]  # Assign first subject as placeholder
            
            # Estimate attended classes based on detection count
            df['attended_classes'] = df['detection_count'].apply(lambda x: 1 if x > 0 else 0)
            df['total_classes'] = 1  # Assume 1 class per day as fallback
        else:
            # Create empty dataframe with required columns
            df = pd.DataFrame(columns=[
                'date', 'subject', 'attended_classes', 'total_classes', 
                'hours_present', 'detection_count'
            ])
    
    # Create full date range
    all_dates = pd.date_range(start=start_date, end=end_date, freq='D')
    date_df = pd.DataFrame({'date': all_dates})
    date_df['date'] = date_df['date'].dt.strftime('%Y-%m-%d')
    date_df['day_name'] = pd.to_datetime(date_df['date']).dt.day_name()
    date_df['day_of_week'] = pd.to_datetime(date_df['date']).dt.dayofweek
    
    # Add week number (relative to start date)
    date_df['week'] = ((pd.to_datetime(date_df['date']) - pd.to_datetime(start_date)).dt.days // 7) + 1
    
    # If we have an empty dataframe or missing data, handle it gracefully
    if df.empty:
        # Create a dataframe with all dates and zero counts
        result = date_df.copy()
        result['hours_present'] = 0
        result['detection_count'] = 0
        result['attended_classes'] = 0
        result['total_classes'] = 0
        result['subject'] = "No Data"
        result['attendance_rate'] = 0
    else:
        # Merge with date range to ensure all dates are represented
        result = pd.merge(date_df, df, on='date', how='left')
        
        # Fill NaN values with zeros for numeric columns
        numeric_cols = ['hours_present', 'detection_count', 'attended_classes', 'total_classes']
        result[numeric_cols] = result[numeric_cols].fillna(0)
        
        # Calculate attendance rate
        result['attendance_rate'] = result.apply(
            lambda row: (row['attended_classes'] / row['total_classes'] * 100) 
                        if row['total_classes'] > 0 else 0, 
            axis=1
        )
    
    conn.close()
    
    # Convert numeric columns to integers
    int_columns = ['hours_present', 'detection_count', 'total_classes', 'attended_classes', 'day_of_week']
    for col in int_columns:
        if col in result.columns:
            result[col] = result[col].fillna(0).astype(int)
    
    return result

# Add function to create attendance history charts
def create_attendance_history_dashboards(history_df):
    """Create comprehensive attendance history visualizations"""
    
    # Weekly attendance rate chart
    weekly_data = history_df.groupby('week').agg({
        'attended_classes': 'sum',
        'total_classes': 'sum'
    }).reset_index()
    
    weekly_data['attendance_rate'] = weekly_data.apply(
        lambda row: (row['attended_classes'] / row['total_classes'] * 100) if row['total_classes'] > 0 else 0,
        axis=1
    )
    
    fig1 = go.Figure()
    
    fig1.add_trace(go.Bar(
        x=weekly_data['week'],
        y=weekly_data['attendance_rate'],
        marker=dict(
            color=weekly_data['attendance_rate'],
            colorscale='RdYlGn',
            cmin=0,
            cmax=100
        ),
        hovertemplate='Week %{x}<br>Attendance: %{y:.1f}%<extra></extra>'
    ))
    
    fig1.update_layout(
        title='Weekly Attendance Rate',
        xaxis=dict(
            title="Week",
            tickmode='linear',
            tick0=1,
            dtick=1
        ),
        yaxis=dict(
            title="Attendance Rate (%)",
            range=[0, 100]
        ),
        height=300,
        margin=dict(l=10, r=10, t=40, b=10)
    )
    
    # Add reference line for 80% attendance
    fig1.add_shape(
        type="line",
        x0=0,
        y0=80,
        x1=max(weekly_data['week']) + 0.5,
        y1=80,
        line=dict(
            color="red",
            width=2,
            dash="dash",
        )
    )
    fig1.add_annotation(
        x=1,
        y=82,
        text="80% Target",
        showarrow=False,
        font=dict(color="red")
    )
    
    # Modify the daily attendance pattern to start with Saturday
    daily_pattern = history_df.groupby('day_of_week').agg({
        'attended_classes': 'sum',
        'total_classes': 'sum',
        'day_name': 'first'
    }).reset_index()
    
    daily_pattern['attendance_rate'] = daily_pattern.apply(
        lambda row: (row['attended_classes'] / row['total_classes'] * 100) if row['total_classes'] > 0 else 0,
        axis=1
    )
    
    # Custom day order starting with Saturday
    custom_day_order = {
        "Saturday": 0,
        "Sunday": 1, 
        "Monday": 2, 
        "Tuesday": 3, 
        "Wednesday": 4, 
        "Thursday": 5, 
        "Friday": 6
    }
    
    # Add custom sort key
    daily_pattern['day_order'] = daily_pattern['day_name'].map(custom_day_order)
    
    # Sort by our custom order
    daily_pattern = daily_pattern.sort_values('day_order')
    
    # Create day pattern chart with new order
    fig2 = go.Figure()
    
    fig2.add_trace(go.Scatter(
        x=daily_pattern['day_name'],
        y=daily_pattern['attendance_rate'],
        mode='lines+markers',
        marker=dict(
            size=10,
            color=daily_pattern['attendance_rate'],
            colorscale='RdYlGn',
            cmin=0,
            cmax=100,
            line=dict(width=2, color='white')
        ),
        line=dict(width=2, color='#1E88E5'),
        hovertemplate='%{x}<br>Attendance: %{y:.1f}%<extra></extra>'
    ))
    
    fig2.update_layout(
        title='Attendance Pattern by Day of Week',
        xaxis=dict(
            title='',
            categoryorder='array',
            categoryarray=daily_pattern['day_name'].tolist()
        ),
        yaxis=dict(
            title="Attendance Rate (%)",
            range=[0, 100]
        ),
        height=300,
        margin=dict(l=10, r=10, t=40, b=10)
    )
    
    # Recent daily attendance
    recent_df = history_df.tail(14).copy()  # Last 2 weeks
    recent_df['formatted_date'] = pd.to_datetime(recent_df['date']).dt.strftime('%b %d')
    
    fig3 = go.Figure()
    
    fig3.add_trace(go.Scatter(
        x=recent_df['formatted_date'],
        y=recent_df['attended_classes'],
        name='Attended',
        mode='lines+markers',
        marker=dict(size=8, color='#4CAF50', line=dict(width=1, color='white')),
        line=dict(width=2, color='#4CAF50'),
        fill='tozeroy',
        fillcolor='rgba(76, 175, 80, 0.2)',
        hovertemplate='%{x}<br>Attended: %{y}<extra></extra>'
    ))
    
    fig3.add_trace(go.Scatter(
        x=recent_df['formatted_date'],
        y=recent_df['total_classes'],
        name='Total Classes',
        mode='lines+markers',
        marker=dict(size=8, color='#FFA726', line=dict(width=1, color='white')),
        line=dict(width=2, color='#FFA726', dash='dot'),
        hovertemplate='%{x}<br>Total: %{y}<extra></extra>'
    ))
    
    fig3.update_layout(
        title='Daily Attendance (Last 2 Weeks)',
        xaxis_title='',
        yaxis_title='Classes',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        height=300,
        margin=dict(l=10, r=10, t=40, b=10)
    )
    
    return fig1, fig2, fig3

# Add a new function to create a better subject bar chart with percentages
def create_subject_bar_chart(history_df):
    """Create a bar chart showing attendance rates by subject with percentages"""
    
    # If dataframe is empty or doesn't have subject column, return empty chart
    if history_df.empty or 'subject' not in history_df.columns:
        fig = go.Figure()
        fig.update_layout(
            title="No subject data available",
            xaxis=dict(title="Subject"),
            yaxis=dict(title="Attendance Rate (%)"),
            height=400
        )
        return fig
    
    # Group data by subject
    subject_stats = history_df.groupby('subject').agg({
        'attended_classes': 'sum',
        'total_classes': 'sum'
    }).reset_index()
    
    # Calculate attendance rate
    subject_stats['attendance_rate'] = subject_stats.apply(
        lambda row: (row['attended_classes'] / row['total_classes'] * 100) 
                    if row['total_classes'] > 0 else 0,
        axis=1
    )
    
    # Sort by attendance rate (high to low)
    subject_stats = subject_stats.sort_values('attendance_rate', ascending=False)
    
    # Create bar chart
    fig = go.Figure()
    
    # Add bars with percentage labels
    fig.add_trace(go.Bar(
        x=subject_stats['subject'],
        y=subject_stats['attendance_rate'],
        text=[f"{rate:.1f}%" for rate in subject_stats['attendance_rate']],
        textposition='outside',
        marker=dict(
            color=subject_stats['attendance_rate'],
            colorscale='RdYlGn',
            cmin=0,
            cmax=100
        ),
        hovertemplate=
        '%{x}<br>' +
        'Attendance Rate: %{y:.1f}%<br>' +
        'Classes: %{customdata[0]}/%{customdata[1]}<extra></extra>',
        customdata=subject_stats[['attended_classes', 'total_classes']].values
    ))
    
    # Add target line at 80%
    fig.add_shape(
        type="line",
        x0=-0.5,
        x1=len(subject_stats)-0.5,
        y0=80,
        y1=80,
        line=dict(
            color="red",
            width=2,
            dash="dash",
        ),
        name="Target (80%)"
    )
    
    fig.add_annotation(
        xref="paper",
        yref="y",
        x=1,
        y=80,
        text="80% Target",
        showarrow=False,
        font=dict(color="red"),
        xanchor="right"
    )
    
    # Update layout
    fig.update_layout(
        title="Attendance Rate by Subject",
        xaxis=dict(
            title="",
            tickangle=-45
        ),
        yaxis=dict(
            title="Attendance Rate (%)",
            range=[0, max(100, subject_stats['attendance_rate'].max() * 1.1)]
        ),
        height=450,
        margin=dict(l=10, r=10, t=40, b=100)
    )
    
    return fig

# Restore dashboard title while maintaining zero spacing

def show_student_report():
    # Apply global CSS - will only inject once per session
    apply_global_css()
    
    # Apply student-specific styles only once
    if 'student_css_added' not in st.session_state:
        st.session_state.student_css_added = True
        st.markdown("""
        <style>
        /* Super aggressive top space elimination specific to student dashboard */
        body .main .block-container,
        .main .block-container,
        div.block-container {
            padding-top: 0 !important;
            margin-top: 0 !important;
        }
        
        /* Dashboard title styling that aligns with the username and buttons */
        .dashboard-header {
            display: flex;
            align-items: center;
            width: %;
            margin: 0 !important;
            padding: 0 !important;
        }
        
        .dashboard-title {
            margin: 0 !important;
            padding: 0 !important;
            font-size: 1.5rem !important;
            color: #1E88E5 !important;
            font-weight: bold !important;
        }
        </style>
        """, unsafe_allow_html=True)
    
    # Initialize session state for auto-refresh
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = datetime.now()
        st.session_state.is_refreshing = False
    
    # Initialize refresh_count if not exists
    if 'refresh_count' not in st.session_state:
        st.session_state.refresh_count = 0
    
    # Check login status from both session state and query params
    if 'username' not in st.session_state:
        # Check if logged_in parameter exists in URL
        if "logged_in" in st.query_params and st.query_params["logged_in"] == "True":
            if "username" in st.query_params:
                # Restore login state from query parameters
                st.session_state.logged_in = True
                st.session_state.username = st.query_params["username"]
            else:
                st.error("Please log in to view your attendance")
                st.stop()
        else:
            st.error("Please log in to view your attendance")
            st.stop()
    
    # Ensure query parameters are updated with current session state
    if 'username' in st.session_state:
        st.query_params["logged_in"] = "True"
        st.query_params["username"] = st.session_state.username
    
    # Get current student data SECURELY
    student_data = get_secure_student_data()
    student_name = student_data['student_name']
    student_id = student_data['student_id']
    section = student_data['section']
    
    # Use securely retrieved student name for all data queries
    # Replace any hardcoded st.session_state.username with student_name
    
    # Get current date and time
    today = datetime.now().date()
    date_str = today.strftime('%Y-%m-%d')
    day_name = today.strftime('%A')
    current_time_obj = datetime.now().time()
    
    # IMPROVED LAYOUT: Put title, username and buttons all in the same container
    st.markdown('<div style="margin-top: 0; padding-top: 0;">', unsafe_allow_html=True)
    top_col1, top_col2 = st.columns([3, 2])
    
    # Put the dashboard title in the first column
    with top_col1:
        st.markdown("""
        <div class="dashboard-header">
            <h2 class="dashboard-title">📚 My Attendance Dashboard</h2>
        </div>
        """, unsafe_allow_html=True)
    
    # User info and buttons in column 2
    with top_col2:
        # Add custom CSS for the header buttons
        st.markdown("""
        <style>
        /* Header buttons container */
        .header-buttons-container {
            display: flex;
            align-items: center;
            justify-content: flex-end;
            gap: 15px;
            margin-bottom: 10px;
        }
        
        /* Enhanced user info styling - compact and centered */
        .user-info-badge {
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            color: white;
            padding: 10px 15px;
            border-radius: 15px;
            font-weight: 600;
            font-size: 14px;
            text-shadow: 0 1px 3px rgba(0,0,0,0.3);
            box-shadow: 0 3px 12px rgba(40, 167, 69, 0.3);
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 15px;
            position: relative;
            overflow: hidden;
            height: 50px;
            text-align: center;
        }
        
        .user-info-badge:before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
            transition: left 0.8s;
        }
        
        .user-info-badge:hover:before {
            left: 100%;
        }
        
        /* Custom button styling - Enhanced symmetric design */
        .stButton > button {
            border-radius: 25px !important;
            border: 2px solid #e9ecef !important;
            background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%) !important;
            color: #495057 !important;
            font-weight: 600 !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            height: 50px !important;
            min-height: 50px !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
            position: relative !important;
            overflow: hidden !important;
        }
        
        .stButton > button:before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
            transition: left 0.5s;
        }
        
        .stButton > button:hover:before {
            left: 100%;
        }
        
        .stButton > button:hover {
            transform: translateY(-3px) !important;
            box-shadow: 0 8px 25px rgba(0,0,0,0.15) !important;
        }
        
        /* Refresh button - Green theme with improved symmetry */
        div[data-testid="column"]:nth-child(1) .stButton > button {
            border-color: #28a745 !important;
            color: #28a745 !important;
            background: linear-gradient(135deg, #ffffff 0%, #f8fff9 100%) !important;
        }
        
        div[data-testid="column"]:nth-child(1) .stButton > button:hover {
            background: linear-gradient(135deg, #e8f5e9 0%, #d4edda 100%) !important;
            border-color: #1e7e34 !important;
            color: #1e7e34 !important;
            box-shadow: 0 8px 25px rgba(40, 167, 69, 0.25) !important;
        }
        
        /* Logout button - Red theme with symmetric design */
        div[data-testid="column"]:nth-child(2) .stButton > button {
            border-color: #dc3545 !important;
            color: #dc3545 !important;
            background: linear-gradient(135deg, #ffffff 0%, #fff8f8 100%) !important;
        }
        
        div[data-testid="column"]:nth-child(2) .stButton > button:hover {
            background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%) !important;
            border-color: #721c24 !important;
            color: #721c24 !important;
            box-shadow: 0 8px 25px rgba(220, 53, 69, 0.25) !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Create three-row layout: user info badge and two buttons with same width
        user_col1, user_col2 = st.columns([1, 1])
        
        # User info display spanning both columns
        st.markdown(f"""
        <div class="user-info-badge">
            👤 {student_name} | ID: {student_id} | Section: {section}
        </div>
        """, unsafe_allow_html=True)
        
        # Two buttons in a clean layout with same width as user badge
        button_col1, button_col2 = st.columns([1, 1])
        
        with button_col1:
            # Refresh button
            if st.button("🔄 Refresh", key="manual_refresh", use_container_width=True, help="Refresh attendance data"):
                st.session_state.last_refresh = datetime.now()
                st.session_state.is_refreshing = True
                st.session_state.refresh_count += 1
                st.rerun()
        
        with button_col2:
            # Logout button
            if st.button("🚪 Logout", key="logout_btn", use_container_width=True, help="Logout from system"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.query_params.clear()
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Get schedule for today (filtered by student's enrolled subjects)
    schedule_df = get_schedule_for_day(day_name, student_name)
    
    # Main content starts here
    
    # Show welcome message - but continue displaying data even if no schedule today
    if schedule_df.empty:
        # Create a welcome message for days with no classes
        welcome_message = f"""
        <div style="background-color: #E3F2FD; color: #0D47A1; padding: 15px; border-radius: 5px; border-left: 5px solid #2196F3; margin-bottom: 20px;">
            <div style="font-size: 16px; font-weight: bold;">
                👋 Welcome {student_name}! You have no classes scheduled for today ({day_name}).
                Here's your attendance history:
            </div>
        </div>
        """
        html(welcome_message, height=70)
        
        # Don't return/stop here - continue to show analytics
        st.info(f"No classes scheduled for today ({day_name})")
    else:
        # Show welcome message with next class info
        next_class = None
        
        # Parse times correctly handling AM/PM format
        for _, row in schedule_df.iterrows():
            try:
                # Try to parse as AM/PM format
                start_time_obj = datetime.strptime(row['start_time'], '%I:%M %p').time()
            except ValueError:
                try:
                    # Try to parse as 24-hour format
                    start_time_obj = datetime.strptime(row['start_time'], '%H:%M').time()
                except ValueError:
                    # Handle any other format issues
                    st.error(f"Invalid time format: {row['start_time']}")
                    continue
                
        # Initialize past_classes counter before using it
        past_classes = 0
        attended_past_classes = 0

        for _, row in schedule_df.iterrows():
            try:
                # Try to parse as AM/PM format
                start_time_obj = datetime.strptime(row['start_time'], '%I:%M %p').time()
                end_time_obj = datetime.strptime(row['end_time'], '%I:%M %p').time()
            except ValueError:
                try:
                    # Try to parse as 24-hour format
                    start_time_obj = datetime.strptime(row['start_time'], '%H:%M').time()
                    end_time_obj = datetime.strptime(row['end_time'], '%H:%M').time()
                except ValueError:
                    # Handle any other format issues
                    continue
            
            # Count classes that have started (consistent with dashboard metrics)
            if current_time_obj >= start_time_obj:
                past_classes += 1
                # Use the same attendance check as the dashboard metrics for consistency
                if check_attendance_for_subject(student_name, date_str, row['subject']):
                    attended_past_classes += 1

        # Now determine the welcome message based on attendance
        next_class = None

        # Find the next class if any
        for _, row in schedule_df.iterrows():
            try:
                # Try to parse as AM/PM format
                start_time_obj = datetime.strptime(row['start_time'], '%I:%M %p').time()
            except ValueError:
                try:
                    # Try to parse as 24-hour format
                        start_time_obj = datetime.strptime(row['start_time'], '%H:%M').time()
                except ValueError:
                    # Handle any other format issues
                    continue
            
            if start_time_obj > current_time_obj:
                next_class = row
                break

        # Display appropriate welcome message with dynamic countdown
        if next_class is None:
            # No more classes today
            if past_classes > 0 and attended_past_classes == past_classes:
                # Student attended all classes that have started today
                welcome_message = welcome_countdown_html(student_name, attended_all=True)
            elif past_classes > 0:
                # Some classes that started were missed
                missed = past_classes - attended_past_classes
                welcome_message = welcome_countdown_html(student_name, missed_count=missed)
            else:
                # No classes have started yet today
                welcome_message = welcome_countdown_html(student_name, no_classes=True)
        else:
            # There's an upcoming class - prepare it as a dictionary for the welcome_countdown_html function
            next_class_dict = {
                'subject': next_class['subject'],
                'start_time': next_class['start_time']
            }
            
            if past_classes > 0 and attended_past_classes < past_classes:
                # Student missed some classes that have started
                missed = past_classes - attended_past_classes
                welcome_message = welcome_countdown_html(student_name, next_class_dict, missed_count=missed)
            else:
                # Student has attended all classes that have started (or there were none)
                welcome_message = welcome_countdown_html(student_name, next_class_dict)

        # Display the welcome message with HTML component to enable JavaScript
        html(welcome_message, height=70)

        # Create interactive timeline
        st.subheader("📅 Today's Schedule")
        timeline_fig = create_timeline_chart(schedule_df, current_time_obj, student_name, date_str)
        if (timeline_fig):
            st.plotly_chart(timeline_fig, use_container_width=True)
        
        # Create detailed cards for each subject
        st.subheader("📚 Class Details")
        
        # Sort schedule by time, handling both 12-hour and 24-hour formats
        try:
            # First try to convert all times to datetime objects for sorting
            time_objs = []
            for idx, row in schedule_df.iterrows():
                try:
                    # Try AM/PM format
                    time_obj = datetime.strptime(row['start_time'], '%I:%M %p').time()
                except ValueError:
                    # Try 24-hour format
                    time_obj = datetime.strptime(row['start_time'], '%H:%M').time()
                
                time_objs.append((idx, time_obj))
            
            # Sort by the extracted time objects
            sorted_indices = [idx for idx, _ in sorted(time_objs, key=lambda x: x[1])]
            schedule_df = schedule_df.iloc[sorted_indices].reset_index(drop=True)
        except Exception as e:
            st.error(f"Error sorting schedule: {e}")
        
        # Use columns to create a responsive grid layout
        total_subjects = len(schedule_df)
        cols_per_row = 3 if total_subjects > 2 else 2
        rows = math.ceil(total_subjects / cols_per_row)
        
        # CSS for consistent spacing between rows
        st.markdown("""
        <style>
        .class-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            grid-gap: 15px;  /* Consistent spacing between cards */
            margin-bottom: 15px;
        }
        .class-card {
            height: 100%;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Start a grid container using HTML/CSS
        st.markdown('<div class="class-grid">', unsafe_allow_html=True)
        
        # Create all class cards and add them to the grid
        for subject_idx in range(total_subjects):
            subject_row = schedule_df.iloc[subject_idx]
            subject = subject_row['subject']
            subject_type = subject_row['type']
            start_time = subject_row['start_time']
            end_time = subject_row['end_time']
            
            # Parse times correctly, handling both formats
            try:
                # Try AM/PM format
                start_time_obj = datetime.strptime(start_time, '%I:%M %p').time()
                end_time_obj = datetime.strptime(end_time, '%I:%M %p').time()
            except ValueError:
                try:
                    # Try 24-hour format
                    start_time_obj = datetime.strptime(start_time, '%H:%M').time()
                    end_time_obj = datetime.strptime(end_time, '%H:%M').time()
                except ValueError:
                    # Handle any other format issues
                    continue
            
            is_current = current_time_obj >= start_time_obj and current_time_obj < end_time_obj
            is_past = current_time_obj >= end_time_obj
            is_upcoming = current_time_obj < start_time_obj
            
            # Status for display
            if is_past:
                time_status = "Class ended"
                time_color = "#757575"  # Gray
            elif is_current:
                time_status = "CLASS IN PROGRESS"
                time_color = "#FF9800"  # Orange
            else:
                time_status = f"Starts in {get_time_until(start_time_obj)}"
                time_color = "#2196F3"  # Blue
            
            # Check if student attended
            attended = check_attendance_for_subject(student_name, date_str, subject)
            show_attendance = is_current or is_past
            
            # Create a unique ID for this card
            card_id = f"card_{subject_idx}"
            
            # Generate the card HTML with embedded JavaScript
            card_html = get_dynamic_time_card_html(
                subject, 
                subject_type, 
                start_time, 
                end_time, 
                is_current, 
                is_past, 
                attended, 
                show_attendance, 
                time_status, 
                time_color, 
                card_id
            )
            
            # Add the card to the grid using html component for proper JS execution
            card_height = 220 if is_current else 200 if is_past else 180
            html(card_html, height=card_height)

        # Close the grid container
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Summary metrics - removing the camera detection metric
        st.subheader("📊 Today's Attendance Summary")
        attended_count = 0
        total_classes = 0
        
        # Count all classes for today, prioritizing manual attendance entries
        for _, row in schedule_df.iterrows():
            start_time = row['start_time']
            subject_name = row['subject']
            
            try:
                # Try AM/PM format
                start_time_obj = datetime.strptime(start_time, '%I:%M %p').time()
            except ValueError:
                try:
                    # Try 24-hour format
                    start_time_obj = datetime.strptime(start_time, '%H:%M').time()
                except ValueError:
                    # Skip if time format is invalid
                    continue
            
            # Check if there's an attendance record for this subject (manual entry by teacher)
            attendance_check = check_attendance_for_subject(student_name, date_str, subject_name)
            
            # If there's an attendance record OR the class has started, count it
            if attendance_check or current_time_obj >= start_time_obj:
                total_classes += 1
                if attendance_check:
                    attended_count += 1
        
        attendance_rate = 0 if total_classes == 0 else (attended_count / total_classes) * 100
        
        # Create a more visually appealing metrics section with progress bars
        metric_col1, metric_col2 = st.columns(2)
        
        with metric_col1:
            st.markdown("### Classes Overview")
            
            # Display classes metrics
            class_cols = st.columns(3)
            with class_cols[0]:
                st.metric("Total Classes", len(schedule_df))
            with class_cols[1]:
                st.metric("Available", total_classes)
            with class_cols[2]:
                st.metric("Attended", attended_count, delta=f"{attendance_rate:.1f}%" if total_classes > 0 else None)
            
            # Create a progress bar showing attendance progress
            remaining_classes = len(schedule_df) - total_classes
            
            st.markdown("#### Today's Progress")
            progress_html = f"""
            <div style="display: flex; align-items: center; gap: 10px; margin: 10px 0;">
                <div style="flex-grow: 1; height: 20px; background-color: #eee; border-radius: 10px; overflow: hidden;">
                    <div style="width: {attended_count/len(schedule_df)*100}%; height: 100%; background-color: #4CAF50;"></div>
                </div>
                <div style="width: 80px; text-align: right;">
                    <span style="font-weight: bold;">{attended_count}/{len(schedule_df)}</span>
                </div>
            </div>
            """
            st.markdown(progress_html, unsafe_allow_html=True)
            
            # Add progress status
            if total_classes == 0:
                st.info("No classes have started yet today.")
            elif attended_count == total_classes:
                st.success("✅ You've attended all classes so far today!")
            elif attended_count == 0:
                st.error("⚠️ You haven't attended any classes today.")
            else:
                st.warning(f"You've attended {attended_count} out of {total_classes} classes so far today.")
            
            # Show upcoming classes reminder if any
            if remaining_classes > 0:
                st.info(f"📆 You have {remaining_classes} more {'class' if remaining_classes == 1 else 'classes'} today.")
        
        with metric_col2:
            # Add attendance rate gauge chart
            st.markdown("### Today's Attendance Rate")
            
            # Create gauge chart for attendance rate
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=attendance_rate,
                title={'text': "Attendance Rate"},
                domain={'x': [0, 1], 'y': [0, 1]},
                gauge={
                    'axis': {'range': [0, 100], 'tickwidth': 1},
                    'bar': {'color': "#1E88E5"},
                    'steps': [
                        {'range': [0, 60], 'color': "#EF5350"},
                        {'range': [60, 80], 'color': "#FFCA28"},
                        {'range': [80, 100], 'color': "#66BB6A"}
                    ],
                    'threshold': {
                        'line': {'color': "black", 'width': 4},
                        'thickness': 0.75,
                        'value': 80
                    }
                }
            ))
            
            fig.update_layout(
                height=250,
                margin=dict(l=20, r=20, t=50, b=20),
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    # The following sections should now ALWAYS show, even if there are no classes today
    
    # Add Attendance History Section
    st.header("📈 Attendance History & Analytics")
    
    # Get extended attendance history data
    history_df = get_extended_attendance_history(student_name, days=30)
    
    # Create visualizations
    weekly_chart, day_pattern_chart, recent_chart = create_attendance_history_dashboards(history_df)
    
    # Display analytics in tabs
    tab1, tab2, tab3, tab4 = st.tabs(["Recent Trends", "Weekly Stats", "Day Patterns", "Subject Patterns"])
    
    with tab1:
        st.plotly_chart(recent_chart, use_container_width=True)
        
        # Calculate overall attendance stats
        total_attended = history_df['attended_classes'].sum()
        total_scheduled = history_df['total_classes'].sum()
        overall_rate = (total_attended / total_scheduled * 100) if total_scheduled > 0 else 0
        
        st.markdown(f"**Overall Attendance:** {overall_rate:.1f}% ({total_attended} out of {total_scheduled} classes)")
        
        # Recent streak calculation - consecutive days with perfect attendance
        # Identify dates with classes
        dates_with_classes = history_df[history_df['total_classes'] > 0].copy()
        if not dates_with_classes.empty:
            dates_with_classes['perfect_day'] = dates_with_classes['attended_classes'] == dates_with_classes['total_classes']
            
            # Calculate current streak
            current_streak = 0
            for perfect in reversed(dates_with_classes['perfect_day'].tolist()):
                if (perfect):
                    current_streak += 1
                else:
                    break
            
            if current_streak > 0:
                st.success(f"🔥 Current streak: {current_streak} {'day' if current_streak == 1 else 'days'} of perfect attendance!")
    
    with tab2:
        st.plotly_chart(weekly_chart, use_container_width=True)
        
        # Add weekly stats summary
        weekly_stats = history_df.groupby('week').agg({
            'attended_classes': 'sum',
            'total_classes': 'sum',
            'attendance_rate': 'mean'
        }).reset_index()
        
        best_week = weekly_stats.loc[weekly_stats['attendance_rate'].idxmax()]
        worst_week = weekly_stats.loc[weekly_stats['attendance_rate'].idxmin()]
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Best Week", f"Week {int(best_week['week'])}", f"{best_week['attendance_rate']:.1f}%")
        with col2:
            st.metric("Worst Week", f"Week {int(worst_week['week'])}", f"{worst_week['attendance_rate']:.1f}%")
    
    with tab3:
        st.plotly_chart(day_pattern_chart, use_container_width=True)
        
        # Find best and worst days
        day_stats = history_df.groupby(['day_of_week', 'day_name']).agg({
            'attended_classes': 'sum',
            'total_classes': 'sum'
        }).reset_index()
        
        day_stats['attendance_rate'] = day_stats.apply(
            lambda row: (row['attended_classes'] / row['total_classes'] * 100) if row['total_classes'] > 0 else 0, 
            axis=1
        )
        
        day_stats = day_stats[day_stats['total_classes'] > 0]
        
        if not day_stats.empty:
            best_day = day_stats.loc[day_stats['attendance_rate'].idxmax()]
            worst_day = day_stats.loc[day_stats['attendance_rate'].idxmin()]
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Best Day", best_day['day_name'], f"{best_day['attendance_rate']:.1f}%")
            with col2:
                st.metric("Worst Day", worst_day['day_name'], f"{worst_day['attendance_rate']:.1f}%")
            
            # Attendance tip based on pattern
            if worst_day['attendance_rate'] < 70:
                st.warning(f"⚠️ Your attendance on {worst_day['day_name']} needs improvement. Consider setting an earlier alarm or adjusting your schedule.")
    
    with tab4:
        try:
            # Only keep the subject bar chart, remove heatmap and trend chart
            st.plotly_chart(create_subject_bar_chart(history_df), use_container_width=True)
            
            # Show top/bottom subjects based on attendance if subject data exists
            if 'subject' in history_df.columns:
                subject_stats = history_df.groupby('subject').agg({
                    'attended_classes': 'sum',
                    'total_classes': 'sum'
                }).reset_index()
                
                subject_stats['attendance_rate'] = (subject_stats['attended_classes'] / subject_stats['total_classes'] * 100).fillna(0)
                subject_stats = subject_stats.sort_values('attendance_rate', ascending=False)
                
                # Show top and bottom subjects in columns
                if len(subject_stats) > 1:
                    st.subheader("Subject Rankings")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("#### Best Attendance")
                        best_subject = subject_stats.iloc[0]
                        st.metric(
                            best_subject['subject'], 
                            f"{best_subject['attendance_rate']:.1f}%",
                            f"{best_subject['attended_classes']} of {best_subject['total_classes']} classes"
                        )
                    
                    with col2:
                        st.markdown("#### Needs Improvement")
                        worst_subject = subject_stats.iloc[-1]
                        st.metric(
                            worst_subject['subject'], 
                            f"{worst_subject['attendance_rate']:.1f}%",
                            f"{worst_subject['attended_classes']} of {worst_subject['total_classes']} classes"
                        )
                elif len(subject_stats) == 1:
                    # Only one subject
                    st.subheader("Subject Performance")
                    subject = subject_stats.iloc[0]
                    st.metric(
                        subject['subject'], 
                        f"{subject['attendance_rate']:.1f}%",
                        f"{subject['attended_classes']} of {subject['total_classes']} classes"
                    )
                else:
                    st.info("No subject attendance data available yet.")
            else:
                st.info("No subject attendance data available. Please check your database configuration.")
        except Exception as e:
            st.error(f"Error displaying subject patterns: {str(e)}")
            st.info("This might happen if there are no attendance records yet or if your database schema is incomplete.")

# Fix the syntax error in the create_attendance_tables function

def create_attendance_tables():
    """
    Create the class_attendance table if it doesn't exist
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # DISABLED: Legacy table creation - using enhanced tables only
        # Create class_attendance table if it doesn't exist
        # cursor.execute("""
        # CREATE TABLE IF NOT EXISTS class_attendance (
        #     id INTEGER PRIMARY KEY AUTOINCREMENT,
        #     student_name TEXT NOT NULL,
        #     class_date DATE NOT NULL,
        #     subject TEXT NOT NULL,
        #     start_time TEXT NOT NULL,
        #     end_time TEXT NOT NULL,
        #     attended BOOLEAN NOT NULL DEFAULT 0,
        #     UNIQUE(student_name, class_date, subject, start_time)
        # )
        # """)
        
        # conn.commit()
        print("DISABLED: Legacy table creation - using enhanced tables only")
        
        # DISABLED: Legacy table operations
        # Check if the table was just created (no data yet)
        # execute_query("SELECT COUNT(*) FROM class_attendance")
        # count = cursor.fetchone()[0]
        
        # if count == 0:
        #     print("Populating class_attendance from existing data")
        #     # Optionally populate the table with data from attendance_records and class_schedules
        #     try:
        #         cursor.execute("""
        #         -- First get all scheduled classes for each day
        #         WITH scheduled_classes AS (
        #             SELECT 
        #                 s.subject,
        #                 s.start_time,
        #                 s.end_time,
        #                 s.day,
        #                 date(a.timestamp) as class_date,
        #                 a.name as student_name
        #             FROM class_schedules s,
        #                 (SELECT DISTINCT name, date(timestamp) as timestamp FROM attendance_records) a
        #             WHERE 
        #                 strftime('%A', a.timestamp) = s.day
        #         )
        #         
        #         -- Now insert records for each scheduled class, marking as attended if there's a matching log
        #         INSERT OR IGNORE INTO class_attendance 
        #             (student_name, class_date, subject, start_time, end_time, attended)
        #         SELECT 
        #             c.student_name,
        #             c.class_date,
        #             c.subject,
        #             c.start_time,
        #             c.end_time,
        #             EXISTS (
        #                 SELECT 1 FROM attendance_records a 
        #                 WHERE a.name = c.student_name 
        #                 AND date(a.timestamp) = c.class_date
        #                 AND time(a.timestamp) BETWEEN time(c.start_time) AND time(c.end_time)
        #             ) as attended
        #         FROM scheduled_classes c
        #         """)
        #         conn.commit()
        #         print("Populated class_attendance table with existing data")
        #     except Exception as e:
        #         print(f"Could not populate class_attendance: {e}")
    except Exception as e:
        print(f"Error in legacy table operations (disabled): {e}")
    finally:
        conn.close()

# DISABLED: Legacy table creation
# Call the table creation function when the module is imported
# create_attendance_tables()

def get_student_details(student_name):
    """Get student details including section information"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Query the student_profiles table for details
    # Note: Using the new table name after database optimization
    cursor.execute("""
    SELECT section
    FROM student_profiles
    WHERE name = ?
    """, (student_name,))
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {
            'section': result[0] if result[0] else 'Unassigned'
        }
    return {'section': 'Unassigned'}

# Add this function to securely load student data
def get_secure_student_data():
    """Get student data for the currently logged-in user only"""
    current_user = st.session_state.get('username')
    
    # If no user is logged in, return empty data
    if not current_user:
        st.error("No user logged in")
        st.stop()
        return None
        
    # Get student details from database using enhanced tables
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get student data from users_enhanced and students_enhanced tables
        query = """
            SELECT s.name, s.roll_number, s.department, s.section, s.year
            FROM users_enhanced u
            JOIN students_enhanced s ON u.linked_id = s.student_id
            WHERE u.username = ? AND u.role = 'student'
        """
        
        cursor.execute(query, (current_user,))
        result = cursor.fetchone()
        
        if result:
            student_data = {
                'student_name': result[0],
                'student_id': result[1] or 'Unknown',
                'section': result[3] or 'Unknown',
                'department': result[2] or 'Unknown',
                'year': result[4] or 'Unknown'
            }
            return student_data
        else:
            # Fallback if no proper record found
            fallback_data = {
                'student_name': current_user,
                'student_id': 'Unknown',
                'section': 'Unknown',
                'department': 'Unknown',
                'year': 'Unknown'
            }
            return fallback_data
            
    except Exception as e:
        st.error(f"Error getting student data: {e}")
        error_data = {
            'student_name': current_user,
            'student_id': 'Unknown',
            'section': 'Unknown',
            'department': 'Unknown',
            'year': 'Unknown'
        }
        return error_data
    finally:
        conn.close()

if __name__ == "__main__":
    show_student_report()
    create_attendance_tables()