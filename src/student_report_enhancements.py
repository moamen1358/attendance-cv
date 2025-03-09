import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import calendar
import time
from streamlit.components.v1 import html
import math
import sqlite3
import base64
from pathlib import Path
import json

# Enhancement utility functions for the student report page

def get_db_connection():
    """Get a connection to the SQLite database"""
    return sqlite3.connect('attendance_system.db')

def export_data_as_csv(df, filename="attendance_data.csv"):
    """Generate a download link for a dataframe as CSV"""
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">Download CSV File</a>'
    return href

def export_data_as_excel(df, filename="attendance_data.xlsx"):
    """Generate a download link for a dataframe as Excel"""
    # Create a BytesIO object
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Attendance")
        # Add formatting
        workbook = writer.book
        worksheet = writer.sheets["Attendance"]
        header_format = workbook.add_format({"bold": True, "bg_color": "#D9EAD3", "border": 1})
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
    
    excel_data = excel_buffer.getvalue()
    b64 = base64.b64encode(excel_data).decode()
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}">Download Excel File</a>'
    return href

def create_attendance_heatmap(history_df):
    """Create attendance heatmap by day and hour"""
    # Create a DataFrame for the heatmap with attendance by day of week and hour
    pivot_df = pd.pivot_table(
        history_df,
        values="attendance_rate",
        index="day_name",
        columns="week",
        aggfunc="mean",
        fill_value=0
    )
    
    # Order days correctly
    days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    pivot_df = pivot_df.reindex(days_order)
    
    # Create heatmap
    fig = px.imshow(
        pivot_df,
        text_auto=".1f",
        labels=dict(x="Week", y="Day", color="Attendance %"),
        x=[f"Week {w}" for w in pivot_df.columns],
        y=pivot_df.index,
        color_continuous_scale="RdYlGn",
        range_color=[0, 100],
        aspect="auto"
    )
    
    fig.update_layout(
        title="Attendance Heatmap by Day and Week",
        height=350,
        coloraxis_colorbar=dict(
            title="Attendance %",
            ticksuffix="%"
        ),
        margin=dict(l=10, r=10, t=40, b=10)
    )
    
    return fig

def create_attendance_calendar(history_df):
    """Create interactive calendar visualization for attendance"""
    # Get min and max dates for proper display
    history_df['date_obj'] = pd.to_datetime(history_df['date'])
    min_date = history_df['date_obj'].min()
    max_date = history_df['date_obj'].max()
    
    # Calculate month range
    months = []
    current_date = min_date.replace(day=1)
    while current_date <= max_date:
        months.append(current_date)
        # Move to next month
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year+1, month=1)
        else:
            current_date = current_date.replace(month=current_date.month+1)
    
    calendar_plots = []
    
    # Create calendar for each month
    for month_date in months:
        month_name = month_date.strftime("%B %Y")
        month_num = month_date.month
        year = month_date.year
        
        # Get number of days in the month
        num_days = calendar.monthrange(year, month_num)[1]
        
        # Create day labels and positions
        days = list(range(1, num_days + 1))
        
        # Get first day of week (0 = Monday, 6 = Sunday in our case)
        first_day = datetime(year, month_num, 1).weekday()
        
        # Create week positions
        weeks = [math.floor((first_day + d - 1) / 7) for d in range(1, num_days + 1)]
        max_weeks = max(weeks) + 1
        
        # Create day positions within week
        day_pos = [(first_day + d - 1) % 7 for d in range(1, num_days + 1)]
        
        # Create dates for merging
        dates = [f"{year}-{month_num:02d}-{d:02d}" for d in days]
        
        # Create base dataframe for the month
        month_df = pd.DataFrame({
            "day": days,
            "week": weeks, 
            "day_pos": day_pos,
            "date": dates
        })
        
        # Merge with actual attendance data
        month_df = pd.merge(month_df, history_df[['date', 'attendance_rate']], on='date', how='left')
        month_df['attendance_rate'] = month_df['attendance_rate'].fillna(0)
        
        # Create hover text
        month_df['text'] = month_df.apply(
            lambda row: f"Date: {row['date']}<br>Attendance: {row['attendance_rate']:.1f}%" 
            if pd.notnull(row['attendance_rate']) else f"Date: {row['date']}<br>No classes", 
            axis=1
        )
        
        # Create the heatmap
        fig = go.Figure()
        
        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        
        # Add colored blocks for attendance rate
        fig.add_trace(go.Heatmap(
            z=month_df['attendance_rate'],
            x=month_df['day_pos'],
            y=month_df['week'],
            text=month_df['text'],
            hoverinfo="text",
            colorscale='RdYlGn',
            showscale=False,
            zmin=0,
            zmax=100
        ))
        
        # Add day numbers as text
        fig.add_trace(go.Scatter(
            x=month_df['day_pos'],
            y=month_df['week'],
            text=month_df['day'].astype(str),
            mode='text',
            hoverinfo='skip',
            textfont=dict(
                color='black',
                size=12
            ),
            showlegend=False
        ))
        
        # Set layout
        fig.update_layout(
            title=month_name,
            height=200 + (50 * max_weeks),
            width=350,
            xaxis=dict(
                tickvals=list(range(7)),
                ticktext=day_names,
                side='top',
                showgrid=False
            ),
            yaxis=dict(
                showticklabels=False,
                showgrid=False
            ),
            plot_bgcolor='rgba(255,255,255,0.8)',
            margin=dict(l=10, r=10, t=40, b=10)
        )
        
        calendar_plots.append(fig)
    
    return calendar_plots

