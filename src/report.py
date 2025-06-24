import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sqlite3
import io
import sys
import time

# Add utils directory to path
sys.path.append('/home/invisa/Desktop/my_grad_streamlit')

# Update imports to use utils directory
from src.database_utils import execute_query, execute_query_df, get_attendance_records_schema
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

# Function to get attendance data with filtering options - now with improved schema validation
def get_attendance_data(start_date=None, end_date=None, student_name=None, limit=1000):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # First check if the attendance_records_enhanced table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='attendance_records_enhanced'")
        if cursor.fetchone():
            table_name = 'attendance_records_enhanced'
        else:
            # Fallback to old tables if enhanced table doesn't exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='attendance_log'")
            if cursor.fetchone():
                table_name = 'attendance_log'
            else:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='attendance_records'")
                if cursor.fetchone():
                    table_name = 'attendance_records'
                else:
                    # No attendance tables exist
                    return pd.DataFrame(columns=['name', 'timestamp', 'date', 'time'])
        
        # Handle different table structures
        if table_name == 'attendance_records_enhanced':
            # Enhanced table structure with foreign keys
            query = f"""
            SELECT 
                s.name,
                ar.attendance_date || ' ' || COALESCE(ar.attendance_time, '00:00:00') as timestamp,
                ar.attendance_date as date,
                COALESCE(ar.attendance_time, '00:00:00') as time,
                ar.status
            FROM attendance_records_enhanced ar
            JOIN students_enhanced s ON ar.student_id = s.student_id
            WHERE 1=1
            """
            
            # Add filters for enhanced table
            params = []
            if start_date:
                query += " AND ar.attendance_date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND ar.attendance_date <= ?"
                params.append(end_date)
            if student_name:
                query += " AND s.name LIKE ?"
                params.append(f"%{student_name}%")
                
            query += " ORDER BY ar.attendance_date DESC, ar.attendance_time DESC"
            if limit:
                query += f" LIMIT {limit}"
                
        else:
            # Legacy table structure
            # Get schema mapping to handle column name differences
            schema = get_attendance_records_schema()
            student_col = schema['student_name']
            timestamp_col = schema['timestamp']
            
        # Check what columns actually exist in the table
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Build a SELECT clause based on available columns
        select_cols = [student_col, timestamp_col]  # These are required
        
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
            where_clauses.append(f"DATE({timestamp_col}) >= ?")
            params.append(start_date)
        
        if end_date:
            where_clauses.append(f"DATE({timestamp_col}) <= ?")
            params.append(end_date)
        
        if student_name and student_name != "All Students":
            where_clauses.append(f"{student_col} = ?")
            params.append(student_name)
        
        if where_clauses:
            query_parts.append("WHERE " + " AND ".join(where_clauses))
        
        # Add order by and limit
        query_parts.append(f"ORDER BY {timestamp_col} DESC")
        query_parts.append(f"LIMIT {limit}")
        
        # Combine query parts
        query = " ".join(query_parts)
        
        # Execute query
        df = pd.read_sql(query, conn, params=params)
        
        # Rename columns to standardized names for downstream processing
        column_mapping = {student_col: 'name', timestamp_col: 'timestamp'}
        df = df.rename(columns=column_mapping)
        
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
    """
    Get class attendance data with various filtering options.
    
    Args:
        start_date (str): Start date in 'YYYY-MM-DD' format
        end_date (str): End date in 'YYYY-MM-DD' format
        student_name (str): Name of student to filter by or None for all students
        subject (str): Subject to filter by or None for all subjects
        teacher_subjects (list): List of subjects assigned to the teacher
        
    Returns:
        DataFrame: Class attendance records
    """
    conn = get_db_connection()
    
    # Build query parts for enhanced table
    query_parts = ["""
        SELECT 
            ar.id,
            s.name as student_name,
            sub.subject_name as subject,
            ar.attendance_date as class_date,
            ar.attendance_time as start_time,
            ar.attendance_time as end_time,
            CASE WHEN ar.status = 'present' THEN 1 ELSE 0 END as attended,
            ar.status as attended_status,
            ar.notes,
            ar.academic_year,
            ar.semester
        FROM attendance_records_enhanced ar
        JOIN students_enhanced s ON ar.student_id = s.student_id
        JOIN subjects_enhanced sub ON ar.subject_id = sub.subject_id
    """]
    where_clauses = []
    params = []
    
    if start_date:
        where_clauses.append("ar.attendance_date >= ?")
        params.append(start_date)
    
    if end_date:
        where_clauses.append("ar.attendance_date <= ?")
        params.append(end_date)
    
    if student_name and student_name != "All Students":
        where_clauses.append("s.name = ?")
        params.append(student_name)
        
    if subject and subject != "All Subjects":
        where_clauses.append("sub.subject_name = ?")
        params.append(subject)
    
    # Add filter for teacher's subjects
    if teacher_subjects and "All Subjects" not in teacher_subjects:
        placeholders = ", ".join(["?"] * len(teacher_subjects))
        where_clauses.append(f"sub.subject_name IN ({placeholders})")
        params.extend(teacher_subjects)
    
    if where_clauses:
        query_parts.append("WHERE " + " AND ".join(where_clauses))
    
    # Add order by
    query_parts.append("ORDER BY ar.attendance_date DESC, ar.attendance_time ASC")
    
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

