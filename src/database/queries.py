"""
Common database queries for the application.

This module provides specialized query functions that abstract common
database operations used throughout the application.
"""
import sqlite3
import pandas as pd
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path

from src.database.connection import get_connection, execute_query, execute_query_df
from src.database.models import User, Student, Professor, Subject, Attendance

# Database path with cross-platform compatibility
DATABASE_PATH = Path('attendance_system.db')

def get_user_by_username(username: str) -> Optional[User]:
    """
    Get a user by username
    
    Args:
        username: User's username
        
    Returns:
        User object if found, None otherwise
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, role, last_login, created_at FROM user_accounts WHERE username = ?",
            (username,)
        )
        row = cursor.fetchone()
        
        if not row:
            return None
        
        return User(
            id=row[0],
            username=row[1],
            role=row[2],
            last_login=row[3],
            created_at=row[4]
        )
    finally:
        conn.close()

def get_student_profile(username: str) -> Optional[Student]:
    """
    Get a student profile by username
    
    Args:
        username: Student's username
        
    Returns:
        Student object if found, None otherwise
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT id, username, name, student_id, section, email, phone, created_at 
               FROM student_profiles WHERE username = ?""",
            (username,)
        )
        row = cursor.fetchone()
        
        if not row:
            return None
        
        return Student(
            id=row[0],
            username=row[1],
            name=row[2],
            student_id=row[3],
            section=row[4],
            email=row[5],
            phone=row[6],
            created_at=row[7]
        )
    finally:
        conn.close()

def get_professor_profile(username: str) -> Optional[Professor]:
    """
    Get a professor profile by username
    
    Args:
        username: Professor's username
        
    Returns:
        Professor object if found, None otherwise
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT id, username, name, department, email, phone, created_at 
               FROM professor_profiles WHERE username = ?""",
            (username,)
        )
        row = cursor.fetchone()
        
        if not row:
            return None
        
        return Professor(
            id=row[0],
            username=row[1],
            name=row[2],
            department=row[3],
            email=row[4],
            phone=row[5],
            created_at=row[6]
        )
    finally:
        conn.close()

def get_attendance_stats(username: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Get attendance statistics for a student
    
    Args:
        username: Student's username
        start_date: Optional start date filter (YYYY-MM-DD)
        end_date: Optional end date filter (YYYY-MM-DD)
        
    Returns:
        Dictionary with attendance statistics
    """
    query = """
    SELECT 
        COUNT(*) as total_classes,
        SUM(attended) as attended_classes,
        ROUND(SUM(attended) * 100.0 / COUNT(*), 1) as attendance_rate
    FROM class_attendance 
    WHERE student_name = ?
    """
    
    params = [username]
    
    if start_date:
        query += " AND class_date >= ?"
        params.append(start_date)
    
    if end_date:
        query += " AND class_date <= ?"
        params.append(end_date)
    
    df = execute_query_df(query, params)
    
    if df.empty:
        return {
            'total_classes': 0,
            'attended_classes': 0,
            'attendance_rate': 0.0
        }
    
    return {
        'total_classes': int(df['total_classes'].iloc[0]),
        'attended_classes': int(df['attended_classes'].iloc[0]),
        'attendance_rate': float(df['attendance_rate'].iloc[0])
    }

def get_subject_attendance(subject_name: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
    """
    Get attendance data for a specific subject
    
    Args:
        subject_name: Subject name
        start_date: Optional start date filter (YYYY-MM-DD)
        end_date: Optional end date filter (YYYY-MM-DD)
        
    Returns:
        DataFrame with attendance data
    """
    query = """
    SELECT ca.student_name, 
           COALESCE(sp.name, ca.student_name) as student_display_name,
           ca.class_date, 
           ca.attended
    FROM class_attendance ca
    LEFT JOIN student_profiles sp ON ca.student_name = sp.username
    WHERE ca.subject = ?
    """
    
    params = [subject_name]
    
    if start_date:
        query += " AND ca.class_date >= ?"
        params.append(start_date)
    
    if end_date:
        query += " AND ca.class_date <= ?"
        params.append(end_date)
    
    query += " ORDER BY ca.class_date, student_display_name"
    
    return execute_query_df(query, params)

def get_subjects_for_professor(professor_username: str) -> List[str]:
    """
    Get list of subjects assigned to a professor
    
    Args:
        professor_username: Professor's username
        
    Returns:
        List of subject names
    """
    # First try using the modern professor_subject_assignments table
    try:
        query = """
        SELECT s.subject_name as name
        FROM professor_subject_assignments psa
        JOIN subjects s ON psa.subject_id = s.subject_id
        WHERE psa.professor_username = ?
        ORDER BY s.subject_name
        """
        
        df = execute_query_df(query, (professor_username,))
        
        if not df.empty:
            return df['name'].tolist()
    except:
        pass
    
    # Fall back to the older teacher_subjects table
    try:
        query = """
        SELECT s.name
        FROM teacher_subjects ts
        JOIN subjects s ON ts.subject_id = s.id
        WHERE ts.teacher_name = ?
        ORDER BY s.name
        """
        
        df = execute_query_df(query, (professor_username,))
        
        if not df.empty:
            return df['name'].tolist()
    except:
        pass
    
    # Return empty list if no subjects found
    return []