def create_course_breakdown_chart(student_name, date_range=30):
    """Create course-specific attendance breakdown"""
    conn = get_db_connection()
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=date_range)
    
    query = """
    SELECT 
        ca.subject,
        SUM(ca.attended) as attended_classes,
        COUNT(*) as total_classes,
        CASE 
            WHEN COUNT(*) > 0 THEN (SUM(ca.attended) * 100.0 / COUNT(*))
            ELSE 0
        END as attendance_rate
    FROM class_attendance ca
    WHERE ca.student_name = ? 
    AND ca.class_date BETWEEN ? AND ?
    GROUP BY ca.subject
    ORDER BY attendance_rate DESC
    """
    
    df = pd.read_sql_query(query, conn, params=(student_name, start_date, end_date))
    conn.close()
    
    if df.empty:
        return None
    
    # Create course breakdown chart
    fig = go.Figure()
    
    # Add bar for each course
    fig.add_trace(go.Bar(
        x=df['subject'],
        y=df['attendance_rate'],
        marker=dict(
            color=df['attendance_rate'],
            colorscale='RdYlGn',
            cmin=0,
            cmax=100
        ),
        text=[f"{r:.1f}%" for r in df['attendance_rate']],
        textposition='outside',
        hoverinfo='text',
        hovertext=[
            f"{subject}<br>Attended: {attended}/{total} classes<br>Rate: {rate:.1f}%" 
            for subject, attended, total, rate in zip(
                df['subject'], df['attended_classes'], df['total_classes'], df['attendance_rate']
            )
        ]
    ))
    
    # Add a line for target attendance (e.g., 80%)
    fig.add_shape(
        type="line",
        x0=-0.5,
        x1=len(df) - 0.5,
        y0=80,
        y1=80,
        line=dict(
            color="red",
            width=2,
            dash="dash",
        )
    )
    
    # Adjust layout
    fig.update_layout(
        title="Attendance by Course",
        xaxis_title="",
        yaxis=dict(
            title="Attendance %",
            range=[0, max(100, df['attendance_rate'].max() * 1.1)]
        ),
        height=400,
        margin=dict(l=10, r=10, t=50, b=110),
    )
    
    # Rotate x-axis labels for readability with long course names
    fig.update_xaxes(tickangle=45)
    
    return fig

