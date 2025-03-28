import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sqlite3
from database_utils import execute_query, execute_query_df

def create_attendance_sunburst(student_name, start_date=None, end_date=None):
    """
    Create a sunburst chart showing attendance by subject and day
    
    Args:
        student_name (str): Name of the student
        start_date (str): Start date in format YYYY-MM-DD
        end_date (str): End date in format YYYY-MM-DD
        
    Returns:
        plotly.graph_objects.Figure: Sunburst chart
    """
    # Connect to database
    conn = sqlite3.connect('attendance_system.db')
    
    # Build query
    query = """
    SELECT 
        ca.subject,
        strftime('%w', ca.class_date) as day_num,
        CASE strftime('%w', ca.class_date)
            WHEN '0' THEN 'Sun'
            WHEN '1' THEN 'Mon'
            WHEN '2' THEN 'Tue'
            WHEN '3' THEN 'Wed'
            WHEN '4' THEN 'Thu'
            WHEN '5' THEN 'Fri'
            WHEN '6' THEN 'Sat'
        END as day_name,
        SUM(ca.attended) as attended_count,
        COUNT(*) as total_count
    FROM class_attendance ca
    WHERE ca.student_name = ?
    """
    
    params = [student_name]
    if start_date:
        query += " AND ca.class_date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND ca.class_date <= ?"
        params.append(end_date)
        
    query += """
    GROUP BY ca.subject, day_num, day_name
    ORDER BY day_num, ca.subject
    """
    
    # Execute query
    df = execute_query_df(query, params)
    conn.close()
    
    if df.empty:
        # Return empty figure if no data
        fig = go.Figure()
        fig.update_layout(title="No attendance data available")
        return fig
    
    # Calculate attendance rate
    df['attendance_rate'] = (df['attended_count'] / df['total_count'] * 100).round(1)
    
    # Define color scale based on attendance rate
    df['color'] = df['attendance_rate'].apply(
        lambda x: f"hsl({min(120, x * 1.2)}, 70%, 50%)"  # 0-100% maps to red-yellow-green
    )
    
    # Create labels for the sunburst
    df['subject_label'] = df['subject'] + '<br>' + df['attendance_rate'].astype(str) + '%'
    df['day_subject'] = df['day_name'] + '-' + df['subject']
    
    # Create sunburst chart
    fig = px.sunburst(
        df,
        path=['day_name', 'subject'],
        values='total_count',
        color='attendance_rate',
        color_continuous_scale='RdYlGn',
        range_color=[0, 100],
        hover_data=['attended_count', 'total_count', 'attendance_rate'],
        branchvalues='total',
    )
    
    # Update layout
    fig.update_layout(
        title={
            'text': "Attendance by Day and Subject",
            'font': {'size': 20}
        },
        coloraxis_colorbar=dict(
            title="Attendance<br>Rate (%)",
            tickvals=[0, 50, 100],
            ticktext=["0%", "50%", "100%"],
        ),
        margin=dict(t=60, l=0, r=0, b=0),
        height=500,
        paper_bgcolor="rgba(0,0,0,0)",  # Transparent background
        plot_bgcolor="rgba(0,0,0,0)"    # Transparent plot area
    )
    
    fig.update_traces(
        hovertemplate='<b>%{label}</b><br>Classes: %{customdata[1]}<br>Attended: %{customdata[0]}<br>Rate: %{color:.1f}%<extra></extra>'
    )
    
    return fig

