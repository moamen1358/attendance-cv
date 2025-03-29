"""
Data visualization utilities.

This module provides visualization functions for attendance data:
- Attendance sunburst charts
- Weekly heatmaps
- Progress gauges
- Subject comparisons
"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union

from src.database import execute_query_df
from src.core.error_handling import handle_errors

@handle_errors
def create_attendance_sunburst(student_name: str, start_date=None, end_date=None):
    """Create a sunburst chart showing attendance by subject and date"""
    # ...existing code from student_visualization.py...

@handle_errors
def create_attendance_gauge(attendance_rate: float, title: str = "Overall Attendance Rate"):
    """Create a gauge chart showing attendance rate"""
    # ...existing code from student_visualization.py...

@handle_errors
def create_weekly_heatmap(student_name: str, weeks: int = 4, start_date=None):
    """Create a heatmap showing weekly attendance patterns"""
    # ...existing code from student_visualization.py...

@handle_errors
def create_subject_radial_chart(student_name: str, start_date=None, end_date=None, min_classes: int = 2):
    """Create a radial chart comparing attendance across subjects"""
    # ...existing code from student_visualization.py...