def generate_achievements(student_name, history_df):
    """Generate achievement badges based on attendance patterns"""
    achievements = []
    
    # Calculate streaks
    streak_data = history_df[history_df['total_classes'] > 0].copy()
    if not streak_data.empty:
        streak_data['perfect_day'] = streak_data['attended_classes'] == streak_data['total_classes']
        
        # Calculate current streak
        current_streak = 0
        max_streak = 0
        for perfect in reversed(streak_data['perfect_day'].tolist()):
            if perfect:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0
        
        # Full attendance streaks
        if max_streak >= 5:
            achievements.append({
                "title": "Attendance Champion",
                "description": f"{max_streak} days perfect attendance streak!",
                "icon": "🏆",
                "color": "#FFD700"
            })
        elif max_streak >= 3:
            achievements.append({
                "title": "Consistency Award",
                "description": f"{max_streak} days perfect attendance streak!",
                "icon": "🌟",
                "color": "#C0C0C0"
            })
        
        # Overall attendance rate
        total_attended = streak_data['attended_classes'].sum()
        total_classes = streak_data['total_classes'].sum()
        
        if total_classes > 0:
            overall_rate = (total_attended / total_classes) * 100
            if overall_rate >= 95:
                achievements.append({
                    "title": "Perfect Attendance",
                    "description": f"{overall_rate:.1f}% overall attendance rate",
                    "icon": "🎯",
                    "color": "#4CAF50"
                })
            elif overall_rate >= 90:
                achievements.append({
                    "title": "Excellent Attendance",
                    "description": f"{overall_rate:.1f}% overall attendance rate",
                    "icon": "👏",
                    "color": "#8BC34A"
                })
        
        # Early bird award (check if student arrives early)
        conn = get_db_connection()
        query = """
        SELECT COUNT(*) as early_count
        FROM attendance_log al
        JOIN class_attendance ca ON ca.student_name = al.name 
                               AND date(al.timestamp) = ca.class_date
        WHERE al.name = ?
        AND time(al.timestamp) <= time(ca.start_time, '-10 minutes')
        AND date(al.timestamp) >= date('now', '-30 days')
        """
        result = conn.execute(query, (student_name,)).fetchone()
        conn.close()
        
        if result and result[0] >= 5:
            achievements.append({
                "title": "Early Bird",
                "description": f"Arrived early {result[0]} times in the last month",
                "icon": "🐦",
                "color": "#2196F3" 
            })
            
        # Improvement award
        if len(streak_data) >= 14:  # At least two weeks of data
            # Compare last week vs previous week
            recent_data = streak_data.tail(7)
            previous_data = streak_data.iloc[-14:-7]
            
            recent_rate = recent_data['attendance_rate'].mean()
            previous_rate = previous_data['attendance_rate'].mean()
            
            if recent_rate > previous_rate + 10:  # 10% improvement
                achievements.append({
                    "title": "Most Improved",
                    "description": f"Attendance improved by {recent_rate - previous_rate:.1f}%",
                    "icon": "📈",
                    "color": "#9C27B0"
                })
    
    return achievements

def render_achievements_section(achievements):
    """Render achievement badges in HTML"""
    if not achievements:
        return ""
    
    html_content = """
    <div style="margin-top: 20px;">
        <h3 style="margin-bottom: 15px;">🏆 Your Achievements</h3>
        <div style="display: flex; flex-wrap: wrap; gap: 10px;">
    """
    
    for achievement in achievements:
        html_content += f"""
        <div style="
            background-color: {achievement['color']}22; 
            border-left: 4px solid {achievement['color']}; 
            border-radius: 5px;
            padding: 10px 15px;
            width: 180px;
        ">
            <div style="font-size: 24px; text-align: center; margin-bottom: 5px;">
                {achievement['icon']}
            </div>
            <div style="font-weight: bold; text-align: center;">
                {achievement['title']}
            </div>
            <div style="font-size: 0.8em; color: #555; text-align: center;">
                {achievement['description']}
            </div>
        </div>
        """
    
    html_content += """
        </div>
    </div>
    """
    
    return html_content