def create_attendance_gauge(attendance_rate, title="Overall Attendance Rate"):
    """Create a beautiful gauge chart for attendance rate"""
    # Define color scale based on attendance rate
    if attendance_rate >= 90:
        color = "#4CAF50"  # Green
        threshold_color = "#43A047"
    elif attendance_rate >= 80:
        color = "#8BC34A"  # Light Green
        threshold_color = "#7CB342"
    elif attendance_rate >= 70:
        color = "#FFEB3B"  # Yellow
        threshold_color = "#FDD835"
    elif attendance_rate >= 60:
        color = "#FFC107"  # Amber
        threshold_color = "#FFB300"
    else:
        color = "#F44336"  # Red
        threshold_color = "#E53935"
    
    # Create gauge chart
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=attendance_rate,
        delta={"reference": 80, "increasing": {"color": "#4CAF50"}, "decreasing": {"color": "#F44336"}},
        gauge={
            "axis": {
                "range": [None, 100],
                "tickwidth": 1,
                "tickcolor": "darkgrey",
                "tickvals": [0, 20, 40, 60, 80, 100],
                "ticktext": ["0%", "20%", "40%", "60%", "80%", "100%"]
            },
            "bar": {"color": color},
            "bgcolor": "rgba(0,0,0,0)",  # Transparent background instead of white
            "borderwidth": 2,
            "bordercolor": "gray",
            "steps": [
                {"range": [0, 60], "color": "rgba(244, 67, 54, 0.3)"},  # Red
                {"range": [60, 70], "color": "rgba(255, 193, 7, 0.3)"},  # Amber
                {"range": [70, 80], "color": "rgba(255, 235, 59, 0.3)"},  # Yellow
                {"range": [80, 90], "color": "rgba(139, 195, 74, 0.3)"},  # Light Green
                {"range": [90, 100], "color": "rgba(76, 175, 80, 0.3)"}   # Green
            ],
            "threshold": {
                "line": {"color": threshold_color, "width": 4},
                "thickness": 0.75,
                "value": 80
            }
        }
    ))
    
    # Update layout
    fig.update_layout(
        title={
            'text': title,
            'y': 0.85,
            'x': 0.5,
            'font': {'size': 20}
        },
        paper_bgcolor="rgba(0,0,0,0)",  # Transparent background
        plot_bgcolor="rgba(0,0,0,0)",   # Transparent plot background
        font={"color": "darkgray", "family": "Arial"},
        height=300,
        margin=dict(l=30, r=30, b=30, t=80)
    )
    
    return fig

