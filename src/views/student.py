"""
Student view module.

This module provides views for student users:
- Personal attendance dashboard
- Attendance visualization
- Course information
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

from src.ui.styles import hide_sidebar_for_role
from src.database import execute_query_df
from src.core.error_handling import handle_errors
from src.core.visualizations import create_attendance_sunburst, create_attendance_gauge, create_weekly_heatmap

class StudentView:
    """Encapsulates the student dashboard functionality"""
    
    def __init__(self):
        """Initialize the student view"""
        self.username = st.session_state.get('username', 'Unknown')
        self.student_id = st.session_state.get('current_user', {}).get('student_id', 'Unknown')
        self.section = st.session_state.get('current_user', {}).get('section', 'Unknown')
        self.full_name = st.session_state.get('current_user', {}).get('full_name', self.username)
    
    def show(self):
        """Display the student dashboard"""
        # Hide sidebar for students
        hide_sidebar_for_role('student')
        
        # Show the student attendance report
        self.show_student_report()
    
    def show_student_report(self):
        """Show attendance report for the current student"""
        # Top navigation bar with title and user info
        top_col1, top_col2 = st.columns([3, 2])
        
        with top_col1:
            st.markdown("## 📊 Student Attendance Dashboard", unsafe_allow_html=False)
        
        # User info and buttons in column 2
        with top_col2:
            # Username display with right alignment
            st.markdown(f"""
            <div class="username-container">
                <div class="username-text">
                    👤 {self.full_name}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Refresh and logout buttons side by side
            button_col1, button_col2 = st.columns(2)
            
            with button_col1:
                # Refresh button with same style as logout
                if st.button("🔄 Refresh", key="student_refresh", use_container_width=True):
                    st.rerun()
            
            with button_col2:
                # Logout button
                if st.button("🚪 Logout", key="student_logout", use_container_width=True):
                    for key in list(st.session_state.keys()):
                        del st.session_state[key]
                    st.query_params.clear()
                    st.rerun()
        
        # Student info card
        st.info(f"**Student ID:** {self.student_id} | **Section:** {self.section}")
        
        # Date filters for attendance data
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Start Date",
                value=datetime.now().date() - timedelta(days=30)
            )
        with col2:
            end_date = st.date_input(
                "End Date",
                value=datetime.now().date()
            )
        
        # Format dates for SQL
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")
        
        # Get attendance data for this student
        attendance_data = self.get_attendance_data(start_date_str, end_date_str)
        
        if attendance_data:
            self.display_attendance_metrics(attendance_data)
            self.display_attendance_visualizations(attendance_data)
            self.display_detailed_attendance(attendance_data)
        else:
            st.warning(f"No attendance data found for {self.username} in the selected date range.")
    
    @handle_errors
    def get_attendance_data(self, start_date, end_date):
        """Get attendance data for the current student"""
        try:
            # Get basic attendance stats
            query = """
            SELECT
                COUNT(*) as total_classes,
                SUM(attended) as attended_classes
            FROM class_attendance
            WHERE student_name = ? AND class_date BETWEEN ? AND ?
            """
            
            stats_df = execute_query_df(query, (self.username, start_date, end_date))
            
            if stats_df.empty or stats_df['total_classes'].iloc[0] == 0:
                return None
            
            # Calculate attendance rate
            total_classes = int(stats_df['total_classes'].iloc[0])
            attended_classes = int(stats_df['attended_classes'].iloc[0])
            attendance_rate = (attended_classes / total_classes * 100) if total_classes > 0 else 0
            
            # Get detailed attendance by subject
            subject_query = """
            SELECT
                subject,
                class_date,
                attended
            FROM class_attendance
            WHERE student_name = ? AND class_date BETWEEN ? AND ?
            ORDER BY class_date DESC
            """
            
            detailed_df = execute_query_df(subject_query, (self.username, start_date, end_date))
            
            # Get attendance by date for calendar view
            date_query = """
            SELECT
                class_date,
                COUNT(*) as total_classes,
                SUM(attended) as attended_classes
            FROM class_attendance
            WHERE student_name = ? AND class_date BETWEEN ? AND ?
            GROUP BY class_date
            ORDER BY class_date
            """
            
            date_df = execute_query_df(date_query, (self.username, start_date, end_date))
            
            # Prepare the return data
            return {
                'total_classes': total_classes,
                'attended_classes': attended_classes,
                'attendance_rate': attendance_rate,
                'detailed': detailed_df,
                'by_date': date_df
            }
        
        except Exception as e:
            st.error(f"Error retrieving attendance data: {e}")
            return None
    
    def display_attendance_metrics(self, attendance_data):
        """Display attendance metrics"""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Classes", attendance_data['total_classes'])
        
        with col2:
            st.metric("Classes Attended", attendance_data['attended_classes'])
        
        with col3:
            st.metric("Attendance Rate", f"{attendance_data['attendance_rate']:.1f}%")
    
    def display_attendance_visualizations(self, attendance_data):
        """Display attendance visualizations"""
        # Create tabs for different visualizations
        tabs = st.tabs(["Overview", "By Subject", "Calendar"])
        
        # Overview tab with gauge chart
        with tabs[0]:
            try:
                # Create gauge chart for attendance rate
                fig = create_attendance_gauge(
                    attendance_data['attendance_rate'], 
                    title="Overall Attendance Rate"
                )
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Error creating overview visualization: {e}")
        
        # By Subject tab with bar chart
        with tabs[1]:
            try:
                # Group by subject
                if not attendance_data['detailed'].empty:
                    by_subject = attendance_data['detailed'].groupby('subject').agg(
                        total=('subject', 'count'),
                        attended=('attended', 'sum')
                    )
                    by_subject['rate'] = (by_subject['attended'] / by_subject['total'] * 100).round(1)
                    by_subject = by_subject.reset_index()
                    
                    # Create bar chart
                    fig = px.bar(
                        by_subject,
                        x='subject',
                        y='rate',
                        text='rate',
                        labels={'rate': 'Attendance Rate (%)', 'subject': 'Subject'},
                        title='Attendance Rate by Subject',
                        color='rate',
                        color_continuous_scale='RdYlGn',
                        range_color=[0, 100]
                    )
                    fig.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No subject data available for the selected period")
            except Exception as e:
                st.error(f"Error creating subject visualization: {e}")
        
        # Calendar tab with heatmap
        with tabs[2]:
            try:
                # Create weekly attendance heatmap
                fig = create_weekly_heatmap(self.username)
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Error creating calendar visualization: {e}")
    
    def display_detailed_attendance(self, attendance_data):
        """Display detailed attendance records"""
        st.subheader("Attendance Details")
        
        if not attendance_data['detailed'].empty:
            # Add human-readable status
            detailed_df = attendance_data['detailed'].copy()
            detailed_df['status'] = detailed_df['attended'].apply(
                lambda x: "Present" if x == 1 else "Absent"
            )
            
            # Format date for display
            detailed_df['date'] = pd.to_datetime(detailed_df['class_date']).dt.strftime('%b %d, %Y')
            
            # Reorder and select columns for display
            display_df = detailed_df[['date', 'subject', 'status']]
            
            # Display the table
            st.dataframe(
                display_df,
                use_container_width=True,
                column_config={
                    "date": st.column_config.TextColumn("Date"),
                    "subject": st.column_config.TextColumn("Subject"),
                    "status": st.column_config.TextColumn("Status")
                }
            )
        else:
            st.info("No detailed attendance records found for the selected period")


def show_student_view():
    """Show the student interface"""
    view = StudentView()
    view.show()