def create_attendance_radar_chart(history_df):
    """Create a radar chart showing attendance patterns by day of week"""
    # Group by day of week
    day_stats = history_df.groupby('day_name').agg({
        'attended_classes': 'sum',
        'total_classes': 'sum'
    }).reset_index()
    
    # Calculate attendance rate
    day_stats['attendance_rate'] = day_stats.apply(
        lambda row: (row['attended_classes'] / row['total_classes'] * 100) if row['total_classes'] > 0 else 0, 
        axis=1
    )
    
    # Sort by day of week
    days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    day_stats = day_stats.set_index('day_name').loc[days_order].reset_index()
    
    # Add the first point at the end to close the loop
    day_stats = pd.concat([day_stats, day_stats.iloc[0:1]], ignore_index=True)
    
    # Create radar chart
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=day_stats['attendance_rate'],
        theta=day_stats['day_name'],
        fill='toself',
        name='Attendance',
        line=dict(color='#1E88E5', width=2),
        fillcolor='rgba(33, 150, 243, 0.3)'
    ))
    
    # Add target line (e.g., 80% attendance)
    fig.add_trace(go.Scatterpolar(
        r=[80] * len(day_stats),
        theta=day_stats['day_name'],
        name='Target (80%)',
        line=dict(color='red', dash='dash', width=1),
        fill=None
    ))
    
    fig.update_layout(
        title="Attendance Pattern by Day of Week",
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        height=400,
        margin=dict(l=10, r=10, t=40, b=10)
    )
    
    return fig

