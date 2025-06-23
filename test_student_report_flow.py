#!/usr/bin/env python3
"""Test script to debug the student report schedule issue"""

import pandas as pd
import sqlite3
from datetime import datetime

DATABASE_PATH = 'attendance_system.db'

def get_db_connection():
    """Get a connection to the SQLite database"""
    return sqlite3.connect(DATABASE_PATH)

def execute_query_df_simple(query, params=None):
    """Simple version of execute_query_df without streamlit dependencies"""
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        print(f"Executing query: {query}")
        print(f"With params: {params}")
        df = pd.read_sql_query(query, conn, params=params)
        print(f"Query result: {len(df)} rows, columns: {df.columns.tolist()}")
        return df
    except Exception as e:
        print(f"Error executing query: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def get_secure_student_data_simple():
    """Simple version of get_secure_student_data"""
    current_user = '2024005'  # Hala's username
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT s.name, s.roll_number, s.department, s.section, s.year
            FROM users_enhanced u
            JOIN students_enhanced s ON u.linked_id = s.student_id
            WHERE u.username = ? AND u.role = 'student'
        """, (current_user,))
        
        result = cursor.fetchone()
        if result:
            return {
                'student_name': result[0],
                'student_id': result[1] or 'Unknown',
                'section': result[3] or 'Unknown',
                'department': result[2] or 'Unknown',
                'year': result[4] or 'Unknown'
            }
        else:
            return {
                'student_name': current_user,
                'student_id': 'Unknown',
                'section': 'Unknown'
            }
    except Exception as e:
        print(f"Error getting student data: {e}")
        return {
            'student_name': current_user,
            'student_id': 'Unknown',
            'section': 'Unknown'
        }
    finally:
        conn.close()

def get_schedule_for_day_simple(day_name, student_name=None):
    """Simple version of get_schedule_for_day"""
    if student_name:
        # Get schedule only for subjects the student is enrolled in
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
        JOIN student_enrollments_enhanced se ON s.subject_id = se.subject_id
        JOIN students_enhanced st ON se.student_id = st.student_id
        WHERE cs.day_of_week = ? 
          AND st.name = ?
          AND se.status = 'active'
          AND cs.status = 'active'
          AND s.subject_name != ''
        ORDER BY cs.start_time
        """
        df = execute_query_df_simple(query, (day_name, student_name))
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
        df = execute_query_df_simple(query, (day_name,))
    
    return df

def test_complete_flow():
    """Test the complete flow from student report page"""
    print("=== Testing Complete Student Report Flow ===")
    
    # 1. Get current day
    day_name = datetime.now().strftime('%A')
    print(f"1. Current day: {day_name}")
    
    # 2. Get student data
    print("\n2. Getting student data...")
    student_data = get_secure_student_data_simple()
    student_name = student_data['student_name']
    student_id = student_data['student_id']
    section = student_data['section']
    print(f"   Student: {student_name}")
    print(f"   ID: {student_id}")
    print(f"   Section: {section}")
    
    # 3. Get schedule for today
    print(f"\n3. Getting schedule for {day_name}...")
    schedule_df = get_schedule_for_day_simple(day_name, student_name)
    print(f"   Schedule result: {len(schedule_df)} classes")
    
    if schedule_df.empty:
        print("   ❌ Schedule is EMPTY!")
        print("   This is why 'No classes scheduled' is displayed")
    else:
        print("   ✅ Schedule found:")
        for _, row in schedule_df.iterrows():
            print(f"      - {row['subject']}: {row['start_time']} - {row['end_time']}")
    
    # 4. Test without student filter (all classes)
    print(f"\n4. Testing schedule without student filter...")
    all_schedule_df = get_schedule_for_day_simple(day_name, None)
    print(f"   All classes for {day_name}: {len(all_schedule_df)} classes")
    
    return schedule_df

if __name__ == "__main__":
    result = test_complete_flow()