def create_weekly_heatmap(student_name, weeks=4, start_date=None):
    """
    Create a beautiful heatmap showing attendance over days of week across multiple weeks
    
    Args:
        student_name (str): Name of the student
        weeks (int): Number of weeks to show
        start_date (str, optional): Start date or None for most recent weeks
    
    Returns:
        plotly.graph_objects.Figure: Heatmap figure
    """
    # Connect to database
    conn = sqlite3.connect('attendance_system.db')
    
    # Calculate date range
    if start_date:
        start = datetime.strptime(start_date, '%Y-%m-%d').date()
    else:
        # Get the most recent class date for the student
        query = """
        SELECT MAX(class_date) FROM class_attendance
        WHERE student_name = ?
        """
        cursor = conn.cursor()
        execute_query(query, (student_name,))
        result = cursor.fetchone()
        if result is not None and result[0] is not None:
            max_date = result[0]
        else:
            max_date = datetime.now().date().strftime('%Y-%m-%d')
            print(f"No attendance records found for {student_name}, using current date")
        
        if max_date:
            start = datetime.strptime(max_date, '%Y-%m-%d').date()
            start = start - timedelta(days=start.weekday())  # Go back to Monday
        else:
            start = datetime.now().date() - timedelta(days=weeks*7)
    
    end_date = start + timedelta(days=weeks*7)
    
    # Query attendance data for the date range
    query = """
    SELECT 
        ca.class_date,
        strftime('%w', ca.class_date) as day_num,
        strftime('%W', ca.class_date) as week_num,
        SUM(ca.attended) as attended_count,
        COUNT(*) as total_count
    FROM class_attendance ca
    WHERE ca.student_name = ?
        AND ca.class_date >= ?
        AND ca.class_date <= ?
    GROUP BY ca.class_date
    ORDER BY ca.class_date
    """
    
    df = execute_query_df(query, (student_name, start.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
    conn.close()
    
    if df.empty:
        # Return empty figure if no data
        fig = go.Figure()
        fig.update_layout(title="No attendance data available for the selected period")
        return fig
    
    # Calculate attendance rate
    df['attendance_rate'] = (df['attended_count'] / df['total_count'] * 100).round(1)
    
    # Convert date strings to datetime
    df['date'] = pd.to_datetime(df['class_date'])
    df['weekday'] = df['date'].dt.day_name()
    
    # FIX: Calculate relative week without using .dt on the result of subtraction
    # Calculate days since start date for each row, then divide by 7 to get week number
    df['days_since_start'] = (df['date'] - pd.Timestamp(start)).dt.days
    df['relative_week'] = (df['days_since_start'] // 7) + 1
    
    # Create a complete date grid with all dates in the range
    date_range = pd.date_range(start=start, end=end_date - timedelta(days=1))
    date_df = pd.DataFrame({
        'date': date_range,
    })
    
    # Add weekday name explicitly and separately to avoid conflicts
    date_df['day_name'] = date_df['date'].dt.day_name()
    
    # Calculate relative week for date grid too
    date_df['days_since_start'] = (date_df['date'] - pd.Timestamp(start)).dt.days
    date_df['relative_week'] = (date_df['days_since_start'] // 7) + 1
    
    # Merge with attendance data - ensure we keep the day_name from date_df
    grid_df = pd.merge(date_df, df, on=['date'], how='left', suffixes=('', '_attendance'))
    
    # Ensure the weekday column exists after merge
    if 'day_name' not in grid_df.columns and 'weekday' not in grid_df.columns:
        # Recalculate day name if missing after merge
        grid_df['day_name'] = grid_df['date'].dt.day_name()
    
    # Fill NaN values with 0
    grid_df['attendance_rate'] = grid_df['attendance_rate'].fillna(0)
    grid_df['total_count'] = grid_df['total_count'].fillna(0)
    grid_df['attended_count'] = grid_df['attended_count'].fillna(0)
    
    # Create custom hover text with safe column access
    grid_df['hover_text'] = grid_df.apply(
        lambda row: f"Date: {row['date'].strftime('%Y-%m-%d')}<br>" +
                   f"Day: {row['day_name'] if 'day_name' in row.index else row['date'].day_name()}<br>" +
                   (f"Classes: {int(row['attended_count']) if not pd.isna(row['attended_count']) else 0}/{int(row['total_count']) if not pd.isna(row['total_count']) else 0}<br>" +
                   f"Rate: {row['attendance_rate']}%" if row['total_count'] > 0 else "No classes"),
        axis=1
    )
    
    # Define layout for the heatmap
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    # Create week labels
    week_labels = []
    for w in range(1, weeks+1):
        week_start = start + timedelta(days=(w-1)*7)
        week_end = week_start + timedelta(days=6)
        week_labels.append(f"Week {w}<br>{week_start.strftime('%b %d')} - {week_end.strftime('%b %d')}")
    
    # Create heatmap with Plotly Express
    fig = px.imshow(
        grid_df.pivot_table(
            values='attendance_rate', 
            index='day_name',  # Updated from 'weekday' to 'day_name'
            columns='relative_week',
            aggfunc='mean'
        ).reindex(days),
        labels=dict(x="Week", y="Day", color="Attendance Rate"),
        x=week_labels,
        y=days,
        color_continuous_scale=[
            [0, "rgba(255, 255, 255, 0.5)"],  # Semi-transparent white for no classes
            [0.01, "rgba(244, 67, 54, 0.8)"],  # Red for 0%
            [0.6, "rgba(255, 193, 7, 0.8)"],   # Amber for 60%
            [0.8, "rgba(139, 195, 74, 0.8)"],  # Light green for 80%
            [1, "rgba(76, 175, 80, 0.8)"]      # Green for 100%
        ],
        range_color=[0, 100],
        aspect="auto",
        height=400
    )
    
    # Add hover text - use 'day_name' instead of 'weekday'
    hover_data = grid_df.pivot_table(
        values='hover_text', 
        index='day_name',  # Updated from 'weekday' to 'day_name'
        columns='relative_week',
        aggfunc='first'
    ).reindex(days)
    
    # Update traces with hover data
    fig.update_traces(
        hovertemplate="%{z}%<br>%{customdata}<extra></extra>",
        customdata=hover_data
    )
    
    # Add a more descriptive title
    fig.update_layout(
        title={
            'text': "Attendance Calendar",
            'y': 0.95,
            'x': 0.5,
            'font': {'size': 20}
        },
        coloraxis_colorbar=dict(
            title="Attendance<br>Rate (%)",
            tickvals=[0, 25, 50, 75, 100],
            ticktext=["0%", "25%", "50%", "75%", "100%"],
        ),
        margin=dict(t=80, l=50, r=30, b=50),
        paper_bgcolor="rgba(0,0,0,0)",  # Transparent background
        plot_bgcolor="rgba(0,0,0,0)"    # Transparent plot area
    )
    
    return fig

def create_subject_radial_chart(student_name, start_date=None, end_date=None, min_classes=2):
    """
    Create a beautiful radial bar chart showing attendance by subject
    
    Args:
        student_name (str): Name of the student
        start_date (str): Start date in format YYYY-MM-DD
        end_date (str): End date in format YYYY-MM-DD
        min_classes (int): Minimum number of classes to include subject
        
    Returns:
        plotly.graph_objects.Figure: Radial bar chart
    """
    # Connect to database
    conn = sqlite3.connect('attendance_system.db')
    
    # Build query
    query = """
    SELECT 
        ca.subject,
        SUM(ca.attended) as attended_count,
        COUNT(*) as total_count
    FROM class_attendance ca
    WHERE ca.student_name = ?
    """
    
    params = [student_name]
    if start_date:
        query += " AND ca.class_date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND ca.class_date <= ?"
        params.append(end_date)
        
    query += """
    GROUP BY ca.subject
    HAVING total_count >= ?
    ORDER BY attended_count * 1.0 / total_count DESC
    """
    params.append(min_classes)
    
    # Execute query
    df = execute_query_df(query, params)
    conn.close()
    
    if df.empty:
        # Return empty figure if no data
        fig = go.Figure()
        fig.update_layout(title="No attendance data available")
        return fig
    
    # Calculate attendance rate
    df['attendance_rate'] = (df['attended_count'] / df['total_count'] * 100).round(1)
    
    # Sort by attendance rate
    df = df.sort_values('attendance_rate', ascending=False)
    
    # Create radial bar chart
    fig = px.bar_polar(
        df, 
        r="attendance_rate",
        theta="subject",
        color="attendance_rate",
        color_continuous_scale='RdYlGn',  # Red to Yellow to Green
        range_color=[0, 100],
        template="plotly_white",
        hover_data=["attended_count", "total_count"]
    )
    
    # Update layout
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickvals=[0, 25, 50, 75, 100],
                ticktext=["0%", "25%", "50%", "75%", "100%"]
            ),
            bgcolor="rgba(0,0,0,0)"  # Transparent background for polar area
        ),
        title={
            'text': "Attendance by Subject",
            'y': 0.95,
            'x': 0.5,
            'font': {'size': 20}
        },
        showlegend=False,
        height=500,
        margin=dict(t=100, b=50),
        paper_bgcolor="rgba(0,0,0,0)",  # Transparent background
        plot_bgcolor="rgba(0,0,0,0)"    # Transparent plot area
    )
    
    # Update hover template
    fig.update_traces(
        hovertemplate='<b>%{theta}</b><br>Attendance: %{r:.1f}%<br>Classes: %{customdata[1]}<br>Attended: %{customdata[0]}<extra></extra>'
    )
    
    return fig