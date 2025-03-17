import streamlit as st
import pandas as pd
import sqlite3
from database_utils import execute_query, execute_query_df
import numpy as np
from datetime import datetime, time
import plotly.figure_factory as ff
import plotly.graph_objects as go
from copy import deepcopy
import uuid
import re

# Constants
DATABASE_PATH = 'attendance_system.db'
DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
TIME_SLOTS = [f"{i:02d}:00" for i in range(8, 21)]  # 8 AM to 8 PM
SECTION_OPTIONS = ['SEC 1', 'SEC 2', 'Both']
ROOM_OPTIONS = ['Hall A', 'Hall B', 'Hall C', 'Hall D', 'Hall E', 'Lab 101', 'Lab 202', 
               'Room 201', 'Room 202', 'Room 303', 'Workshop']
CLASS_TYPES = ['lec', 'lab', 'sec', 'tut', 'sem']

def get_db_connection():
    """Create a connection to the database"""
    return sqlite3.connect(DATABASE_PATH)

def normalize_time(time_str):
    """Normalize time string to 12-hour format with AM/PM"""
    try:
        # Try parsing as 24-hour format first
        time_obj = datetime.strptime(time_str, '%H:%M').time()
        return time_obj.strftime('%I:%M %p').lstrip('0')
    except ValueError:
        try:
            # If that fails, try parsing as 12-hour format
            time_obj = datetime.strptime(time_str, '%I:%M %p').time()
            return time_obj.strftime('%I:%M %p').lstrip('0')
        except ValueError:
            # If that fails too, return the original string
            return time_str

def format_time_display(time_str):
    """Format time for display in the timetable"""
    try:
        time_obj = datetime.strptime(time_str, '%I:%M %p').time()
        return time_obj.strftime('%I:%M %p').lstrip('0')
    except:
        try:
            time_obj = datetime.strptime(time_str, '%H:%M').time()
            return time_obj.strftime('%I:%M %p').lstrip('0')
        except:
            return time_str

def load_class_schedules():
    """Load class schedules from database"""
    conn = get_db_connection()
    
    query = """
    SELECT id, subject, day, start_time, end_time, type, section, teacher, room
    FROM class_schedules
    ORDER BY day, start_time, subject
    """
    
    df = execute_query_df(query)
    conn.close()
    
    return df

def load_subjects():
    """Load unique subjects from database"""
    conn = get_db_connection()
    
    query = """
    SELECT DISTINCT subject
    FROM class_schedules
    ORDER BY subject
    """
    
    df = execute_query_df(query)
    conn.close()
    
    return df['subject'].tolist()

def load_teachers():
    """Load unique teachers from database"""
    conn = get_db_connection()
    
    query = """
    SELECT DISTINCT teacher
    FROM class_schedules
    ORDER BY teacher
    """
    
    df = execute_query_df(query)
    conn.close()
    
    return df['teacher'].tolist()

def insert_class_schedule(data):
    """Insert a new class schedule"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
    INSERT INTO class_schedules (subject, day, start_time, end_time, type, section, teacher, room)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    try:
        cursor.execute(query, (
            data['subject'],
            data['day'],
            data['start_time'],
            data['end_time'],
            data['type'],
            data['section'],
            data['teacher'],
            data['room']
        ))
        
        conn.commit()
        last_id = cursor.lastrowid
        conn.close()
        return True, last_id
    except Exception as e:
        conn.close()
        return False, str(e)

def update_class_schedule(schedule_id, data):
    """Update an existing class schedule"""
    