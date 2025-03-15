import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import plotly.express as px
import json
import numpy as np
from custom_table_view import CustomTableView

# Constants
DATABASE_PATH = 'attendance_system.db'

def initialize_subjects_tables():
    """Create necessary tables for subject management if they don't exist"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # First check if the teacher_subjects table exists and has the right schema
        cursor.execute("PRAGMA table_info(teacher_subjects)")
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
    """Get all subjects from the database"""
    conn = get_db_connection()
    query = "SELECT * FROM subjects ORDER BY subject_name"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_teachers():
    """Get all teachers from the database"""
    conn = get_db_connection()
    query = "SELECT username FROM user_accounts WHERE role = 'professor'"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df['username'].tolist()

def get_teacher_subjects(teacher):
    """Get subjects taught by a specific teacher with enhanced error handling"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # First check if the teacher_subjects table has the right schema
        cursor.execute("PRAGMA table_info(teacher_subjects)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        # Check if the expected column exists
        if 'teacher_name' not in column_names:
            # Try to identify what the column might be called
            teacher_col = None
            for potential_name in ['teacher', 'username', 'name', 'professor']:
                if potential_name in column_names:
                    teacher_col = potential_name
                    break
            
            if teacher_col:
                # Use the found column name instead
                query = f"""
                SELECT s.* 
                FROM subjects s
                JOIN teacher_subjects ts ON s.subject_id = ts.subject_id
                WHERE ts.{teacher_col} = ?
                ORDER BY s.subject_name
                """
                df = pd.read_sql_query(query, conn, params=(teacher,))
            else:
                # If no suitable column found, return empty DataFrame with warning
                st.warning(f"Teacher column not found in teacher_subjects table. Available columns: {', '.join(column_names)}. Please run the database initialization again.")
                df = pd.DataFrame(columns=['subject_id', 'subject_name', 'course_code', 'credit_hours', 'description'])
        else:
            # Standard query with expected schema
            query = """
            SELECT s.* 
            FROM subjects s
            JOIN teacher_subjects ts ON s.subject_id = ts.subject_id
            WHERE ts.teacher_name = ?
            ORDER BY s.subject_name
            """
            df = pd.read_sql_query(query, conn, params=(teacher,))
        
    except Exception as e:
        st.error(f"Database error in get_teacher_subjects: {e}")
        # Return empty DataFrame with expected structure
        df = pd.DataFrame(columns=['subject_id', 'subject_name', 'course_code', 'credit_hours', 'description'])
    finally:
        conn.close()
        
    return df

def get_subject_schedules(subject_id=None):
    """Get all schedules or for a specific subject"""
    conn = get_db_connection()
    if subject_id:
        query = "SELECT * FROM class_schedules WHERE subject_id = ? ORDER BY day, start_time"
        df = pd.read_sql_query(query, conn, params=(subject_id,))
    else:
        query = """
        SELECT cs.*, s.subject_name 
        FROM class_schedules cs
        JOIN subjects s ON cs.subject_id = s.subject_id
        ORDER BY s.subject_name, cs.day, cs.start_time
        """
        df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def add_new_subject(subject_data):
    """Add a new subject to the database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Insert the subject
        cursor.execute(
            "INSERT INTO subjects (subject_name, course_code, credit_hours, description) VALUES (?, ?, ?, ?)",
            (subject_data['name'], subject_data['code'], subject_data['credits'], subject_data['description'])
        )
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
    """Add a new class schedule"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
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
    </style>
    """, unsafe_allow_html=True)
    
    # Create tabs for different management sections
    tab1, tab2, tab3, tab4 = st.tabs([
        "📚 View Subjects", 
        "➕ Add Subject", 
        "🗓️ Manage Schedule", 
        "📊 Subject Analytics"
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
                        st.markdown(f"""
                        <div class='card'>
                            <h3>{subject['subject_name']}</h3>
                            <p><strong>Course Code:</strong> {subject['course_code']}</p>
                            <p><strong>Credit Hours:</strong> {subject['credit_hours']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        # Get teachers for this subject
                        conn = get_db_connection()
                        teachers_query = """
                        SELECT teacher_name FROM teacher_subjects 
                        WHERE subject_id = ?
                        """
                        teachers_df = pd.read_sql_query(teachers_query, conn, params=(subject['subject_id'],))
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
                        
                        # View schedules button
                        if st.button("View Schedule", key=f"view_{subject['subject_id']}"):
                            st.session_state.view_schedule_id = subject['subject_id']
                            st.session_state.view_schedule_name = subject['subject_name']
                            
                        # Delete subject button
                        if st.button("Delete Subject", key=f"delete_{subject['subject_id']}", type="primary"):
                            if 'confirm_delete' not in st.session_state:
                                st.session_state.confirm_delete = subject['subject_id']
                            else:
                                st.session_state.confirm_delete = subject['subject_id']
                        st.markdown("</div>", unsafe_allow_html=True)
                
                # Show confirmation dialog for deletion
                if 'confirm_delete' in st.session_state and st.session_state.confirm_delete == subject['subject_id']:
                    st.warning(f"Are you sure you want to delete {subject['subject_name']}? This will delete all schedules.")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Yes, Delete", key=f"confirm_{subject['subject_id']}"):
                            success, error = delete_subject(subject['subject_id'])
                            if success:
                                st.success(f"Subject {subject['subject_name']} deleted successfully!")
                                del st.session_state.confirm_delete
                                st.rerun()
                            else:
                                st.error(f"Error deleting subject: {error}")
                    with col2:
                        if st.button("Cancel", key=f"cancel_{subject['subject_id']}"):
                            del st.session_state.confirm_delete
                            st.rerun()
                
                # Show schedule if view button was clicked
                if 'view_schedule_id' in st.session_state and st.session_state.view_schedule_id == subject['subject_id']:
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
    
    # Tab 2: Add Subject
    with tab2:
        st.header("Add New Subject")
        
        with st.form("add_subject_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                subject_name = st.text_input("Subject Name*", placeholder="e.g., Introduction to Computer Science")
                course_code = st.text_input("Course Code*", placeholder="e.g., CS101")
            
            with col2:
                credit_hours = st.number_input("Credit Hours*", min_value=1, max_value=6, value=3, step=1)
                subject_description = st.text_area("Description", placeholder="Brief description of the subject")
            
            # Get all teachers for multiselect
            all_teachers = get_teachers()
            assigned_teachers = st.multiselect("Assign Teachers*", all_teachers)
            
            submit_button = st.form_submit_button("Add Subject", use_container_width=True, type="primary")
            
            if submit_button:
                if not subject_name or not course_code or not assigned_teachers:
                    st.error("Please fill all required fields marked with *")
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
                        # Automatic redirect to add schedules
                        st.info("Now you can add schedules for this subject in the 'Manage Schedule' tab.")
                    else:
                        st.error(f"Error adding subject: {result}")
    
    # Tab 3: Manage Schedule
    with tab3:
        st.header("Manage Class Schedules")
        
        # Get all subjects for dropdown
        subjects_df = get_all_subjects()
        subject_options = [(row['subject_id'], row['subject_name']) for _, row in subjects_df.iterrows()]
        
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
                
                # Join with subject names for better display
                merged_df = pd.merge(
                    schedules_df,
                    subjects_df[['subject_id', 'subject_name']],
                    on='subject_id',
                    how='left'
                )
                
                # Get attendance data for subjects
                try:
                    conn = get_db_connection()
                    attendance_query = """
                    SELECT s.subject_name, COUNT(DISTINCT a.id) as attendance_count
                    FROM subjects s
                    JOIN class_schedules cs ON s.subject_id = cs.subject_id
                    JOIN class_attendance_records a ON cs.subject = a.subject
                    GROUP BY s.subject_name
                    """
                    attendance_df = pd.read_sql_query(attendance_query, conn)
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
                    subject_classes = merged_df.groupby('subject_name').size().reset_index(name='class_count')
                    subject_classes = subject_classes.sort_values('class_count', ascending=False)
                    
                    fig3 = px.bar(
                        subject_classes.head(10), 
                        x='subject_name', 
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

if __name__ == "__main__":
    show_subject_management()