def show_enhanced_student_report():
    """
    Display an enhanced version of the student attendance report
    with advanced visualizations and new features
    """
    # Normal student report initialization here...
    
    # New section for attendance analytics
    with st.expander("📊 Advanced Analytics", expanded=True):
        st.write("Dive deeper into your attendance patterns with these analytical tools.")
        
        # Get extended attendance history
        history_df = get_extended_attendance_history(student_name, days=60)  # Increased to 60 days
        
        # Create tabs for different analytics views
        analytics_tab1, analytics_tab2, analytics_tab3, analytics_tab4 = st.tabs([
            "Course Breakdown", "Calendar View", "Time Patterns", "Achievements"
        ])
        
        with analytics_tab1:
            # Course breakdown chart
            course_chart = create_course_breakdown_chart(student_name)
            if course_chart:
                st.plotly_chart(course_chart, use_container_width=True)
                
                # Add warning for courses with low attendance
                low_attendance_courses = []
                conn = get_db_connection()
                query = """
                SELECT subject, 
                       SUM(attended) * 100.0 / COUNT(*) as rate
                FROM class_attendance
                WHERE student_name = ?
                GROUP BY subject
                HAVING rate < 80
                ORDER BY rate ASC
                """
                cursor = conn.cursor()
                cursor.execute(query, (student_name,))
                low_courses = cursor.fetchall()
                conn.close()
                
                if low_courses:
                    st.warning("⚠️ **Attention needed**: Your attendance is below 80% in these courses:")
                    for course, rate in low_courses:
                        st.markdown(f"- **{course}**: {rate:.1f}% attendance")
                    st.markdown("Consider attending these classes more consistently to improve your academic performance.")
            else:
                st.info("Not enough course data available for breakdown.")
        
        with analytics_tab2:
            # Calendar view
            st.write("Monthly attendance calendar:")
            calendar_plots = create_attendance_calendar(history_df)
            
            # Display calendars in columns
            col1, col2 = st.columns(2)
            
            for i, fig in enumerate(calendar_plots):
                with col1 if i % 2 == 0 else col2:
                    st.plotly_chart(fig, use_container_width=True)
            
            # Add export options
            st.subheader("Export Attendance Data")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(export_data_as_csv(history_df, "attendance_history.csv"), unsafe_allow_html=True)
            with col2:
                try:
                    import io
                    import xlsxwriter
                    st.markdown(export_data_as_excel(history_df, "attendance_history.xlsx"), unsafe_allow_html=True)
                except ImportError:
                    st.warning("Excel export requires xlsxwriter. Install with `pip install xlsxwriter`")
        
        with analytics_tab3:
            # Time patterns analysis
            col1, col2 = st.columns(2)
            
            with col1:
                # Radar chart by day of week
                radar_chart = create_attendance_radar_chart(history_df)
                st.plotly_chart(radar_chart, use_container_width=True)
            
            with col2:
                # Heatmap of attendance
                heatmap_chart = create_attendance_heatmap(history_df)
                st.plotly_chart(heatmap_chart, use_container_width=True)
                
            # Time attendance analysis
            st.subheader("Attendance Time Analysis")
            
            conn = get_db_connection()
            query = """
            WITH class_times AS (
                SELECT 
                    al.name,
                    c4.subject,
                    c4.start_time,
                    MIN(time(al.timestamp)) as arrival_time,
                    CAST(
                        (JULIANDAY(MIN(time(al.timestamp))) - JULIANDAY(time(c4.start_time))) * 24 * 60 AS INTEGER
                    ) as minutes_diff
                FROM attendance_log al
                JOIN class_attendance ca ON ca.student_name = al.name 
                                      AND date(al.timestamp) = ca.class_date
                                      AND ca.attended = 1
                JOIN control_4 c4 ON c4.subject = ca.subject 
                                AND c4.start_time = ca.start_time
                                AND strftime('%A', al.timestamp) = c4.day
                WHERE al.name = ?
                GROUP BY al.name, c4.subject, date(al.timestamp)
            )
            
            SELECT 
                subject,
                AVG(minutes_diff) as avg_minutes,
                MIN(minutes_diff) as min_minutes,
                MAX(minutes_diff) as max_minutes,
                COUNT(*) as class_count
            FROM class_times
            GROUP BY subject
            ORDER BY AVG(minutes_diff)
            """
            
            arrival_df = pd.read_sql_query(query, conn, params=(student_name,))
            conn.close()
            
            if not arrival_df.empty:
                # Create arrival time chart
                fig = go.Figure()
                
                # Add bar for average arrival time
                fig.add_trace(go.Bar(
                    x=arrival_df['subject'],
                    y=arrival_df['avg_minutes'],
                    marker_color=arrival_df['avg_minutes'].apply(
                        lambda x: '#4CAF50' if x <= 0 else 
                                 '#FF9800' if x <= 10 else '#F44336'
                    ),
                    text=[f"{m:.1f} min" for m in arrival_df['avg_minutes']],
                    textposition='outside',
                    hovertemplate='%{x}<br>Average: %{y:.1f} minutes<extra></extra>'
                ))
                
                # Add range markers
                for i, row in arrival_df.iterrows():
                    fig.add_trace(go.Scatter(
                        x=[row['subject'], row['subject']],
                        y=[row['min_minutes'], row['max_minutes']],
                        mode='lines',
                        line=dict(color='black', width=2),
                        showlegend=False,
                        hoverinfo='skip'
                    ))
                
                # Add reference line for "on time"
                fig.add_shape(
                    type="line",
                    x0=-0.5,
                    x1=len(arrival_df) - 0.5,
                    y0=0,
                    y1=0,
                    line=dict(color="black", width=2),
                )
                
                fig.update_layout(
                    title="Average Arrival Time Relative to Class Start (minutes)",
                    xaxis_title="",
                    yaxis=dict(
                        title="Minutes (negative = early, positive = late)",
                    ),
                    height=400,
                    margin=dict(l=10, r=10, t=50, b=110),
                )
                
                fig.update_xaxes(tickangle=45)
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Add interpretation
                avg_arrival = arrival_df['avg_minutes'].mean()
                if avg_arrival < 0:
                    st.success(f"🎉 On average, you arrive **{abs(avg_arrival):.1f} minutes early** to your classes. Great job!")
                elif avg_arrival <= 5:
                    st.info(f"👍 On average, you arrive **{avg_arrival:.1f} minutes after** class starts, which is generally acceptable.")
                else:
                    st.warning(f"⚠️ On average, you arrive **{avg_arrival:.1f} minutes late** to your classes. Try to arrive earlier to avoid missing important content.")
            else:
                st.info("Not enough attendance data to analyze arrival patterns.")
        
        with analytics_tab4:
            # Achievements section
            achievements = generate_achievements(student_name, history_df)
            
            if achievements:
                html(render_achievements_section(achievements), height=len(achievements) * 50 + 100)
                
                # Recommendation based on achievements
                st.subheader("Personalized Recommendations")
                
                # Check for types of achievements to customize recommendations
                achievement_types = [a['title'] for a in achievements]
                
                if "Most Improved" in achievement_types:
                    st.success("🚀 **Keep up the momentum!** You're showing great improvement in your attendance. Maintain this trend to see positive effects on your academic performance.")
                
                if "Early Bird" in achievement_types:
                    st.info("⏰ **Great time management!** Being early helps you prepare better for classes. Share your morning routine tips with classmates who might struggle with punctuality.")
                
                if "Perfect Attendance" in achievement_types:
                    st.success("🌟 **Outstanding commitment!** Your perfect attendance record sets you apart. This level of consistency will serve you well in your academic and future professional life.")
            else:
                st.info("Complete more classes to earn achievements!")
                st.write("Here's how you can earn achievements:")
                st.markdown("""
                - 🏆 **Attendance Champion**: Maintain perfect attendance for 5+ consecutive days
                - 🌟 **Consistency Award**: Maintain perfect attendance for 3+ consecutive days
                - 🎯 **Perfect Attendance**: Achieve 95%+ overall attendance rate
                - 🐦 **Early Bird**: Arrive early to class 5+ times in a month
                - 📈 **Most Improved**: Improve your attendance rate by 10%+ compared to the previous week
                """)
    
    # New section for attendance projections
    with st.expander("🔮 Attendance Projections", expanded=False):
        st.write("Understand the impact of future attendance on your overall rate.")
        
        # Calculate current attendance metrics
        conn = get_db_connection()
        query = """
        SELECT 
            SUM(attended) as classes_attended,
            COUNT(*) as total_classes
        FROM class_attendance
        WHERE student_name = ?
        """
        cursor = conn.cursor()
        cursor.execute(query, (student_name,))
        result = cursor.fetchone()
        
        if result and result[1] > 0:
            attended = result[0]
            total = result[1]
            current_rate = (attended / total) * 100
            
            # Get upcoming classes in the next 2 weeks
            query = """
            WITH dates(date) AS (
                SELECT date('now')
                UNION ALL
                SELECT date(date, '+1 day') 
                FROM dates 
                WHERE date < date('now', '+14 days')
            ),
            upcoming_dates AS (
                SELECT 
                    dates.date,
                    strftime('%A', dates.date) as day
                FROM dates
            ),
            upcoming_classes AS (
                SELECT 
                    d.date,
                    d.day,
                    c4.subject,
                    c4.start_time,
                    c4.end_time,
                    c4.type
                FROM upcoming_dates d
                JOIN control_4 c4 ON d.day = c4.day
                ORDER BY d.date, c4.start_time
            )
            
            SELECT COUNT(*) as upcoming_classes
            FROM upcoming_classes
            """
            
            cursor.execute(query)
            upcoming_result = cursor.fetchone()
            upcoming_classes = upcoming_result[0] if upcoming_result else 0
            
            conn.close()
            
            st.write(f"Your current attendance rate is **{current_rate:.1f}%** ({attended} out of {total} classes attended).")
            st.write(f"You have approximately **{upcoming_classes}** classes scheduled in the next 2 weeks.")
            