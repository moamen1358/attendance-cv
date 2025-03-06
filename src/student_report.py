import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import time
import random
import math
from streamlit.components.v1 import html

# Page configuration
st.set_page_config(
    page_title="Student Attendance",
    page_icon="📚",
    layout="wide",
)

# Constants
DATABASE_PATH = 'attendance_system.db'
AUTO_REFRESH_INTERVAL = 30  # seconds

# Custom CSS
st.markdown("""
<style>
.class-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    grid-gap: 0px;  /* Reduced gap between cards */
    margin-bottom: 15px;
}
.class-card {
    height: 100%;
    transition: transform 0.2s ease;
}
.class-card:hover {
    transform: translateY(-3px);
}
</style>
""", unsafe_allow_html=True)

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
    conn = get_db_connection()
    
    if date:
        # Format for SQLite date filtering
        date_start = f"{date} 00:00:00"
        date_end = f"{date} 23:59:59"
        
        query = """
        SELECT * 
        FROM attendance_log 
        WHERE name = ? AND timestamp BETWEEN ? AND ?
        ORDER BY timestamp DESC
        """
        df = pd.read_sql(query, conn, params=(student_name, date_start, date_end))
    else:
        query = """
        SELECT * 
        FROM attendance_log 
        WHERE name = ?
        ORDER BY timestamp DESC
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

def get_schedule_for_day(day_name):
    """
    Get the subject schedule for a specific day
    
    Args:
        day_name (str): Name of the day (e.g., 'Sunday', 'Monday')
    
    Returns:
        pandas.DataFrame: DataFrame containing schedule for the day
    """
    conn = get_db_connection()
    query = """
    SELECT subject, type, start_time, end_time 
    FROM control_4 
    WHERE day = ? AND subject != ''
    ORDER BY start_time
    """
    df = pd.read_sql_query(query, conn, params=(day_name,))
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
    FROM attendance_log
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
    
    Args:
        student_name (str): Name of the student
        date (str): Date in format 'YYYY-MM-DD'
        start_time (str): Class start time (e.g., '9:00 AM')
        end_time (str): Class end time (e.g., '11:00 AM')
    
    Returns:
        bool: True if student attended, False otherwise
    """
    conn = get_db_connection()
    
    # Convert AM/PM time to 24-hour format for database comparison
    try:
        start_dt_obj = datetime.strptime(start_time, '%I:%M %p')
        start_time_24h = start_dt_obj.strftime('%H:%M')
        
        end_dt_obj = datetime.strptime(end_time, '%I:%M %p')
        end_time_24h = end_dt_obj.strftime('%H:%M')
    except ValueError:
        # If already in 24-hour format, use as is
        start_time_24h = start_time
        end_time_24h = end_time
    
    # Format for SQLite date filtering - add seconds for exact comparison
    date_start = f"{date} {start_time_24h}:00"
    date_end = f"{date} {end_time_24h}:59"
    
    query = """
    SELECT COUNT(*) as count 
    FROM attendance_log 
    WHERE name = ? AND timestamp BETWEEN ? AND ?
    """
    
    result = pd.read_sql(query, conn, params=(student_name, date_start, date_end))
    conn.close()
    
    return result['count'].iloc[0] > 0

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
    FROM attendance_log
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
        start_time = row['start_time']
        end_time = row['end_time']
        
        # Convert AM/PM times to datetime for plotting
        try:
            start_dt = datetime.strptime(f"2023-01-01 {start_time}", "%Y-%m-%d %I:%M %p")
            end_dt = datetime.strptime(f"2023-01-01 {end_time}", "%Y-%m-%d %I:%M %p")
            
            # Also create time objects for comparison
            start_time_obj = datetime.strptime(start_time, '%I:%M %p').time()
            end_time_obj = datetime.strptime(end_time, '%I:%M %p').time()
        except ValueError:
            # If already in 24-hour format
            start_dt = datetime.strptime(f"2023-01-01 {start_time}", "%Y-%m-%d %H:%M")
            end_dt = datetime.strptime(f"2023-01-01 {end_time}", "%Y-%m-%d %H:%M")
            
            # Also create time objects for comparison
            start_time_obj = datetime.strptime(start_time, '%H:%M').time()
            end_time_obj = datetime.strptime(end_time, '%H:%M').time()
        
        # Check attendance
        attended = check_attendance(student_name, date_str, start_time, end_time)
        
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

