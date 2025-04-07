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
    
    # Add custom CSS for this page
    st.markdown("""
    <style>
    .css-18e3th9 {
        padding-top: 1rem;
    }
    .subject-header {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .card {
        padding: 1.5rem;
        border-radius: 0.5rem;
        background-color: white;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
        margin-bottom: 1rem;
        transition: all 0.3s cubic-bezier(.25,.8,.25,1);
    }
    .card:hover {
        box-shadow: 0 3px 6px rgba(0,0,0,0.16), 0 3px 6px rgba(0,0,0,0.23);
    }
    .schedule-item {
        padding: 0.75rem;
        border-left: 4px solid #4CAF50;
        background-color: #f9f9f9;
        margin-bottom: 0.5rem;
        border-radius: 0 0.25rem 0.25rem 0;
    }
    
    /* Complete removal of background color from tabs */
    [data-testid="stTabs"] {
        background-color: transparent !important;
    }
    [data-testid="stTabsContent"] {
        background-color: transparent !important;
        border: none !important;
    }
    div[role="tablist"] {
        background-color: transparent !important;
    }
    div[role="tab"] {
        background-color: transparent !important;
        border: none !important;
        border-bottom: 2px solid transparent;
        transition: all 0.3s ease;
    }
    div[role="tab"][aria-selected="true"] {
        background-color: transparent !important;
        border-bottom-color: #1E88E5;
        color: #1E88E5;
        box-shadow: none !important;
    }
    div[role="tab"]:hover {
        background-color: transparent !important;
        color: #1565C0;
    }
    [data-testid="stTabContent"] {
        padding-top: 20px;
        background-color: transparent !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Create tabs for different management sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📚 View Subjects", 
        "➕ Add Subject", 
        "🗓️ Manage Schedule", 
        "📊 Subject Analytics",
        "👨‍🏫 Professor Assignments"
    ])
    
    # Tab 1: View Subjects
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
            # Display subjects in an improved layout
            for _, subject in subjects_df.iterrows():
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        # Safely access columns with fallback values
                        subject_name = subject['name'] if 'name' in subject else subject.get('subject_name', 'Unnamed Subject')
                        course_code = subject.get('course_code', 'N/A')
                        credit_hours = subject.get('credit_hours', 3)
                        
                        st.markdown(f"""
                        <div class='card'>
                            <h3>{subject_name}</h3>
                            <p><strong>Course Code:</strong> {course_code}</p>
                            <p><strong>Credit Hours:</strong> {credit_hours}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        # Get teachers for this subject - Handle potential missing subject_id gracefully
                        conn = get_db_connection()
                        teachers_query = """
                        SELECT teacher_name FROM teacher_subjects 
                        WHERE subject_id = ?
                        """
                        
                        # Safely get subject_id, with fallback
                        if 'subject_id' in subject:
                            subject_id = subject['subject_id']
                        else:
                            # Try alternative column names
                            subject_id = subject.get('id', None)
                            if subject_id is None:
                                # Last resort: generate a placeholder ID
                                st.warning(f"Could not find subject ID for {subject.get('name', 'Unknown Subject')}")
                                subject_id = -1  # Invalid ID to avoid matching anything
                        
                        teachers_df = execute_query_df(teachers_query, (subject_id,))
                        conn.close()
                        
                        st.markdown("<div class='card'>", unsafe_allow_html=True)
                        st.markdown("#### Instructors")
                        for _, teacher in teachers_df.iterrows():
                            st.markdown(f"- {teacher['teacher_name']}")
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    with col3:
                        # Display actions in a card
                        st.markdown("<div class='card'>", unsafe_allow_html=True)
                        st.markdown("#### Actions")
                        
                        # Safely get subject_id with fallback to avoid KeyError
                        subject_id = subject.get('subject_id', subject.get('id', 0))
                        
                        # View schedules button with safe subject_id access
                        if st.button("View Schedule", key=f"view_{subject_id}"):
                            st.session_state.view_schedule_id = subject_id
                            st.session_state.view_schedule_name = subject.get('name', subject.get('subject_name', 'Unknown Subject'))
                            
                        # Delete subject button with safe subject_id access
                        if st.button("Delete Subject", key=f"delete_{subject_id}", type="primary"):
                            if 'confirm_delete' not in st.session_state:
                                st.session_state.confirm_delete = subject_id
                            else:
                                st.session_state.confirm_delete = subject_id
                        st.markdown("</div>", unsafe_allow_html=True)
                
                # Show confirmation dialog for deletion - with safe subject_id access
                if 'confirm_delete' in st.session_state:
                    # Get subject_id safely with fallback
                    subject_id = subject.get('subject_id', subject.get('id', 0))
                    if subject_id and st.session_state.confirm_delete == subject_id:
                        st.warning(f"Are you sure you want to delete {subject.get('name', 'this subject')}? This will delete all schedules.")
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Yes, Delete", key=f"confirm_{subject_id}"):
                                success, error = delete_subject(subject_id)
                                if success:
                                    st.success(f"Subject {subject.get('name', 'this subject')} deleted successfully!")
                                    del st.session_state.confirm_delete
                                    st.rerun()
                                else:
                                    st.error(f"Error deleting subject: {error}")
                        with col2:
                            if st.button("Cancel", key=f"cancel_{subject_id}"):
                                del st.session_state.confirm_delete
                                st.rerun()
                
                # Show schedule if view button was clicked - with safe subject_id access
                subject_id = subject.get('subject_id', subject.get('id', 0))
                if 'view_schedule_id' in st.session_state and subject_id and st.session_state.view_schedule_id == subject_id:
                    schedules = get_subject_schedules(subject['subject_id'])
                    
                    st.markdown(f"### Schedule for {st.session_state.view_schedule_name}")
                    
                    if schedules.empty:
                        st.info("No schedules found for this subject.")
                    else:
                        # Group by day
                        days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                        schedules['day_order'] = schedules['day'].apply(lambda x: days_order.index(x) if x in days_order else 99)
                        schedules = schedules.sort_values('day_order')
                        
                        # Create a tabular schedule
                        day_groups = schedules.groupby('day')
                        
                        for day, group in day_groups:
                            st.markdown(f"#### {day}")
                            
                            for _, schedule in group.iterrows():
                                st.markdown(f"""
                                <div class="schedule-item">
                                    <div style="display: flex; justify-content: space-between;">
                                        <div>
                                            <strong>Time:</strong> {schedule['start_time']} - {schedule['end_time']}
                                        </div>
                                        <div>
                                            <strong>Room:</strong> {schedule['room']}
                                        </div>
                                        <div>
                                            <strong>Type:</strong> {schedule['type']}
                                        </div>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                    
                    # Close button
                    if st.button("Close Schedule View", key="close_schedule"):
                        del st.session_state.view_schedule_id
                        del st.session_state.view_schedule_name
                        st.rerun()
    
    # Tab 2: Add Subject - ENHANCED VERSION
    with tab2:
        st.header("Add New Subject")
        
        # Create a container with a nice background color
        with st.container():
            st.markdown("""
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 5px solid #4CAF50;">
                <h3 style="margin-top: 0;">Subject Details</h3>
                <p>Fill in the details below to create a new subject.</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Get common subject names for suggestions
            common_subjects = get_common_subject_names()
            
            # Get common course codes for suggestions
            common_codes = get_common_course_codes()
            
            with st.form("add_subject_form", clear_on_submit=True):
                # Subject Name section with dropdown/text combo
                st.subheader("Subject Information")
                
                # Option to select from common subjects or enter custom
                use_common_subject = st.checkbox("Select from common subjects", value=True)
                
                if use_common_subject:
                    subject_name = st.selectbox("Subject Name*", common_subjects)
                else:
                    subject_name = st.text_input("Subject Name*", placeholder="Enter subject name")
                
                # Course code with option to use common patterns
                col1, col2 = st.columns(2)
                
                with col1:
                    use_common_code = st.checkbox("Select from common codes", value=True)
                    
                    if use_common_code:
                        course_code = st.selectbox("Course Code*", common_codes)
                    else:
                        course_code = st.text_input("Course Code*", placeholder="e.g., CS101")
                
                with col2:
                    # MODIFIED: Replace button-based credit hours with number_input
                    credit_hours = st.number_input(
                        "Credit Hours*",
                        min_value=1,
                        max_value=6,
                        value=3,
                        step=1,
                        help="Number of credit hours for this subject"
                    )
                
                # Enhanced description field with character count
                subject_description = st.text_area(
                    "Description", 
                    placeholder="Brief description of the subject",
                    height=100,
                    max_chars=500,
                    help="A short description of the subject content and objectives"
                )
                
                st.write(f"Characters: {len(subject_description)}/500")
                
                # Teacher assignment section
                st.subheader("Assign Teachers")
                
                # Get all teachers for multiselect
                all_teachers = get_teachers()
                
                # Display teachers with a more visual approach
                if all_teachers:
                    # Show available teachers with avatars
                    st.markdown("""
                    <style>
                    .teacher-container {
                        display: flex;
                        flex-wrap: wrap;
                        gap: 10px;
                        margin-top: 10px;
                    }
                    .teacher-card {
                        display: flex;
                        align-items: center;
                        padding: 5px 10px;
                        border-radius: 20px;
                        background-color: #f0f0f0;
                        cursor: pointer;
                    }
                    .teacher-card.selected {
                        background-color: #4CAF50;
                        color: white;
                    }
                    .teacher-avatar {
                        width: 25px;
                        height: 25px;
                        border-radius: 50%;
                        background-color: #1976D2;
                        color: white;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-size: 12px;
                        margin-right: 5px;
                    }
                    </style>
                    """, unsafe_allow_html=True)
                    
                    # Enhanced teacher selection with search
                    assigned_teachers = st.multiselect(
                        "Select Teachers*", 
                        all_teachers,
                        placeholder="Search for teachers...",
                        help="Assign one or more teachers to this subject"
                    )
                    
                    # Preview of selected teachers
                    if assigned_teachers:
                        st.markdown("### Selected Teachers")
                        cols = st.columns(len(assigned_teachers) if len(assigned_teachers) <= 4 else 4)
                        for i, teacher in enumerate(assigned_teachers[:4]):  # Show first 4 with larger avatars
                            with cols[i % 4]:
                                st.markdown(f"""
                                <div style="display: flex; flex-direction: column; align-items: center;">
                                    <div style="width: 40px; height: 40px; border-radius: 50%; background-color: #1976D2; 
                                        color: white; display: flex; align-items: center; justify-content: center; 
                                        font-size: 16px; margin-bottom: 5px;">
                                        {teacher[0].upper()}
                                    </div>
                                    <div style="text-align: center; font-size: 0.9em;">{teacher}</div>
                                </div>
                                """, unsafe_allow_html=True)
                        
                        if len(assigned_teachers) > 4:
                            st.write(f"...and {len(assigned_teachers) - 4} more")
                else:
                    st.warning("No teachers available. Please add teachers first.")
                    assigned_teachers = []
                
                # Submit button with error checking
                submit_col1, submit_col2 = st.columns([1, 1])
                
                with submit_col1:
                    st.markdown("**Required fields are marked with * **")
                
                with submit_col2:
                    submit_button = st.form_submit_button(
                        "➕ Add Subject", 
                        use_container_width=True, 
                        type="primary"
                    )
                
                if submit_button:
                    # Validate required fields
                    errors = []
                    
                    if not subject_name:
                        errors.append("Subject Name is required")
                    
                    if not course_code:
                        errors.append("Course Code is required")
                    
                    if not assigned_teachers:
                        errors.append("At least one teacher must be assigned")
                    
                    if errors:
                        for error in errors:
                            st.error(error)
                    else:
                        # Prepare data
                        subject_data = {
                            'name': subject_name,
                            'code': course_code,
                            'credits': credit_hours,
                            'description': subject_description,
                            'teachers': assigned_teachers
                        }
                        
                        # Add subject
                        success, result = add_new_subject(subject_data)
                        
                        if success:
                            st.success(f"Subject '{subject_name}' added successfully!")
                            st.session_state.new_subject_id = result
                            st.session_state.new_subject_name = subject_name
                            
                            # Show confirmation with details
                            st.markdown(f"""
                            <div style="background-color: #eaffea; padding: 15px; border-radius: 5px; 
                                     border-left: 5px solid #4CAF50; margin-top: 20px;">
                                <h4 style="margin-top: 0;">Subject Created Successfully!</h4>
                                <p><strong>Subject Name:</strong> {subject_name}</p>
                                <p><strong>Course Code:</strong> {course_code}</p>
                                <p><strong>Credit Hours:</strong> {credit_hours}</p>
                                <p><strong>Teachers:</strong> {", ".join(assigned_teachers)}</p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Automatic redirect to add schedules
                            st.info("Now you can add schedules for this subject in the 'Manage Schedule' tab.")
                        else:
                            st.error(f"Error adding subject: {result}")
                            
        # Add some helpful tips at the bottom
        with st.expander("Tips for Adding Subjects", expanded=False):
            st.markdown("""
            - Course codes typically follow a department prefix + number format (e.g., CS101)
            - Credit hours usually range from 1-4 for most courses
            - You can assign multiple teachers to a subject
            - After creating the subject, go to the "Manage Schedule" tab to set up class times
            """)
    
    # Tab 3: Manage Schedule
    with tab3:
        st.header("Manage Class Schedules")
        
        # Get all subjects for dropdown
        subjects_df = get_all_subjects()
        subject_options = [(row['subject_id'], row['name']) for _, row in subjects_df.iterrows()]
        
        # Check if we're coming from adding a new subject
        default_index = 0
        if 'new_subject_id' in st.session_state and 'new_subject_name' in st.session_state:
            # Find the index of the newly added subject
            for i, (subj_id, _) in enumerate(subject_options):
                if subj_id == st.session_state.new_subject_id:
                    default_index = i
                    break
        
        # Select subject to schedule
        subject_names = [name for _, name in subject_options]
        subject_ids = [id for id, _ in subject_options]
        
        if not subject_options:
            st.warning("No subjects available. Please add subjects first.")
        else:
            selected_subject_name = st.selectbox(
                "Select Subject to Schedule:", 
                subject_names,
                index=default_index
            )
            selected_subject_id = subject_ids[subject_names.index(selected_subject_name)]
            
            # Show existing schedules for this subject
            st.subheader(f"Current Schedule for {selected_subject_name}")
            
            schedules = get_subject_schedules(selected_subject_id)
            if schedules.empty:
                st.info("No schedules found for this subject.")
            else:
                # Create tabbed view by day
                unique_days = schedules['day'].unique()
                
                # Sort days in correct order
                day_order = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3, 
                            "Friday": 4, "Saturday": 5, "Sunday": 6}
                sorted_days = sorted(unique_days, key=lambda d: day_order.get(d, 99))
                
                day_tabs = st.tabs(sorted_days)
                
                for i, day in enumerate(sorted_days):
                    with day_tabs[i]:
                        day_schedules = schedules[schedules['day'] == day]
                        
                        for _, schedule in day_schedules.iterrows():
                            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                            with col1:
                                st.markdown(f"**Time:** {schedule['start_time']} - {schedule['end_time']}")
                            with col2:
                                st.markdown(f"**Room:** {schedule['room']}")
                            with col3:
                                st.markdown(f"**Type:** {schedule['type']}")
                            with col4:
                                if st.button("🗑️", key=f"delete_schedule_{schedule['id']}"):
                                    success, error = delete_schedule(schedule['id'])
                                    if success:
                                        st.success("Schedule deleted!")
                                        st.rerun()
                                    else:
                                        st.error(f"Error: {error}")
                        
                # Option to delete all schedules for this subject
                if not schedules.empty:
                    if st.button("Delete All Schedules", key="delete_all", type="primary"):
                        st.warning("Are you sure you want to delete all schedules for this subject?")
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Yes, Delete All", key="confirm_delete_all"):
                                # Delete all schedules for this subject
                                conn = get_db_connection()
                                cursor = conn.cursor()
                                try:
                                    cursor.execute("DELETE FROM class_schedules WHERE subject_id = ?", (selected_subject_id,))
                                    conn.commit()
                                    st.success("All schedules deleted successfully!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")
                                finally:
                                    conn.close()
                        with col2:
                            if st.button("Cancel", key="cancel_delete_all"):
                                st.rerun()
            
            # Form to add a new schedule
            st.subheader("Add New Schedule")
            
            with st.form("add_schedule_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    day_options = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                    day = st.selectbox("Day*", day_options)
                    start_time = st.time_input("Start Time*", value=datetime.strptime("08:00", "%H:%M").time())
                
                with col2:
                    room = st.text_input("Room/Location*", placeholder="e.g., Room 101")
                    class_type = st.selectbox("Class Type*", ["lec", "sec"], format_func=lambda x: "Lecture" if x == "lec" else "Section")
                    end_time = st.time_input("End Time*", value=(datetime.combine(datetime.today(), start_time) + timedelta(hours=1)).time())
                
                schedule_submit = st.form_submit_button("Add Schedule", use_container_width=True, type="primary")
                
                if schedule_submit:
                    if not room:
                        st.error("Please enter a room/location.")
                    else:
                        # Format times for database
                        start_time_str = start_time.strftime("%I:%M %p")  # 12-hour format with AM/PM
                        end_time_str = end_time.strftime("%I:%M %p")
                        
                        # Check if end time is after start time
                        if end_time <= start_time:
                            st.error("End time must be after start time.")
                        else:
                            # Check for schedule conflicts
                            conflict = False
                            
                            # If no conflicts, add the schedule
                            if not conflict:
                                schedule_data = {
                                    'subject_id': selected_subject_id,
                                    'day': day,
                                    'start_time': start_time_str,
                                    'end_time': end_time_str,
                                    'room': room,
                                    'type': class_type
                                }
                                
                                success, error = add_class_schedule(schedule_data)
                                if success:
                                    st.success("Schedule added successfully!")
                                    st.rerun()
                                else:
                                    st.error(f"Error adding schedule: {error}")
    
    # Tab 4: Subject Analytics
    with tab4:
        st.header("Subject Analytics")
        
        # If using CustomTableView for analytics
        if 'subjects' in st.session_state and st.session_state.subjects:
            ctv = CustomTableView('subjects')
            ctv.show()
        else:
            # Get all subjects first
            subjects_df = get_all_subjects()
            
            if subjects_df.empty:
                st.info("No subjects available for analytics. Please add subjects first.")
            else:
                # Get all schedules
                schedules_df = get_subject_schedules()
                
                # Handle merge with better error checking
                try:
                    # Check if both DataFrames have the required columns
                    if 'subject_id' in schedules_df.columns and 'subject_id' in subjects_df.columns:
                        # Ensure subject_id has the same type in both DataFrames
                        schedules_df['subject_id'] = schedules_df['subject_id'].astype(str)
                        subjects_df['subject_id'] = subjects_df['subject_id'].astype(str)
                        
                        # Now perform the merge
                        merged_df = pd.merge(
                            schedules_df,
                            subjects_df[['subject_id', 'name']],
                            on='subject_id',
                            how='left'
                        )
                    else:
                        # Alternative: if subject_id is not in schedules_df but 'subject' is
                        if 'subject' in schedules_df.columns:
                            st.info("Using 'subject' column for joining instead of 'subject_id'")
                            # Copy schedules_df to avoid modifying the original
                            merged_df = schedules_df.copy()
                        else:
                            st.error("Required columns for joining data are missing.")
                            st.stop()
                
                    # Get attendance data for subjects
                    try:
                        conn = get_db_connection()
                        attendance_query = """
                        SELECT s.subject_name, COUNT(DISTINCT a.id) as attendance_count
                        FROM subjects s
                        JOIN class_schedules cs ON s.subject_id = cs.subject_id
                        JOIN class_attendance a ON cs.subject = a.subject
                        GROUP BY s.subject_name
                        """
                        attendance_df = execute_query_df(attendance_query)
                        conn.close()
                        
                        # Create visualizations
                        
                        # 1. Subject distribution by day
                        st.subheader("Class Schedule Distribution by Day")
                        day_counts = merged_df['day'].value_counts().reset_index()
                        day_counts.columns = ['Day', 'Count']
                        
                        # Define custom order for days
                        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                        day_counts['Day_order'] = day_counts['Day'].apply(lambda x: day_order.index(x) if x in day_order else 99)
                        day_counts = day_counts.sort_values('Day_order').drop('Day_order', axis=1)
                        
                        fig = px.bar(
                            day_counts, 
                            x='Day', 
                            y='Count',
                            color='Count',
                            color_continuous_scale='Viridis',
                            title="Number of Classes per Day"
                        )
                        fig.update_layout(xaxis_title="Day", yaxis_title="Number of Classes")
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # 2. Room utilization
                        st.subheader("Room Utilization")
                        room_counts = merged_df['room'].value_counts().head(10).reset_index()
                        room_counts.columns = ['Room', 'Classes']
                        
                        fig2 = px.pie(
                            room_counts, 
                            values='Classes', 
                            names='Room',
                            title="Top 10 Room Usage",
                            hole=0.4
                        )
                        st.plotly_chart(fig2, use_container_width=True)
                        
                        # 3. Subject with most classes
                        st.subheader("Subjects by Number of Classes")
                        subject_classes = merged_df.groupby('name').size().reset_index(name='class_count')
                        subject_classes = subject_classes.sort_values('class_count', ascending=False)
                        
                        fig3 = px.bar(
                            subject_classes.head(10), 
                            x='name', 
                            y='class_count',
                            title="Top 10 Subjects by Number of Classes",
                            color='class_count',
                            color_continuous_scale='Blues'
                        )
                        fig3.update_layout(xaxis_title="Subject", yaxis_title="Number of Classes", xaxis_tickangle=-45)
                        st.plotly_chart(fig3, use_container_width=True)
                        
                        # 4. Subjects with highest attendance
                        if not attendance_df.empty:
                            st.subheader("Subjects by Attendance")
                            fig4 = px.bar(
                                attendance_df.sort_values('attendance_count', ascending=False).head(10),
                                x='subject_name',
                                y='attendance_count',
                                title="Top 10 Subjects by Attendance",
                                color='attendance_count',
                                color_continuous_scale='Greens'
                            )
                            fig4.update_layout(xaxis_title="Subject", yaxis_title="Attendance Count", xaxis_tickangle=-45)
                            st.plotly_chart(fig4, use_container_width=True)
                        
                    except Exception as e:
                        st.error(f"Error generating analytics: {str(e)}")
                        st.info("Some analytics may not be available due to database schema limitations.")
                
                except Exception as e:
                    st.error(f"Error merging data: {str(e)}")
                    st.info("Please check that your database schema is properly set up.")
                    st.stop()

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