# Modified function to get list of registered students from the database
# Now also includes students who have attendance records but might not be in the students table
def get_registered_students():
    conn = get_db_connection()
    
    # First get students from the students_enhanced table
    query1 = "SELECT name FROM students_enhanced ORDER BY name"
    df1 = pd.read_sql(query1, conn)
    students_list = df1['name'].tolist() if not df1.empty else []
    
    # Then get all student names from attendance records  
    query2 = """SELECT DISTINCT s.name 
                FROM attendance_records_enhanced ar 
                JOIN students_enhanced s ON ar.student_id = s.student_id 
                ORDER BY s.name"""
    df2 = pd.read_sql(query2, conn)
    attendance_students = df2['name'].tolist() if not df2.empty else []
    
    # Also get students from attendance records for completeness
    query3 = """SELECT DISTINCT s.name 
                FROM attendance_records_enhanced ar 
                JOIN students_enhanced s ON ar.student_id = s.student_id 
                ORDER BY s.name"""
    df3 = pd.read_sql(query3, conn)
    log_students = df3['name'].tolist() if not df3.empty else []
    
    # Combine all lists and remove duplicates
    all_students = list(set(students_list + attendance_students + log_students))
    
    # Sort alphabetically
    all_students.sort()
    
    conn.close()
    return all_students

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
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='subjects_enhanced'")
            if cursor.fetchone():
                cursor.execute("SELECT subject_name FROM subjects_enhanced ORDER BY subject_name")
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

