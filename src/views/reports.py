"""
Reports view module.

This module provides shared reporting functionality:
- Attendance reports
- Student performance reports
- Visualizations
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

from src.database import execute_query_df
from src.core.error_handling import handle_errors
from src.core.visualizations import (
    create_attendance_sunburst, 
    create_attendance_gauge,
    create_weekly_heatmap,
    create_subject_radial_chart
)
from src.ui.components import create_metric_card
from src.views.base import BaseView

class ReportsView(BaseView):
    """Reports view for displaying attendance reports"""
    
    def __init__(self, student_name=None):
        """Initialize the reports view"""
        super().__init__(title="Attendance Report")
        self.student_name = student_name

    def _render_content(self):
        """Render the reports view content"""
        # Display the title and user info
        self.render_top_bar()
        
        if self.student_name:
            self._render_student_report(self.student_name)
        else:
            self._render_professor_report()
    
    @handle_errors
    def _render_student_report(self, student_name: str):
        """Render report for a specific student"""
        # ...existing code from student_report.py...
    
    @handle_errors
    def _render_professor_report(self):
        """Render report for a professor (all students)"""
        # ...existing code from report.py...

def show_attendance_report(username=None):
    """Show the attendance report page"""
    view = ReportsView(username)
    view.render()
