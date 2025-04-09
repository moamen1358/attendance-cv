import streamlit as st
import pandas as pd
import sqlite3
from database_utils import execute_query, execute_query_df
from datetime import datetime, timedelta
import plotly.express as px
import json
import numpy as np
from custom_table_view import CustomTableView
import professor_subject_assignment  # Import the module with assignment functionality
import sync_professor_tables
import os
import sys

# Constants
DATABASE_PATH = 'attendance_system.db'

def initialize_subjects_tables():
    """Create necessary tables for subject management if they don't exist"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # First check if the teacher_subjects table exists and has the right schema
        execute_query("PRAGMA table_info(teacher_subjects)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        # If the table exists but doesn't have the teacher_name column, we need to recreate it
        if columns and 'teacher_name' not in column_names:
            print("Existing teacher_subjects table has incorrect schema. Updating...")
            # Rename the old table
            cursor.execute("ALTER TABLE teacher_subjects RENAME TO teacher_subjects_old")
            # Create the new table with correct schema
            cursor.execute('''
            CREATE TABLE teacher_subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id INTEGER,
                teacher_name TEXT,
                FOREIGN KEY (subject_id) REFERENCES subjects(subject_id)
            )
            ''')
            # Try to migrate data if there's a column we can map
            try:
                if 'username' in column_names:
                    cursor.execute("INSERT INTO teacher_subjects (subject_id, teacher_name) SELECT subject_id, username FROM teacher_subjects_old")
                    print("Data migrated from old table using username column")
                elif 'name' in column_names:
                    cursor.execute("INSERT INTO teacher_subjects (subject_id, teacher_name) SELECT subject_id, name FROM teacher_subjects_old")
                    print("Data migrated from old table using name column")
                elif 'teacher' in column_names:
                    cursor.execute("INSERT INTO teacher_subjects (subject_id, teacher_name) SELECT subject_id, teacher FROM teacher_subjects_old")
                    print("Data migrated from old table using teacher column")
            except Exception as e:
                print(f"Failed to migrate data: {e}")
                
            # Drop the old table
            cursor.execute("DROP TABLE teacher_subjects_old")
        else:
            # Create the standard tables if they don't exist
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS subjects (
                subject_id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_name TEXT NOT NULL,
                course_code TEXT,
                credit_hours INTEGER DEFAULT 3,
                description TEXT
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS teacher_subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id INTEGER,
                teacher_name TEXT,
                FOREIGN KEY (subject_id) REFERENCES subjects(subject_id)
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS class_schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id INTEGER,
                subject TEXT,
                day TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                room TEXT,
                type TEXT DEFAULT 'lec',
                FOREIGN KEY (subject_id) REFERENCES subjects(subject_id)
            )
            ''')
        
        conn.commit()
        print("Subject management tables initialized successfully")
    except Exception as e:
        conn.rollback()
        print(f"Error initializing subject tables: {e}")
    finally:
        conn.close()

# Initialize tables at module import
initialize_subjects_tables()

def get_db_connection():
    """Get a connection to the SQLite database"""
    return sqlite3.connect(DATABASE_PATH)

def get_all_subjects():
    """
    Retrieve all subjects from the database with schema validation and column mapping.
    """
    # Check the actual schema to understand what columns are available
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("PRAGMA table_info(subjects)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"Available columns in subjects table: {columns}")
    except Exception as e:
        print(f"Error checking schema: {e}")
    finally:
        conn.close()
    
    # Determine the correct column names based on the actual schema
    id_column = 'subject_id' if 'subject_id' in columns else 'id'
    name_column = 'name' if 'name' in columns else 'subject_name'
    
    # Build a query using the detected column names
    query = f"SELECT * FROM subjects ORDER BY {name_column}"
    
    try:
        df = execute_query_df(query)
        
        # Ensure 'subject_id' column exists - most important fix!
        if 'subject_id' not in df.columns and 'id' in df.columns:
            df['subject_id'] = df['id']
            print("Added subject_id column mapped from id column")
        elif 'subject_id' not in df.columns:
            df['subject_id'] = range(1, len(df) + 1)  # Add sequential IDs
            print("Added missing subject_id column with sequential values")
            
        # Ensure 'name' column exists
        if 'name' not in df.columns and 'subject_name' in df.columns:
            df['name'] = df['subject_name']
            print("Added name column mapped from subject_name")
        elif 'name' not in df.columns:
            df['name'] = 'Unnamed Subject'
            print("Added missing name column with default values")
            
        # Add other missing columns with default values
        if 'course_code' not in df.columns:
            df['course_code'] = 'N/A'
            print("Added missing course_code column with default values")
            
        if 'credit_hours' not in df.columns:
            df['credit_hours'] = 3  # Default value
            print("Added missing credit_hours column with default values")
            
        # Ensure all expected columns exist
        print(f"Final DataFrame columns: {df.columns.tolist()}")
        
        return df
    except Exception as e:
        print(f"Error retrieving subjects: {e}")
        # Return empty DataFrame with expected columns to prevent further errors
        return pd.DataFrame(columns=['subject_id', 'name', 'course_code', 'credit_hours', 'description'])

def get_teachers():
    """Get all teachers from the database"""
    conn = get_db_connection()
    query = "SELECT username FROM user_accounts WHERE role = 'professor'"
    df = execute_query_df(query)
    conn.close()
    return df['username'].tolist()

def get_teacher_subjects(teacher):
    """Get subjects taught by a specific teacher with enhanced error handling"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # First check if professor_subject_assignments table exists - use this first if available
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='professor_subject_assignments'")
            if cursor.fetchone():
                # Check subjects table schema
                cursor.execute("PRAGMA table_info(subjects)")
                columns = [col[1] for col in cursor.fetchall()]
                
                # Determine which ID column to use
                id_column = 'subject_id' if 'subject_id' in columns else 'id'
                name_column = 'subject_name' if 'subject_name' in columns else 'name'
                
                # Use professor_subject_assignments table with corrected column names
                query = f"""
                SELECT s.* 
                FROM subjects s
                JOIN professor_subject_assignments psa ON s.{id_column} = psa.subject_id
                WHERE psa.professor_username = ?
                ORDER BY s.{name_column}
                """
                df = execute_query_df(query, (teacher,))
                
                # If we found subjects, return them
                if not df.empty:
                    return df
        except Exception as e:
            st.error(f"Error checking professor_subject_assignments: {e}")
        
        # Fall back to teacher_subjects if needed
        try:
            cursor.execute("PRAGMA table_info(teacher_subjects)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            # Debug information
            st.write(f"Available columns in teacher_subjects: {', '.join(column_names)}")
            
            # Check if the expected column exists
            if not columns or 'teacher_name' not in column_names:
                # Direct fix - create the table right here if it's missing or empty
                st.warning("Teacher column not found. Attempting to rebuild the table...")
                
                # Force recreate the table
                try:
                    cursor.execute("DROP TABLE IF EXISTS teacher_subjects")
                    cursor.execute("""
                    CREATE TABLE teacher_subjects (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        subject_id INTEGER,
                        teacher_name TEXT
                    )
                    """)
                    conn.commit()
                    
                    # Try again with the new table
                    cursor.execute("PRAGMA table_info(teacher_subjects)")
                    columns = cursor.fetchall()
                    column_names = [col[1] for col in columns]
                    
                    if 'teacher_name' not in column_names:
                        html_link = '<a href="/fix_db_tables" target="_blank">Open Database Repair Tool</a>'
                        st.error(f"Could not recreate teacher_subjects table with proper structure. {html_link}", unsafe_allow_html=True)
                        # Create a direct link to the fix tool as a button
                        if st.button("🔧 Open Database Repair Tool", type="primary"):
                            st.markdown("Opening repair tool in a new tab...")
                            js_code = f"""
                            <script>
                                window.open("/fix_db_tables", "_blank");
                            </script>
                            """
                            st.markdown(js_code, unsafe_allow_html=True)
                        
                        return pd.DataFrame(columns=['subject_id', 'subject_name', 'course_code', 'credit_hours', 'description'])
                except Exception as fix_error:
                    st.error(f"Error rebuilding table: {fix_error}")
                    return pd.DataFrame(columns=['subject_id', 'subject_name', 'course_code', 'credit_hours', 'description'])
            
            # Check subjects table schema
            cursor.execute("PRAGMA table_info(subjects)")
            subject_columns = [col[1] for col in cursor.fetchall()]
            
            # Determine which ID column to use in subjects table
            id_column = 'subject_id' if 'subject_id' in subject_columns else 'id'
            name_column = 'subject_name' if 'subject_name' in subject_columns else 'name'
            
            # Standard query with expected schema and dynamic column names
            query = f"""
            SELECT s.* 
            FROM subjects s
            JOIN teacher_subjects ts ON s.{id_column} = ts.subject_id
            WHERE ts.teacher_name = ?
            ORDER BY s.{name_column}
            """
            df = execute_query_df(query, (teacher,))
            
        except Exception as e:
            st.error(f"Error with teacher_subjects table: {e}")
            return pd.DataFrame(columns=['subject_id', 'subject_name', 'course_code', 'credit_hours', 'description'])
        
    except Exception as e:
        st.error(f"Database error in get_teacher_subjects: {e}")
        # Return empty DataFrame with expected structure
        df = pd.DataFrame(columns=['subject_id', 'subject_name', 'course_code', 'credit_hours', 'description'])
    finally:
        conn.close()
        
    return df

def get_subject_schedules(subject_id=None):
    """Get all schedules or for a specific subject with enhanced schema detection"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check the actual schema of the class_schedules table
    execute_query("PRAGMA table_info(class_schedules)")
    columns = [col[1] for col in cursor.fetchall()]
    
    # Determine if we have subject_id column or just subject column
    has_subject_id = 'subject_id' in columns
    has_subject = 'subject' in columns
    
    if subject_id is not None:
        if has_subject_id:
            # Use subject_id for filtering if available
            query = "SELECT * FROM class_schedules WHERE subject_id = ? ORDER BY day, start_time"
            df = execute_query_df(query, (subject_id,))
        elif has_subject:
            # Get subject name for filtering by name
            execute_query("SELECT subject_name FROM subjects WHERE subject_id = ?", (subject_id,))
            result = cursor.fetchone()
            if result:
                subject_name = result[0]
                query = "SELECT * FROM class_schedules WHERE subject = ? ORDER BY day, start_time"
                df = execute_query_df(query, (subject_name,))
            else:
                df = pd.DataFrame()  # Empty DataFrame if subject not found
        else:
            # No suitable column found
            st.warning("Schema issue: class_schedules table is missing required columns")
            df = pd.DataFrame()
    else:
        # For getting all schedules
        if has_subject_id and 'subject_name' in columns:
            query = """
            SELECT cs.*, s.subject_name 
            FROM class_schedules cs
            JOIN subjects s ON cs.subject_id = s.subject_id
            ORDER BY s.subject_name, cs.day, cs.start_time
            """
        elif has_subject:
            query = """
            SELECT * FROM class_schedules 
            ORDER BY subject, day, start_time
            """
        else:
            query = """
            SELECT * FROM class_schedules 
            ORDER BY day, start_time
            """
        df = execute_query_df(query)
    
    conn.close()
    return df

def add_new_subject(subject_data):
    """Add a new subject to the database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check what columns are available in the subjects table
        cursor.execute("PRAGMA table_info(subjects)")
        columns = {info[1] for info in cursor.fetchall()}
        
        # Check if course_code and credit_hours columns exist
        has_course_code = 'course_code' in columns
        has_credit_hours = 'credit_hours' in columns
        has_subject_name = 'subject_name' in columns
        has_name = 'name' in columns
        
        # Determine which column to use for subject name
        subject_name_col = 'subject_name' if has_subject_name else 'name'
        
        # Prepare query parts
        insert_cols = [subject_name_col, 'description']
        insert_vals = [subject_data['name'], subject_data['description']]
        
        # Add course_code if column exists
        if has_course_code:
            insert_cols.append('course_code')
            insert_vals.append(subject_data['code'])
        
        # Add credit_hours if column exists
        if has_credit_hours:
            insert_cols.append('credit_hours')
            insert_vals.append(subject_data['credits'])
        
        # Build the query
        query = f"INSERT INTO subjects ({', '.join(insert_cols)}) VALUES ({', '.join(['?'] * len(insert_cols))})"
        
        # Insert the subject
        cursor.execute(query, insert_vals)
        subject_id = cursor.lastrowid
        
        # Associate with teachers
        for teacher in subject_data['teachers']:
            cursor.execute(
                "INSERT INTO teacher_subjects (subject_id, teacher_name) VALUES (?, ?)",
                (subject_id, teacher)
            )
            
        conn.commit()
        return True, subject_id
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

def add_class_schedule(schedule_data):
    """Add a new class schedule with enhanced schema detection"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check the actual schema of the class_schedules table
        execute_query("PRAGMA table_info(class_schedules)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Determine columns to use based on schema
        has_subject_id = 'subject_id' in columns
        has_subject = 'subject' in columns
        
        if has_subject_id and has_subject:
            # If both columns exist, populate both
            subject_id = schedule_data['subject_id']
            
            # Get subject name from ID
            execute_query("SELECT subject_name FROM subjects WHERE subject_id = ?", (subject_id,))
            result = cursor.fetchone()
            subject_name = result[0] if result else "Unknown"
            
            cursor.execute(
                "INSERT INTO class_schedules (subject_id, subject, day, start_time, end_time, room, type) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    subject_id,
                    subject_name,
                    schedule_data['day'], 
                    schedule_data['start_time'], 
                    schedule_data['end_time'], 
                    schedule_data['room'],
                    schedule_data['type']
                )
            )
        elif has_subject_id:
            cursor.execute(
                "INSERT INTO class_schedules (subject_id, day, start_time, end_time, room, type) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    schedule_data['subject_id'], 
                    schedule_data['day'], 
                    schedule_data['start_time'], 
                    schedule_data['end_time'], 
                    schedule_data['room'],
                    schedule_data['type']
                )
            )
        elif has_subject:
            # Get subject name from ID
            execute_query("SELECT subject_name FROM subjects WHERE subject_id = ?", (schedule_data['subject_id'],))
            result = cursor.fetchone()
            subject_name = result[0] if result else "Unknown"
            
            cursor.execute(
                "INSERT INTO class_schedules (subject, day, start_time, end_time, room, type) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    subject_name,
                    schedule_data['day'], 
                    schedule_data['start_time'], 
                    schedule_data['end_time'], 
                    schedule_data['room'],
                    schedule_data['type']
                )
            )
        else:
            raise Exception("Schema issue: class_schedules table is missing required columns")
        
        conn.commit()
        return True, ""
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

def delete_subject(subject_id):
    """Delete a subject and its related records"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # First delete the schedules
        cursor.execute("DELETE FROM class_schedules WHERE subject_id = ?", (subject_id,))
        
        # Delete teacher associations
        cursor.execute("DELETE FROM teacher_subjects WHERE subject_id = ?", (subject_id,))
        
        # Delete the subject
        cursor.execute("DELETE FROM subjects WHERE subject_id = ?", (subject_id,))
        
        conn.commit()
        return True, ""
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

def delete_schedule(schedule_id):
    """Delete a class schedule"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM class_schedules WHERE id = ?", (schedule_id,))
        conn.commit()
        return True, ""
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

def get_common_subject_names():
    """Return a list of common subject names for suggestions"""
    return [
        "Introduction to Computer Science",
        "Data Structures and Algorithms",
        "Database Systems",
        "Operating Systems",
        "Computer Networks",
        "Web Development",
        "Mobile App Development",
        "Machine Learning",
        "Artificial Intelligence",
        "Software Engineering",
        "Computer Architecture",
        "Discrete Mathematics",
        "Calculus I",
        "Calculus II",
        "Linear Algebra",
        "Statistics",
        "Physics I",
        "Physics II",
        "Chemistry",
        "Biology"
    ]

def get_common_course_codes():
    """Return a list of common course code patterns"""
    return [
        "CS101", "CS201", "CS301", "CS401",
        "IT101", "IT201", "IT301", "IT401",
        "MATH101", "MATH201", "MATH301",
        "PHYS101", "PHYS201",
        "CHEM101", "BIO101"
    ]

def show_subject_management():
    st.title("Subject & Schedule Management")
    
    # Add custom CSS for this page - Updated for a more professional look
    st.markdown("""
    <style>
    .css-18e3th9 {
        padding-top: 1rem;
    }
    
    /* Professional tab styling */
    [data-testid="stTabs"] {
        background-color: transparent !important;
    }
    div[role="tablist"] {
        background-color: transparent !important;
        border-bottom: 1px solid #e0e0e0;
        padding-bottom: 0 !important;
        padding-left: 0 !important;
        margin-bottom: 20px;
    }
    div[role="tab"] {
        background-color: transparent !important;
        border: none !important;
        padding: 10px 20px !important;
        margin-right: 5px !important;
        font-weight: 500 !important;
        color: #5f6368 !important;
        position: relative !important;
        transition: color 0.2s ease !important;
    }
    div[role="tab"][aria-selected="true"] {
        background-color: transparent !important;
        color: #1565C0 !important;
        font-weight: 600 !important;
        border-bottom: 3px solid #1565C0 !important;
        box-shadow: none !important;
    }
    div[role="tab"]:hover {
        background-color: rgba(21, 101, 192, 0.05) !important;
        color: #1565C0 !important;
    }
    
    /* Professional subject card styling */
    .subject-card {
        padding: 20px;
        border-radius: 8px;
        background-color: white;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.12);
        margin-bottom: 16px;
        transition: box-shadow 0.2s ease-in-out;
        border-left: 4px solid #1565C0;
    }
    .subject-card:hover {
        box-shadow: 0 3px 6px rgba(0,0,0,0.10), 0 3px 6px rgba(0,0,0,0.15);
    }
    
    /* Improved heading styles */
    .subject-title {
        font-size: 18px;
        font-weight: 600;
        color: #202124;
        margin-bottom: 8px;
    }
    
    /* Clean details styling */
    .subject-details {
        display: flex;
        gap: 16px;
        color: #5f6368;
        margin-bottom: 12px;
        font-size: 14px;
    }
    .subject-detail-item {
        display: flex;
        align-items: center;
        gap: 5px;
    }
    
    /* Instructor list styling */
    .instructor-list {
        list-style-type: none;
        padding-left: 0;
        margin-top: 10px;
        margin-bottom: 5px;
    }
    .instructor-item {
        display: flex;
        align-items: center;
        margin-bottom: 5px;
        font-size: 14px;
    }
    .instructor-icon {
        width: 24px;
        height: 24px;
        border-radius: 50%;
        background-color: #E8F0FE;
        color: #1565C0;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 8px;
        font-size: 12px;
        font-weight: 600;
    }
    
    /* Actions section styling */
    .actions-section {
        margin-top: 10px;
        display: flex;
        gap: 8px;
        justify-content: flex-end;
    }
    .action-button {
        padding: 5px 10px;
        border-radius: 4px;
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
        text-align: center;
    }
    .view-button {
        background-color: #E8F0FE;
        color: #1565C0;
    }
    .view-button:hover {
        background-color: #D2E3FC;
    }
    .delete-button {
        background-color: #FEE8E6;
        color: #D93025;
    }
    .delete-button:hover {
        background-color: #FCCFC7;
    }
    
    /* Enhanced schedule items */
    .schedule-item {
        padding: 12px;
        border-left: 3px solid #4285F4;
        background-color: #F8F9FA;
        margin-bottom: 8px;
        border-radius: 0 4px 4px 0;
    }
    .schedule-header {
        font-weight: 600;
        margin-bottom: 10px;
        color: #1A73E8;
        padding-bottom: 5px;
        border-bottom: 1px solid #E8EAED;
    }
    </style>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📚 View Subjects", 
        "➕ Add Subject", 
        "🗓️ Manage Schedule", 
        "📊 Subject Analytics",
        "👨‍🏫 Professor Assignments"
    ])
    
    # Tab 1: View Subjects - UPDATED FOR PROFESSIONAL LOOK
    with tab1:
        st.header("Subject List")
        
        # Teacher filter
        teachers = ["All"] + get_teachers()
        selected_teacher = st.selectbox("Filter by Teacher:", teachers, index=0)
        
        # Get subjects based on filter
        if selected_teacher == "All":
            subjects_df = get_all_subjects()
        else:
            subjects_df = get_teacher_subjects(selected_teacher)
        
        if subjects_df.empty:
            st.info("No subjects found. Add some subjects in the 'Add Subject' tab.")
        else:
            # Display subjects in a more professional layout
            for _, subject in subjects_df.iterrows():
                with st.container():
                    # Safely access columns with fallback values
                    subject_name = subject['name'] if 'name' in subject else subject.get('subject_name', 'Unnamed Subject')
                    course_code = subject.get('course_code', 'N/A')
                    credit_hours = subject.get('credit_hours', 3)
                    subject_id = subject.get('subject_id', subject.get('id', 0))
                    
                    # Generate a professional card using HTML/CSS
                    st.markdown(f"""
                    <div class="subject-card">
                        <div class="subject-title">{subject_name}</div>
                        <div class="subject-details">
                            <div class="subject-detail-item">
                                <span>📝</span>
                                <span>{course_code}</span>
                            </div>
                            <div class="subject-detail-item">
                                <span>🕒</span>
                                <span>{credit_hours} Credit Hours</span>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Get teachers for this subject
                    conn = get_db_connection()
                    teachers_query = """
                    SELECT DISTINCT teacher_name FROM teacher_subjects 
                    WHERE subject_id = ?
                    ORDER BY teacher_name
                    """
                    teachers_df = execute_query_df(teachers_query, (subject_id,))
                    conn.close()
                    
                    # Display instructors with professional styling
                    st.markdown("<h4 style='margin-bottom:5px; font-size:15px; color:#202124;'>Instructors</h4>", unsafe_allow_html=True)
                    
                    if teachers_df.empty:
                        st.markdown("<div style='color:#5f6368; font-style:italic; font-size:13px;'>No instructors assigned</div>", unsafe_allow_html=True)
                    else:
                        # Remove duplicate entries just to be double-safe
                        teachers_df = teachers_df.drop_duplicates()
                        
                        st.markdown("<ul class='instructor-list'>", unsafe_allow_html=True)
                        
                        for _, teacher in teachers_df.iterrows():
                            teacher_name = teacher['teacher_name']
                            initial = teacher_name[0].upper() if teacher_name else "?"
                            st.markdown(f"""
                            <li class="instructor-item">
                                <div class="instructor-icon">{initial}</div>
                                {teacher_name}
                            </li>
                            """, unsafe_allow_html=True)
                        
                        st.markdown("</ul>", unsafe_allow_html=True)
                    
                    # Action buttons
                    st.markdown(f"""
                    <div class="actions-section">
                        <div class="action-button view-button" onclick="
                            document.getElementById('view_btn_{subject_id}').click();">
                            View Schedule
                        </div>
                        <div class="action-button delete-button" onclick="
                            document.getElementById('delete_btn_{subject_id}').click();">
                            Delete
                        </div>
                    </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Hidden buttons that JavaScript will click
                    col1, col2 = st.columns([1,1])
                    with col1:
                        if st.button("View Schedule", key=f"view_btn_{subject_id}", help="View class schedule for this subject"):
                            st.session_state.view_schedule_id = subject_id
                            st.session_state.view_schedule_name = subject_name
                    
                    with col2:
                        if st.button("Delete Subject", key=f"delete_btn_{subject_id}"):
                            st.session_state.confirm_delete = subject_id
                
                # Show confirmation dialog for deletion with more professional styling
                if 'confirm_delete' in st.session_state and st.session_state.confirm_delete == subject_id:
                    with st.container():
                        st.markdown("""
                        <div style="padding: 15px; border-radius: 8px; background-color: #FEF7F6; border-left: 4px solid #EA4335; margin: 10px 0 20px 0;">
                            <h4 style="margin-top: 0; color: #B31412;">Confirm Deletion</h4>
                            <p style="margin-bottom: 10px;">Are you sure you want to delete this subject? This will also delete all associated schedules.</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        col1, col2 = st.columns([1, 1])
                        with col1:
                            if st.button("Yes, Delete", key=f"confirm_{subject_id}", type="primary"):
                                success, error = delete_subject(subject_id)
                                if success:
                                    st.success(f"Subject deleted successfully!")
                                    del st.session_state.confirm_delete
                                    st.rerun()
                                else:
                                    st.error(f"Error deleting subject: {error}")
                        with col2:
                            if st.button("Cancel", key=f"cancel_{subject_id}"):
                                del st.session_state.confirm_delete
                                st.rerun()
                
                # Show schedule if view button was clicked - with improved styling
                if 'view_schedule_id' in st.session_state and st.session_state.view_schedule_id == subject_id:
                    schedules = get_subject_schedules(subject_id)
                    
                    st.markdown(f"""
                    <h3 style="margin-top:20px; font-size:18px; color:#1565C0; display:flex; align-items:center; gap:8px;">
                        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                            <line x1="16" y1="2" x2="16" y2="6"></line>
                            <line x1="8" y1="2" x2="8" y2="6"></line>
                            <line x1="3" y1="10" x2="21" y2="10"></line>
                        </svg>
                        Schedule for {st.session_state.view_schedule_name}
                    </h3>
                    """, unsafe_allow_html=True)
                    
                    if schedules.empty:
                        st.info("No schedules found for this subject.")
                    else:
                        # Group by day with professional styling
                        days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                        schedules['day_order'] = schedules['day'].apply(lambda x: days_order.index(x) if x in days_order else 99)
                        schedules = schedules.sort_values('day_order')
                        
                        # Create a tabular schedule with improved styling
                        day_groups = schedules.groupby('day')
                        
                        for day, group in day_groups:
                            st.markdown(f"<div class='schedule-header'>{day}</div>", unsafe_allow_html=True)
                            
                            for _, schedule in group.iterrows():
                                st.markdown(f"""
                                <div class="schedule-item">
                                    <div style="display: flex; justify-content: space-between; align-items: center;">
                                        <div>
                                            <span style="font-weight:500;">⏰ {schedule['start_time']} - {schedule['end_time']}</span>
                                        </div>
                                        <div style="display:flex; gap:15px;">
                                            <span style="color:#5f6368;">🏫 {schedule['room']}</span>
                                            <span style="color:#5f6368; text-transform:capitalize;">📝 {schedule['type']}</span>
                                        </div>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                    
                    # Close button with better styling
                    if st.button("Close Schedule", key="close_schedule", type="primary"):
                        del st.session_state.view_schedule_id
                        del st.session_state.view_schedule_name
                        st.rerun()

    # Tab 2: Add Subject
    with tab2:
        st.header("Add New Subject")
        # Existing code for Add Subject tab...

    # Tab 3: Manage Schedule
    with tab3:
        st.header("Manage Class Schedules")
        # Existing code for Manage Schedule tab...

    # Tab 4: Subject Analytics
    with tab4:
        st.header("Subject Analytics")
        # Existing code for Subject Analytics tab...

    # Tab 5: Professor Assignments
    with tab5:
        professor_subject_assignment.show_professor_assignments()

if __name__ == "__main__":
    show_subject_management()

def update_class_schedules_schema():
    """Update class_schedules table schema if needed"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if table exists
        execute_query("SELECT name FROM sqlite_master WHERE type='table' AND name='class_schedules'")
        table_exists = cursor.fetchone() is not None
        
        if table_exists:
            # Check current columns
            execute_query("PRAGMA table_info(class_schedules)")
            columns = [col[1] for col in cursor.fetchall()]
            
            # Check if we need to add subject_id column
            if 'subject_id' not in columns:
                cursor.execute("ALTER TABLE class_schedules ADD COLUMN subject_id INTEGER")
                
                # If we have subject column and subjects table, try to update subject_id values
                if 'subject' in columns:
                    cursor.execute("""
                    UPDATE class_schedules
                    SET subject_id = (
                        SELECT subject_id FROM subjects 
                        WHERE subjects.subject_name = class_schedules.subject
                        LIMIT 1
                    )
                    WHERE subject IS NOT NULL
                    """)
                
                conn.commit()
                print("Added subject_id column to class_schedules table")
            
            # Check if we need to add subject column
            if 'subject' not in columns:
                cursor.execute("ALTER TABLE class_schedules ADD COLUMN subject TEXT")
                
                # If we have subject_id column and subjects table, try to update subject values
                if 'subject_id' in columns:
                    cursor.execute("""
                    UPDATE class_schedules
                    SET subject = (
                        SELECT subject_name FROM subjects 
                        WHERE subjects.subject_id = class_schedules.subject_id
                        LIMIT 1
                    )
                    WHERE subject_id IS NOT NULL
                    """)
                
                conn.commit()
                print("Added subject column to class_schedules table")
        else:
            # Create table with both columns
            cursor.execute('''
            CREATE TABLE class_schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id INTEGER,
                subject TEXT,
                day TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                room TEXT,
                type TEXT DEFAULT 'lec',
                FOREIGN KEY (subject_id) REFERENCES subjects(subject_id)
            )
            ''')
            conn.commit()
            print("Created class_schedules table with all required columns")
            
    except Exception as e:
        conn.rollback()
        print(f"Error updating schema: {e}")
    finally:
        conn.close()

# Run schema update at module import
update_class_schedules_schema()