# Simplified function to add manual attendance record
# Uses the enhanced database schema for cleaner operation
def add_manual_attendance_simple(student_name, class_date, subject, attendance_time, status, notes=""):
    """
    Simplified function to add manual attendance record
    Uses the enhanced database schema for cleaner operation
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get student ID
        cursor.execute("SELECT student_id FROM students_enhanced WHERE name = ?", (student_name,))
        student_result = cursor.fetchone()
        if not student_result:
            return False, f"Student '{student_name}' not found"
        student_id = student_result[0]
        
        # Get subject ID
        cursor.execute("SELECT subject_id FROM subjects_enhanced WHERE subject_name = ?", (subject,))
        subject_result = cursor.fetchone()
        if not subject_result:
            return False, f"Subject '{subject}' not found"
        subject_id = subject_result[0]
        
        # Format the time for database
        time_str = attendance_time.strftime("%H:%M:%S")
        
        # Insert or update attendance record
        cursor.execute("""
            INSERT OR REPLACE INTO attendance_records_enhanced
            (student_id, subject_id, attendance_date, attendance_time, status, notes, recorded_by)
            VALUES (?, ?, ?, ?, ?, ?, 'manual_entry')
        """, (student_id, subject_id, class_date, time_str, status, notes))
        
        conn.commit()
        return True, "Attendance recorded successfully"
        
    except Exception as e:
        conn.rollback()
        return False, f"Error recording attendance: {str(e)}"
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
        search_condition = "AND s.name LIKE ?"
        params.append(f"%{search_term}%")
    
    # Build date filter conditions
    date_condition = ""
    if start_date:
        date_condition += "AND ar.attendance_date >= ?"
        params.append(start_date)
    
    if end_date:
        date_condition += "AND ar.attendance_date <= ?"
        params.append(end_date)
    
    # Build subject filter condition
    subject_condition = ""
    if teacher_subjects and "All Subjects" not in teacher_subjects:
        placeholders = ", ".join(["?"] * len(teacher_subjects))
        subject_condition = f"AND sub.subject_name IN ({placeholders})"
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
    SELECT COUNT(DISTINCT s.name) as total_count
    FROM attendance_records_enhanced ar
    JOIN students_enhanced s ON ar.student_id = s.student_id
    JOIN subjects_enhanced sub ON ar.subject_id = sub.subject_id
    WHERE 1=1 {date_condition} {search_condition} {subject_condition}
    """
    
    count_df = pd.read_sql_query(count_query, conn, params=params)
    total_count = count_df['total_count'][0] if not count_df.empty else 0
    
    # Main query with sorting and pagination
    query = f"""
    SELECT 
        s.name as student_name,
        COUNT(CASE WHEN ar.status = 'present' THEN 1 ELSE NULL END) as attended_classes,
        COUNT(*) as total_classes,
        COUNT(CASE WHEN ar.status = 'present' THEN 1 ELSE NULL END) * 100.0 / COUNT(*) as attendance_rate,
        MIN(ar.attendance_date) as first_date,
        MAX(ar.attendance_date) as last_date
    FROM attendance_records_enhanced ar
    JOIN students_enhanced s ON ar.student_id = s.student_id
    JOIN subjects_enhanced sub ON ar.subject_id = sub.subject_id
    WHERE 1=1 {date_condition} {search_condition} {subject_condition}
    GROUP BY s.name, ar.student_id
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
        conditions.append("ar.attendance_date >= ?")
        params.append(start_date)
    
    if end_date:
        conditions.append("ar.attendance_date <= ?")
        params.append(end_date)
    
    if search_term:
        conditions.append("sub.subject_name LIKE ?")
        params.append(f"%{search_term}%")
    
    # Add filter for teacher's subjects
    if teacher_subjects and "All Subjects" not in teacher_subjects:
        placeholders = ", ".join(["?"] * len(teacher_subjects))
        conditions.append(f"sub.subject_name IN ({placeholders})")
        params.extend(teacher_subjects)
    
    # Build WHERE clause
    where_clause = " AND ".join(conditions)
    if where_clause:
        where_clause = "WHERE " + where_clause
    
    # Query for subject statistics
    query = f"""
    SELECT 
        sub.subject_name as subject,
        COUNT(DISTINCT s.name) as unique_students,
        COUNT(CASE WHEN ar.status = 'present' THEN 1 ELSE NULL END) as attended_count,
        COUNT(*) as total_count,
        COUNT(CASE WHEN ar.status = 'present' THEN 1 ELSE NULL END) * 100.0 / COUNT(*) as attendance_rate
    FROM attendance_records_enhanced ar
    JOIN students_enhanced s ON ar.student_id = s.student_id
    JOIN subjects_enhanced sub ON ar.subject_id = sub.subject_id
    {where_clause}
    GROUP BY sub.subject_name
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
        conditions.append("ar.attendance_date >= ?")
        params.append(start_date)
    
    if end_date:
        conditions.append("ar.attendance_date <= ?")
        params.append(end_date)
    
    # Add filter for teacher's subjects
    if teacher_subjects and "All Subjects" not in teacher_subjects:
        placeholders = ", ".join(["?"] * len(teacher_subjects))
        conditions.append(f"sub.subject_name IN ({placeholders})")
        params.extend(teacher_subjects)
    
    # Build WHERE clause
    where_clause = " AND ".join(conditions)
    if where_clause:
        where_clause = "WHERE " + where_clause
    
    # Query for monthly trends
    query = f"""
    SELECT 
        strftime('%Y-%m', ar.attendance_date) as month,
        COUNT(DISTINCT ar.student_id) as active_students,
        COUNT(*) as total_classes,
        COUNT(CASE WHEN ar.status = 'present' THEN 1 ELSE NULL END) as attended_classes,
        COUNT(CASE WHEN ar.status = 'present' THEN 1 ELSE NULL END) * 100.0 / COUNT(*) as attendance_rate
    FROM attendance_records_enhanced ar
    JOIN students_enhanced s ON ar.student_id = s.student_id
    JOIN subjects_enhanced sub ON ar.subject_id = sub.subject_id
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
        conditions.append("ar.attendance_date >= ?")
        params.append(start_date)
    
    if end_date:
        conditions.append("ar.attendance_date <= ?")
        params.append(end_date)
    
    # Add filter for teacher's subjects
    if teacher_subjects and "All Subjects" not in teacher_subjects:
        placeholders = ", ".join(["?"] * len(teacher_subjects))
        conditions.append(f"sub.subject_name IN ({placeholders})")
        params.extend(teacher_subjects)
    
    # Build WHERE clause
    where_clause = " AND ".join(conditions)
    if where_clause:
        where_clause = "WHERE " + where_clause
    
    # Query for top performers
    top_query = f"""
    SELECT 
        s.name as student_name,
        COUNT(CASE WHEN ar.status = 'present' THEN 1 ELSE NULL END) as attended_classes,
        COUNT(*) as total_classes,
        COUNT(CASE WHEN ar.status = 'present' THEN 1 ELSE NULL END) * 100.0 / COUNT(*) as attendance_rate
    FROM attendance_records_enhanced ar
    JOIN students_enhanced s ON ar.student_id = s.student_id
    JOIN subjects_enhanced sub ON ar.subject_id = sub.subject_id
    {where_clause}
    GROUP BY s.name, ar.student_id
    HAVING COUNT(*) > 3
    ORDER BY attendance_rate DESC
    LIMIT {limit}
    """
    
    # Query for bottom performers
    bottom_query = f"""
    SELECT 
        s.name as student_name,
        COUNT(CASE WHEN ar.status = 'present' THEN 1 ELSE NULL END) as attended_classes,
        COUNT(*) as total_classes,
        COUNT(CASE WHEN ar.status = 'present' THEN 1 ELSE NULL END) * 100.0 / COUNT(*) as attendance_rate
    FROM attendance_records_enhanced ar
    JOIN students_enhanced s ON ar.student_id = s.student_id
    JOIN subjects_enhanced sub ON ar.subject_id = sub.subject_id
    {where_clause}
    GROUP BY s.name, ar.student_id
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
    # Apply global CSS
    apply_global_css()
    
    # Add enhanced CSS for professor dashboard
    st.markdown("""
    <style>
    /* Enhanced dashboard styling */
    .dashboard-container {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        min-height: 100vh;
        padding: 0;
    }
    
    /* Modern card styling */
    .professor-card {
        background: white;
        border-radius: 15px;
        padding: 25px;
        margin: 15px 0;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        border: 1px solid rgba(255,255,255,0.2);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .professor-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(0,0,0,0.15);
    }
    
    /* Header card styling */
    .header-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        text-align: center;
        margin-bottom: 30px;
    }
    
    /* Stats card styling */
    .stats-card {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        color: white;
        text-align: center;
    }
    
    /* Metric cards */
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border-left: 4px solid;
        margin: 10px 0;
        transition: all 0.3s ease;
    }
    
    .metric-card.students { border-left-color: #3498db; }
    .metric-card.attendance { border-left-color: #2ecc71; }
    .metric-card.rate { border-left-color: #f39c12; }
    
    .metric-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }
    
    .metric-number {
        font-size: 2.5rem;
        font-weight: 700;
        color: #2c3e50;
        margin: 0;
    }
    
    .metric-label {
        font-size: 1rem;
        color: #7f8c8d;
        margin: 5px 0 0 0;
        font-weight: 500;
    }
    
    /* Tab styling improvements */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background: white;
        border-radius: 10px;
        padding: 5px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        border-radius: 8px;
        color: #64748b;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
    }
    
    /* Subject overview styling */
    .subject-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 30px;
        border-radius: 15px;
        text-align: center;
        margin: 20px 0;
        position: relative;
        overflow: hidden;
    }
    
    .subject-header:before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
        animation: pulse 4s ease-in-out infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 0.3; }
        50% { opacity: 0.1; }
    }
    
    .subject-title {
        font-size: 2rem;
        font-weight: 700;
        margin: 0 0 10px 0;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        position: relative;
        z-index: 1;
    }
    
    .subject-code {
        font-size: 1.2rem;
        opacity: 0.9;
        position: relative;
        z-index: 1;
    }
    
    /* Enhanced form styling */
    .form-container {
        background: white;
        border-radius: 15px;
        padding: 30px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        margin: 20px 0;
    }
    
    .form-section-title {
        color: #2c3e50;
        font-size: 1.5rem;
        font-weight: 600;
        margin: 0 0 20px 0;
        text-align: center;
        position: relative;
    }
    
    .form-section-title:after {
        content: '';
        position: absolute;
        bottom: -5px;
        left: 50%;
        transform: translateX(-50%);
        width: 50px;
        height: 3px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 2px;
    }
    </style>
    """, unsafe_allow_html=True)
    
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
        # Check which columns actually exist in the subjects_enhanced table
        cursor.execute("PRAGMA table_info(subjects_enhanced)")
        available_columns = {col[1].lower(): col[1] for col in cursor.fetchall()}
        print(f"Available columns in subjects_enhanced table: {available_columns}")
        
        # Get subject table schema info - only include columns that actually exist
        id_col = available_columns.get('subject_id', available_columns.get('id', 'subject_id'))
        name_col = available_columns.get('subject_name', available_columns.get('name', 'subject_name'))
        
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
        
        # Try teacher_subjects_enhanced table with users_enhanced (our actual setup)
        query = f"""
        SELECT {', '.join(select_columns)}
        FROM subjects_enhanced s
        JOIN teacher_subjects_enhanced tse ON s.{id_col} = tse.subject_id
        JOIN users_enhanced u ON tse.teacher_id = u.linked_id
        WHERE u.username = ? AND u.role = 'teacher' AND tse.status = 'active'
        ORDER BY s.{name_col}
        """
        
        print(f"Executing query: {query}")
        assigned_subjects = pd.read_sql_query(query, conn, params=(username,))
        
        # If no results, try fallback approach
        if assigned_subjects.empty:
            # Get teacher_id from users_enhanced first
            cursor.execute("SELECT linked_id FROM users_enhanced WHERE username = ? AND role = 'teacher'", (username,))
            teacher_result = cursor.fetchone()
            
            if teacher_result:
                teacher_id = teacher_result[0]
                query = f"""
                SELECT {', '.join(select_columns)}
                FROM subjects_enhanced s
                JOIN teacher_subjects_enhanced tse ON s.{id_col} = tse.subject_id
                WHERE tse.teacher_id = ? AND tse.status = 'active'
                ORDER BY s.{name_col}
                """
                print(f"Executing teacher_id query: {query}")
                assigned_subjects = pd.read_sql_query(query, conn, params=(teacher_id,))
    except Exception as e:
        st.error(f"Error querying subjects: {e}")
    finally:
        conn.close()
    
    # Get teacher's subjects using the enhanced function
    subjects_list = get_teacher_subjects(username)
    
    # Check if teacher has assigned subjects
    if not subjects_list:
        st.error("❌ No subjects assigned to you. Please contact an administrator.")
        
        # Show available subjects for reference
        conn = sqlite3.connect(DATABASE_PATH)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT subject_name, course_code FROM subjects_enhanced ORDER BY subject_name")
            all_subjects = cursor.fetchall()
            
            if all_subjects:
                st.info("📚 Available subjects in the system:")
                for subject_name, course_code in all_subjects[:10]:  # Show first 10
                    st.write(f"• {subject_name} ({course_code})")
                if len(all_subjects) > 10:
                    st.write(f"... and {len(all_subjects) - 10} more subjects")
        except Exception as e:
            st.error(f"Error loading subjects: {e}")
        finally:
            conn.close()
        
        return
    
    # Since teachers now have only one subject, get the primary subject
    primary_subject = subjects_list[0]
    if '(' in primary_subject:
        subject_name = primary_subject.split('(')[0].strip()
        subject_code = primary_subject.split('(')[1].replace(')', '').strip()
    else:
        subject_name = primary_subject
        subject_code = ""
    
    # Display teacher's assigned subject with enhanced modern styling
    st.markdown(f"""
    <div class="subject-header">
        <h1 class="subject-title">📚 {subject_name}</h1>
        <p class="subject-code">Course Code: {subject_code}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Now get specific statistics for this teacher's subject
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # Get subject_id for the teacher's assigned subject
        cursor.execute("""
            SELECT subject_id FROM subjects_enhanced 
            WHERE subject_name = ?
        """, (subject_name,))
        
        subject_result = cursor.fetchone()
        if not subject_result:
            st.error(f"Subject '{subject_name}' not found in database")
            return
        
        subject_id = subject_result[0]
        
        # Get attendance statistics for this specific subject
        # First get enrolled students count
        cursor.execute("""
            SELECT COUNT(DISTINCT student_id) as enrolled_students
            FROM student_enrollments_enhanced
            WHERE subject_id = ? AND status IN ('enrolled', 'active')
        """, (subject_id,))
        
        enrolled_result = cursor.fetchone()
        total_students = enrolled_result[0] if enrolled_result else 0
        
        # Then get attendance statistics from actual attendance records
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN status = 'present' THEN 1 END) as present_count,
                COUNT(*) as total_records,
                ROUND(COUNT(CASE WHEN status = 'present' THEN 1 END) * 100.0 / COUNT(*), 1) as attendance_rate
            FROM attendance_records_enhanced
            WHERE subject_id = ?
        """, (subject_id,))
        
        stats = cursor.fetchone()
        if stats:
            present_count, total_records, attendance_rate = stats
        else:
            present_count, total_records, attendance_rate = 0, 0, 0
            
        # Handle case where there are no attendance records yet
        if total_records == 0:
            attendance_rate = 0
        
        # Modern dashboard metrics
        st.markdown("""
        <div class="professor-card stats-card">
            <h2 style="margin: 0 0 20px 0; font-size: 1.5rem;">📊 Class Overview</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Display metrics in a clean grid with modern cards
        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
        
        with metric_col1:
            st.markdown(f"""
            <div class="metric-card students">
                <p class="metric-number">{total_students or 0}</p>
                <p class="metric-label">👥 Students</p>
            </div>
            """, unsafe_allow_html=True)
        
        with metric_col2:
            st.markdown(f"""
            <div class="metric-card attendance">
                <p class="metric-number">{present_count or 0}</p>
                <p class="metric-label">✅ Present</p>
            </div>
            """, unsafe_allow_html=True)
        
        with metric_col3:
            st.markdown(f"""
            <div class="metric-card">
                <p class="metric-number">{total_records or 0}</p>
                <p class="metric-label">📅 Total Classes</p>
            </div>
            """, unsafe_allow_html=True)
        
        with metric_col4:
            rate_color = "#2ecc71" if (attendance_rate or 0) >= 75 else "#f39c12" if (attendance_rate or 0) >= 60 else "#e74c3c"
            st.markdown(f"""
            <div class="metric-card rate" style="border-left-color: {rate_color};">
                <p class="metric-number" style="color: {rate_color};">{attendance_rate or 0}%</p>
                <p class="metric-label">📊 Rate</p>
            </div>
            """, unsafe_allow_html=True)
            attendance_rate = attendance_rate or 0
        # Add some breathing space at the bottom
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Manual Attendance Entry Section
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 25px; 
            border-radius: 15px; 
            border: none;
            box-shadow: 0 8px 32px rgba(102, 126, 234, 0.2);
            margin: 20px 0;
        ">
            <h2 style="
                color: white; 
                margin: 0 0 10px 0; 
                font-weight: 600;
                text-shadow: 0 2px 4px rgba(0,0,0,0.3);
                display: flex;
                align-items: center;
                gap: 10px;
            ">
                ✏️ Manual Attendance Entry
            </h2>
            <p style="
                color: rgba(255,255,255,0.9); 
                margin: 0;
                font-size: 16px;
            ">
                Record attendance for students in your class
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Get students enrolled in this subject for manual entry
        cursor.execute("""
            SELECT DISTINCT s.student_id, s.name 
            FROM students_enhanced s
            JOIN student_enrollments_enhanced se ON s.student_id = se.student_id
            WHERE se.subject_id = ? AND se.status IN ('enrolled', 'active')
            ORDER BY s.name
        """, (subject_id,))
        
        enrolled_students = cursor.fetchall()
        
        if enrolled_students:
            # Manual entry form - properly wrapped
            with st.form("manual_attendance_form_main", clear_on_submit=False):
                st.markdown("### 👥 Student & Class Information")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    # Student selection dropdown
                    st.markdown("**🎓 Select Student**")
                    student_options = [name for student_id, name in enrolled_students]
                    selected_student_name = st.selectbox(
                        "Choose student",
                        options=student_options,
                        key="manual_student_select_main",
                        help="Choose the student to record attendance for",
                        label_visibility="collapsed"
                    )
                    # Get student ID for the selected name
                    selected_student_id = next(student_id for student_id, name in enrolled_students if name == selected_student_name)
                
                with col2:
                    # Date selection
                    st.markdown("**📅 Class Date**")
                    selected_date = st.date_input(
                        "Select date",
                        value=datetime.now().date(),
                        key="manual_date_select_main",
                        help="Select the date of the class",
                        label_visibility="collapsed"
                    )
                
                with col3:
                    # Time selection dropdown
                    st.markdown("**🕐 Class Hour**")
                    time_options = [
                        "08:00", "09:00", "10:00", "11:00", "12:00",
                        "13:00", "14:00", "15:00", "16:00", "17:00", "18:00"
                    ]
                    selected_time_str = st.selectbox(
                        "Select time",
                        options=time_options,
                        index=1,  # Default to 09:00
                        key="manual_time_select_main",
                        help="Select the class hour",
                        label_visibility="collapsed"
                    )
                
                with col4:
                    # Status selection
                    st.markdown("**📊 Attendance Status**")
                    status_options = ["present", "absent", "late", "excused"]
                    attendance_status = st.selectbox(
                        "Select status",
                        options=status_options,
                        key="manual_status_select_main",
                        help="Select the attendance status",
                        format_func=lambda x: {
                            "present": "✅ Present",
                            "absent": "❌ Absent", 
                            "late": "🕐 Late",
                            "excused": "📋 Excused"
                        }[x],
                        label_visibility="collapsed"
                    )
                
                # Submit button
                col_submit1, col_submit2, col_submit3 = st.columns([2, 3, 2])
                with col_submit2:
                    st.markdown("""
                    <style>
                    /* Enhanced button styling for main form */
                    div[data-testid="stForm"] button[data-testid="baseButton-primary"],
                    div[data-testid="stForm"] button[kind="primary"],
                    div[data-testid="stForm"] .stButton > button {
                        background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%) !important;
                        border: 2px solid #4CAF50 !important;
                        color: white !important;
                        font-weight: bold !important;
                        padding: 15px 30px !important;
                        border-radius: 10px !important;
                        box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3) !important;
                        width: 100% !important;
                        font-size: 16px !important;
                        min-height: 55px !important;
                    }
                    
                    /* Hover effects */
                    div[data-testid="stForm"] button:hover {
                        background: linear-gradient(135deg, #45a049 0%, #3d8b40 100%) !important;
                        transform: translateY(-2px) !important;
                        box-shadow: 0 8px 20px rgba(76, 175, 80, 0.4) !important;
                    }
                    </style>
                    """, unsafe_allow_html=True)
                    
                    # Form submit button
                    if st.form_submit_button("🎯 Add Attendance Record", type="primary", use_container_width=True):
                        try:
                            # Convert selected time string to time object for database
                            selected_time = datetime.strptime(selected_time_str, "%H:%M").time()
                            attendance_time_str = selected_time.strftime("%H:%M:%S")
                            
                            # Check if record already exists for this student, subject, and date
                            cursor.execute("""
                                SELECT id FROM attendance_records_enhanced 
                                WHERE student_id = ? AND subject_id = ? AND attendance_date = ?
                            """, (selected_student_id, subject_id, selected_date))
                            
                            existing_record = cursor.fetchone()
                            
                            if existing_record:
                                # Update existing record
                                cursor.execute("""
                                    UPDATE attendance_records_enhanced 
                                    SET status = ?, attendance_time = ?, 
                                        marked_by = ?, created_at = CURRENT_TIMESTAMP
                                    WHERE id = ?
                                """, (attendance_status, attendance_time_str, username, existing_record[0]))
                                
                                st.success(f"✅ Successfully Updated! Attendance record for **{selected_student_name}** has been updated for {selected_date.strftime('%B %d, %Y')}")
                            else:
                                # Get teacher_id for this subject
                                cursor.execute("""
                                    SELECT teacher_id FROM teacher_subjects_enhanced 
                                    WHERE subject_id = ? LIMIT 1
                                """, (subject_id,))
                                teacher_result = cursor.fetchone()
                                teacher_id = teacher_result[0] if teacher_result else 1
                                
                                # Create new record
                                cursor.execute("""
                                    INSERT INTO attendance_records_enhanced 
                                    (student_id, subject_id, teacher_id, attendance_date, attendance_time, 
                                     status, marked_by, academic_year, semester, created_at)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                                """, (selected_student_id, subject_id, teacher_id, selected_date, 
                                     attendance_time_str, attendance_status, username, '2024-2025', 'Fall'))
                                
                                st.success(f"✅ Successfully Added! New attendance record created for **{selected_student_name}** on {selected_date.strftime('%B %d, %Y')}")
                            
                            conn.commit()
                            
                            # Display confirmation details
                            status_icon = {'present': '✅', 'absent': '❌', 'late': '🕐', 'excused': '📋'}[attendance_status]
                            st.info(f"""
                            **📋 Record Details:**
                            - **Student:** {selected_student_name}
                            - **Date:** {selected_date.strftime('%B %d, %Y')}
                            - **Time:** {datetime.strptime(selected_time_str, '%H:%M').strftime('%I:%M %p')}
                            - **Status:** {attendance_status.title()} {status_icon}
                            """)
                            
                            # Refresh the page to show updated statistics
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"❌ Error Recording Attendance: {str(e)}")
                            conn.rollback()
        else:
            st.info("📚 No students are currently enrolled in this subject. Please check the student enrollment records.")
        
        st.markdown("<br>", unsafe_allow_html=True)
        # Recent Attendance Records Section
        st.markdown("""
        <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; border: 1px solid #dee2e6;">
            <h3 style="color: #495057; margin-top: 0;">📋 Recent Attendance Records</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Get recent attendance records for this subject
        cursor.execute("""
            SELECT ar.attendance_date, s.name, ar.status, ar.attendance_time, ar.notes, ar.created_at
            FROM attendance_records_enhanced ar
            JOIN students_enhanced s ON ar.student_id = s.student_id
            WHERE ar.subject_id = ?
            ORDER BY ar.attendance_date DESC, ar.attendance_time DESC
            LIMIT 10
        """, (subject_id,))
        
        recent_records = cursor.fetchall()
        
        if recent_records:
            # Create a DataFrame for better display
            df = pd.DataFrame(recent_records, columns=[
                'Date', 'Student', 'Status', 'Time', 'Notes', 'Recorded At'
            ])
            
            # Format the dataframe
            df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
            df['Time'] = df['Time'].astype(str)
            df['Notes'] = df['Notes'].fillna('')
            df['Recorded At'] = pd.to_datetime(df['Recorded At']).dt.strftime('%Y-%m-%d %H:%M')
            
            # Color code the status
            def style_status(val):
                if val == 'present':
                    return 'background-color: #d4edda; color: #155724'
                elif val == 'absent':
                    return 'background-color: #f8d7da; color: #721c24'
                elif val == 'late':
                    return 'background-color: #fff3cd; color: #856404'
                elif val == 'excused':
                    return 'background-color: #d1ecf1; color: #0c5460'
                return ''
            
            # Apply styling
            styled_df = df.style.applymap(style_status, subset=['Status'])
            
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
        else:
            st.info("No attendance records found for this subject.")
        
    except Exception as e:
        st.error(f"Error getting subject statistics: {e}")
    finally:
        conn.close()
    
    # Subject-specific statistics are complete, return here to avoid duplicate displays
    return
    
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
    
    # Get teacher's subjects - for new one-subject-per-teacher system
    teacher_subjects = []
    if user_role == 'admin':
        teacher_subjects = ["All Subjects"]
    elif user_role == 'professor':
        subjects_list = get_teacher_subjects(username)
        if subjects_list:
            # Teachers now have only one subject - use it directly
            teacher_subjects = subjects_list  # Don't add "All Subjects"
        else:
            teacher_subjects = []
    
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
    
    # Enhanced tabs with better organization and icons
    tabs = st.tabs([
        "📊 Dashboard", 
        "👥 Class Records", 
        "📋 Attendance Log", 
        "✏️ Manual Entry"
    ])
    
    # Get list of all students for filtering
    students = ["All Students"] + get_registered_students()
    subjects = teacher_subjects  # Now using teacher-specific subjects
    
    # Tab 1: Enhanced Dashboard with modern visualizations
    with tabs[0]:
        st.markdown("""
        <div class="professor-card">
            <h2 style="margin: 0 0 20px 0; color: #2c3e50; font-size: 1.8rem; text-align: center;">
                📊 Attendance Analytics Dashboard
            </h2>
        """, unsafe_allow_html=True)
        
        # Get overall attendance metrics - filtered by teacher subjects
        overall_stats = get_teacher_overall_stats(start_date_str, end_date_str, teacher_subjects)
        monthly_trends = get_monthly_attendance_trends(start_date_str, end_date_str, teacher_subjects=teacher_subjects)
        
        total_students = overall_stats.get('total_students', 0)
        total_attended = overall_stats.get('attended_classes', 0)
        total_classes = overall_stats.get('total_classes', 0)
        overall_rate = overall_stats.get('attendance_rate', 0)
        
        # Create a row with two columns for overall metrics and gauge chart
        col1, col2 = st.columns([3, 2])
        
        # Column 1: Overall metrics in a more visual format
        with col1:
            st.subheader("Overall Attendance")
            
            # Create a nice metric row
            metric_cols = st.columns(3)
            with metric_cols[0]:
                st.metric("Total Students", total_students)
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
        
        # Display top performers section with a completely different style
        st.subheader("Top Students by Attendance")
        
        # New leaderboard style CSS - completely different approach
        st.markdown("""
        <style>
        .leaderboard-container {
            border-radius: 12px;
            background: linear-gradient(145deg, #f0f8ff, #ffffff);
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
            padding: 1.2rem;
            margin-bottom: 1.5rem;
        }
        .leaderboard-title {
            color: #3f51b5;
            font-weight: 600;
            font-size: 1.2rem;
            margin-bottom: 1rem;
            text-align: center;
        }
        .leaderboard-row {
            display: flex;
            align-items: center;
            padding: 12px 15px;
            border-bottom: 1px solid #eee;
            transition: transform 0.2s;
        }
        .leaderboard-row:hover {
            background-color: rgba(63, 81, 181, 0.05);
            transform: translateY(-2px);
        }
        .leaderboard-row:last-child {
            border-bottom: none;
        }
        .rank {
            font-weight: bold;
            font-size: 1.5rem;
            min-width: 40px;
            text-align: center;
        }
        .rank-1 { color: gold; }
        .rank-2 { color: silver; }
        .rank-3 { color: #cd7f32; } /* Bronze */
        .student-avatar {
            width: 50px;
            height: 50px;
            border-radius: 50%;
            margin: 0 15px;
            background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.3rem;
            font-weight: bold;
        }
        .perfect-avatar {
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        }
        .student-info {
            flex-grow: 1;
        }
        .student-name {
            font-size: 1.1rem;
            font-weight: 600;
            color: #333;
            margin-bottom: 4px;
        }
        .student-stats {
            font-size: 0.9rem;
            color: #666;
        }
        .attendance-bar {
            height: 8px;
            width: 100%;
            background-color: #f0f0f0;
            border-radius: 4px;
            margin-top: 5px;
            overflow: hidden;
        }
        .attendance-fill {
            height: 100%;
            border-radius: 4px;
        }
        .perfect-fill {
            background: linear-gradient(to right, #11998e, #38ef7d);
        }
        .high-fill {
            background: linear-gradient(to right, #396afc, #2948ff);
        }
        .attendance-percent {
            min-width: 60px;
            text-align: right;
            font-weight: bold;
            font-size: 1.2rem;
            padding-left: 15px;
        }
        .perfect-percent {
            color: #11998e;
        }
        .high-percent {
            color: #396afc;
        }
        .medal-icon {
            font-size: 1.4rem;
            margin-right: 10px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Display top performers in a horizontal leaderboard style
        if not top_df.empty:
            # Create leaderboard container
            st.markdown('<div class="leaderboard-container">', unsafe_allow_html=True)
            
            # For each of the top students 
            for i, (_, row) in enumerate(top_df.iterrows()):
                if i < 3:  # Show only up to 3 students
                    is_perfect = row['attendance_rate'] == 100.0
                    
                    # Set classes based on attendance
                    avatar_class = "student-avatar perfect-avatar" if is_perfect else "student-avatar"
                    fill_class = "attendance-fill perfect-fill" if is_perfect else "attendance-fill high-fill"
                    percent_class = "attendance-percent perfect-percent" if is_perfect else "attendance-percent high-percent"
                    
                    # Rank number
                    rank_num = i + 1
                    
                    # Create leaderboard row
                    st.markdown(f"""
                    <div class="leaderboard-row">
                        <div class="rank rank-{rank_num}">{rank_num}</div>
                        <div class="{avatar_class}">{row['student_name'][0].upper()}</div>
                        <div class="student-info">
                            <div class="student-name">{row['student_name']}</div>
                            <div class="student-stats">
                                Attended {row['attended_classes']} of {row['total_classes']} classes
                                <div class="attendance-bar">
                                    <div class="{fill_class}" style="width: {row['attendance_rate']}%;"></div>
                                </div>
                            </div>
                        </div>
                        <div class="{percent_class}">{row['attendance_rate']:.1f}%</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Close the leaderboard container
            st.markdown('</div>', unsafe_allow_html=True)
            
            # If there are perfect attendance students, show recognition message
            perfect_students = top_df[top_df['attendance_rate'] == 100.0]
            if not perfect_students.empty:
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
        buffer = io.BytesIO()  # Fix: io.Bytes.IO() -> io.BytesIO()
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

    # Tab 4: Enhanced Manual Entry
    with tabs[3]:
        # Get the subject ID for the current teacher
        conn_tab = sqlite3.connect(DATABASE_PATH)
        cursor_tab = conn_tab.cursor()
        
        try:
            # Get subject_id for the teacher's assigned subject
            cursor_tab.execute("""
                SELECT subject_id FROM subjects_enhanced 
                WHERE subject_name = ?
            """, (subject_name,))
            
            subject_result = cursor_tab.fetchone()
            if not subject_result:
                st.error("❌ Subject not found in database.")
                return
            
            tab_subject_id = subject_result[0]
            
            # Get students enrolled in this subject
            cursor_tab.execute("""
                SELECT DISTINCT s.student_id, s.name 
                FROM students_enhanced s
                JOIN student_enrollments_enhanced se ON s.student_id = se.student_id
                WHERE se.subject_id = ? AND se.status IN ('enrolled', 'active')
                ORDER BY s.name
            """, (tab_subject_id,))
            
            enrolled_students = cursor_tab.fetchall()
            
            if enrolled_students:
                # Manual Attendance Entry Section
                st.markdown("""
                <div style="
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 25px; 
                    border-radius: 15px; 
                    border: none;
                    box-shadow: 0 8px 32px rgba(102, 126, 234, 0.2);
                    margin: 20px 0;
                ">
                    <h2 style="
                        color: white; 
                        margin: 0 0 10px 0; 
                        font-weight: 600;
                        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
                        display: flex;
                        align-items: center;
                        gap: 10px;
                    ">
                        ✏️ Manual Attendance Entry
                    </h2>
                    <p style="
                        color: rgba(255,255,255,0.9); 
                        margin: 0;
                        font-size: 16px;
                    ">
                        Record attendance for students in your class
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # Manual entry form - properly wrapped
                with st.form("manual_attendance_form_tab", clear_on_submit=False):
                    st.markdown("### 👥 Student & Class Information")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        # Student selection dropdown
                        st.markdown("**🎓 Select Student**")
                        student_options = [name for student_id, name in enrolled_students]
                        selected_student_name = st.selectbox(
                            "Choose student",
                            options=student_options,
                            key="manual_student_select_tab",
                            help="Choose the student to record attendance for",
                            label_visibility="collapsed"
                        )
                        # Get student ID for the selected name
                        selected_student_id = next(student_id for student_id, name in enrolled_students if name == selected_student_name)
                    
                    with col2:
                        # Date selection
                        st.markdown("**📅 Class Date**")
                        selected_date = st.date_input(
                            "Select date",
                            value=datetime.now().date(),
                            key="manual_date_select_tab",
                            help="Select the date of the class",
                            label_visibility="collapsed"
                        )
                    
                    with col3:
                        # Time selection dropdown
                        st.markdown("**🕐 Class Hour**")
                        time_options = [
                            "08:00", "09:00", "10:00", "11:00", "12:00",
                            "13:00", "14:00", "15:00", "16:00", "17:00", "18:00"
                        ]
                        selected_time_str = st.selectbox(
                            "Select time",
                            options=time_options,
                            index=1,  # Default to 09:00
                            key="manual_time_select_tab",
                            help="Select the class hour",
                            label_visibility="collapsed"
                        )
                    
                    with col4:
                        # Status selection
                        st.markdown("**📊 Attendance Status**")
                        status_options = ["present", "absent", "late", "excused"]
                        attendance_status = st.selectbox(
                            "Select status",
                            options=status_options,
                            key="manual_status_select_tab",
                            help="Select the attendance status",
                            format_func=lambda x: {
                                "present": "✅ Present",
                                "absent": "❌ Absent", 
                                "late": "🕐 Late",
                                "excused": "📋 Excused"
                            }[x],
                            label_visibility="collapsed"
                        )
                    
                    # Submit button
                    col_submit1, col_submit2, col_submit3 = st.columns([2, 3, 2])
                    with col_submit2:
                        st.markdown("""
                        <style>
                        /* Enhanced button styling */
                        div[data-testid="stForm"] button[data-testid="baseButton-primary"],
                        div[data-testid="stForm"] button[kind="primary"],
                        div[data-testid="stForm"] .stButton > button {
                            background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%) !important;
                            border: 2px solid #4CAF50 !important;
                            color: white !important;
                            font-weight: bold !important;
                            padding: 15px 30px !important;
                            border-radius: 10px !important;
                            box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3) !important;
                            width: 100% !important;
                            font-size: 16px !important;
                            min-height: 55px !important;
                        }
                        
                        /* Hover effects */
                        div[data-testid="stForm"] button:hover {
                            background: linear-gradient(135deg, #45a049 0%, #3d8b40 100%) !important;
                            transform: translateY(-2px) !important;
                            box-shadow: 0 8px 20px rgba(76, 175, 80, 0.4) !important;
                        }
                        </style>
                        """, unsafe_allow_html=True)
                        
                        # Form submit button
                        if st.form_submit_button("🎯 Add Attendance Record", type="primary", use_container_width=True):
                            try:
                                # Convert selected time string to time object for database
                                selected_time = datetime.strptime(selected_time_str, "%H:%M").time()
                                attendance_time_str = selected_time.strftime("%H:%M:%S")
                                
                                # Check if record already exists for this student, subject, and date
                                cursor_tab.execute("""
                                    SELECT id FROM attendance_records_enhanced 
                                    WHERE student_id = ? AND subject_id = ? AND attendance_date = ?
                                """, (selected_student_id, tab_subject_id, selected_date))
                                
                                existing_record = cursor_tab.fetchone()
                                
                                if existing_record:
                                    # Update existing record
                                    cursor_tab.execute("""
                                        UPDATE attendance_records_enhanced 
                                        SET status = ?, attendance_time = ?, 
                                            marked_by = ?, created_at = CURRENT_TIMESTAMP
                                        WHERE id = ?
                                    """, (attendance_status, attendance_time_str, username, existing_record[0]))
                                    
                                    st.success(f"✅ Successfully Updated! Attendance record for **{selected_student_name}** has been updated for {selected_date.strftime('%B %d, %Y')}")
                                else:
                                    # Get teacher_id for this subject
                                    cursor_tab.execute("""
                                        SELECT teacher_id FROM teacher_subjects_enhanced 
                                        WHERE subject_id = ? LIMIT 1
                                    """, (tab_subject_id,))
                                    teacher_result = cursor_tab.fetchone()
                                    teacher_id = teacher_result[0] if teacher_result else 1
                                    
                                    # Create new record
                                    cursor_tab.execute("""
                                        INSERT INTO attendance_records_enhanced 
                                        (student_id, subject_id, teacher_id, attendance_date, attendance_time, 
                                         status, marked_by, academic_year, semester, created_at)
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                                    """, (selected_student_id, tab_subject_id, teacher_id, selected_date, 
                                         attendance_time_str, attendance_status, username, '2024-2025', 'Fall'))
                                    
                                    st.success(f"✅ Successfully Added! New attendance record created for **{selected_student_name}** on {selected_date.strftime('%B %d, %Y')}")
                                
                                conn_tab.commit()
                                
                                # Display confirmation details
                                status_icon = {'present': '✅', 'absent': '❌', 'late': '🕐', 'excused': '📋'}[attendance_status]
                                st.info(f"""
                                **📋 Record Details:**
                                - **Student:** {selected_student_name}
                                - **Date:** {selected_date.strftime('%B %d, %Y')}
                                - **Time:** {datetime.strptime(selected_time_str, '%H:%M').strftime('%I:%M %p')}
                                - **Status:** {attendance_status.title()} {status_icon}
                                """)
                                
                                # Refresh the page to show updated statistics
                                st.rerun()
                                
                            except Exception as e:
                                st.error(f"❌ Error Recording Attendance: {str(e)}")
                                conn_tab.rollback()
            else:
                st.info("📚 No students are currently enrolled in this subject. Please check the student enrollment records.")
                
        except Exception as e:
            st.error(f"Error setting up manual attendance form: {e}")
        finally:
            conn_tab.close()