def real_time_clock():
    """Display a real-time clock that updates every second using JavaScript"""
    clock_html = """
    <div id="real_time_clock" style="font-size:1.2rem; font-weight:bold; color:#555; margin:10px 0;">
        <span id="clock"></span>
    </div>

    <script>
    function updateClock() {
        const now = new Date();
        let hours = now.getHours();
        const minutes = now.getMinutes().toString().padStart(2, '0');
        const seconds = now.getSeconds().toString().padStart(2, '0');
        let ampm = hours >= 12 ? 'PM' : 'AM';
        
        // Convert to 12-hour format
        hours = hours % 12;
        hours = hours ? hours : 12; // the hour '0' should be '12'
        
        // Display the time
        document.getElementById('clock').textContent = 
            hours + ':' + minutes + ':' + seconds + ' ' + ampm;
        
        // Call this function again in 1000ms (1 second)
        setTimeout(updateClock, 1000);
    }
    
    // Start the clock when the page loads
    updateClock();
    </script>
    """
    return html(clock_html, height=40)

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

def show_student_report():
    """Display the advanced student attendance report page"""
    # Initialize session state for auto-refresh
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = datetime.now()
        st.session_state.is_refreshing = False
    
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
    
    # Get student name
    username = st.session_state.username
    student_name = username  # Simplified for now
    
    # Get current date and time
    today = datetime.now().date()
    date_str = today.strftime('%Y-%m-%d')
    day_name = today.strftime('%A')
    current_time_obj = datetime.now().time()
    
    # Create header with auto-refresh info and real-time clock
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("📚 My Attendance Dashboard")
    with col2:
        # Add real-time clock
        real_time_clock()
        
        # Auto-refresh mechanism (keep this for page reloads)
        time_since_refresh = (datetime.now() - st.session_state.last_refresh).seconds
        next_refresh = max(0, AUTO_REFRESH_INTERVAL - time_since_refresh)
        
        if time_since_refresh >= AUTO_REFRESH_INTERVAL:
            st.session_state.last_refresh = datetime.now()
            st.session_state.is_refreshing = True
            st.rerun()
        
        st.caption(f"Auto-refresh in: {next_refresh}s • Last full update: {st.session_state.last_refresh.strftime('%H:%M:%S')}")

    # Get schedule for today
    schedule_df = get_schedule_for_day(day_name)
    
    # Create tabs
    tab1, tab2 = st.tabs(["📋 Today's Schedule", "📊 Attendance Analytics"])
    
    with tab1:
        if schedule_df.empty:
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
                
                # Count past classes (classes that have already ended)
                if current_time_obj >= end_time_obj:
                    past_classes += 1
                    if check_attendance(student_name, date_str, row['start_time'], row['end_time']):
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
                    # Student attended all classes today
                    welcome_message = welcome_countdown_html(student_name, attended_all=True)
                elif past_classes > 0:
                    # Some classes were missed
                    missed = past_classes - attended_past_classes
                    welcome_message = welcome_countdown_html(student_name, missed_count=missed)
                else:
                    # No classes were scheduled for today
                    welcome_message = welcome_countdown_html(student_name, no_classes=True)
            else:
                # There's an upcoming class - prepare it as a dictionary for the welcome_countdown_html function
                next_class_dict = {
                    'subject': next_class['subject'],
                    'start_time': next_class['start_time']
                }
                
                if past_classes > 0 and attended_past_classes < past_classes:
                    # Student missed some earlier classes
                    missed = past_classes - attended_past_classes
                    welcome_message = welcome_countdown_html(student_name, next_class_dict, missed_count=missed)
                else:
                    # Student has attended all previous classes (or there were none)
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
                attended = check_attendance(student_name, date_str, start_time, end_time)
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
            
            # Summary metrics
            st.subheader("📊 Today's Attendance Summary")
            attended_count = 0
            total_classes = 0
            
            # Only count classes that have already started
            for _, row in schedule_df.iterrows():
                start_time = row['start_time']
                
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
                
                if current_time_obj >= start_time_obj:
                    total_classes += 1
                    if check_attendance(student_name, date_str, row['start_time'], row['end_time']):
                        attended_count += 1
            
            attendance_rate = 0 if total_classes == 0 else (attended_count / total_classes) * 100
            
            # Metrics with color-coded delta indicators
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Classes Today", len(schedule_df))
            with col2:
                st.metric("Classes So Far", total_classes)
            with col3:
                st.metric("Attended", attended_count, delta=f"{attendance_rate:.1f}%" if total_classes > 0 else None)
            with col4:
                # Get today's detections
                today_df = get_student_attendance(student_name, date_str)
                detection_count = len(today_df)
                st.metric("Camera Detections", detection_count)
    
    with tab2:
        # Analytics section with charts and insights
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Today's Attendance By Hour")
            # Get hourly attendance data
            hourly_df = get_attendance_count_by_hour(student_name, date_str)
            hourly_fig = create_hourly_attendance_chart(hourly_df)
            st.plotly_chart(hourly_fig, use_container_width=True)
        
        with col2:
            st.subheader("📈 Weekly Attendance History")
            # Get attendance history
            history_df = get_attendance_history(student_name, days=7)
            history_fig = create_attendance_history_chart(history_df)
            st.plotly_chart(history_fig, use_container_width=True)
        
        # Add a weekly summary section
        st.subheader("📅 Weekly Attendance Analysis")
        history_expanded = get_attendance_history(student_name, days=14)  # Get 2 weeks
        
        # Calculate some statistics
        total_detections = history_expanded['detection_count'].sum()
        avg_detections = history_expanded['detection_count'].mean()
        total_days_present = history_expanded[history_expanded['detection_count'] > 0].shape[0]
        streak = 0
        
        # Find current streak
        sorted_df = history_expanded.sort_values('date', ascending=False)
        for _, row in sorted_df.iterrows():
            if (row['detection_count'] > 0):
                streak += 1
            else:
                break
        
        # Create metrics for the weekly summary
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Detections", int(total_detections))
        with col2:
            st.metric("Avg. Daily Detections", f"{avg_detections:.1f}")
        with col3:
            st.metric("Days Present", f"{total_days_present}/{len(history_expanded)}")
        with col4:
            st.metric("Current Streak", f"{streak} days")
        
        # Show detailed detection records
        st.subheader("📷 Recent Camera Detection Records")
        attendance_df = get_student_attendance(student_name, date_str)
        
        if attendance_df.empty:
            st.warning("No camera detections for today. Make sure to face the camera clearly.")
        else:
            # Format and display the data
            attendance_df = attendance_df.sort_values('timestamp', ascending=False)
            
            # Create a display dataframe
            display_df = pd.DataFrame()
            display_df['Time'] = attendance_df['time']
            
            # Add confidence column if it exists
            if 'confidence' in attendance_df.columns:
                display_df['Confidence'] = attendance_df['confidence']
            
            # Add device_id column if it exists
            if 'device_id' in attendance_df.columns:
                display_df['Location'] = attendance_df['device_id']
            
            # Configure column display
            column_config = {
                "Time": st.column_config.Column(
                    "Detection Time",
                    width="medium"
                )
            }
            
            if 'Confidence' in display_df.columns:
                display_df['Confidence'] = display_df['Confidence'].fillna(0).astype(float)
                column_config["Confidence"] = st.column_config.ProgressColumn(
                    "Confidence",
                    format="%.2f",
                    min_value=0,
                    max_value=1
                )
            
            if 'Location' in display_df.columns:
                column_config["Location"] = st.column_config.Column(
                    "Camera Location",
                    width="medium"
                )
            
            # Show in a nice table
            st.dataframe(
                display_df,
                column_config=column_config,
                hide_index=True,
                use_container_width=True
            )
            
            # Add current time refresh indicator
            current_time = datetime.now().strftime('%I:%M:%S %p')
            st.caption(f"Last updated: {current_time} • {len(attendance_df)} records found today")
    
    # Clear the refreshing flag
    if st.session_state.is_refreshing:
        st.session_state.is_refreshing = False

if __name__ == "__main__":
    show_student_report()