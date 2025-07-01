import streamlit as st
import sqlite3
import pandas as pd
import re
import io
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import hashlib
from global_fixes import apply_global_dropdown_fixes
# Add import for professor assignments functionality
import importlib
# Import time utilities for better formatting
try:
    from .time_format_utils import display_formatted_time, convert_to_db_time_format
except ImportError:
    # Fallback for when running as script
    try:
        from time_format_utils import display_formatted_time, convert_to_db_time_format
    except ImportError:
        # Define fallback functions
        def display_formatted_time(timestamp):
            return str(timestamp)
        def convert_to_db_time_format(timestamp):
            return timestamp

# Define a list of tables that should be hidden from the UI
HIDDEN_TABLES = [
    'sqlite_sequence',  # SQLite internal table for autoincrement
    'sqlite_stat1',     # SQLite statistics table
    'sqlite_master',    # SQLite schema table 
    'facial_recognition_data',  # Sensitive data table with face embeddings
    'embedding_store',     # Internal table for embeddings
    'control_4',         # Legacy control table
    # Hide legacy compatibility tables - these are just views
    'attendance_records_compat',
    'student_profiles_compat', 
    'subjects_compat',
    'subjects_compatible',
    'student_profiles_view',
    'professor_assignments_view',
    'attendance_with_names',
    'student_name_mapping',
    # Hide empty legacy tables
    'class_attendance',
    'teacher_subjects', 
    'professor_subject_assignments'
]

# Define priority order for enhanced tables
PRIORITY_TABLES = [
    'student_profiles_enhanced',
    'user_accounts_enhanced', 
    'subjects_enhanced',
    'attendance_records_enhanced',
    'class_schedules_enhanced',
    'student_enrollments',
    'facial_embeddings',
    'departments',
    'academic_terms'
]

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def execute_query_safe(query, params=None, fetch=False, commit=False):
    """
    Execute a SQL query with error handling - safe wrapper for database explorer
    
    Args:
        query (str): SQL query to execute
        params (tuple): Parameters for the query
        fetch (bool): Whether to fetch results
        commit (bool): Whether to commit changes
    
    Returns:
        list or None: Query results if fetch=True, None otherwise
    """
    conn = None
    try:
        conn = sqlite3.connect('attendance_system.db')
        cursor = conn.cursor()
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        if fetch:
            result = cursor.fetchall()
        else:
            result = None
            
        if commit:
            conn.commit()
            
        return result
    except sqlite3.Error as e:
        # Add query info to error message
        error_msg = f"SQLite error: {e}\nQuery: {query[:100]}{'...' if len(query) > 100 else ''}"
        if params:
            error_msg += f"\nParams: {params}"
        
        # Show error in Streamlit if available
        try:
            if 'st' in globals():
                st.error(f"Database Error: {e}")
            else:
                print(error_msg)
        except:
            print(error_msg)
            
        return None if fetch else False
    except Exception as e:
        # Handle non-SQLite errors
        error_msg = f"Unexpected error: {e}\nQuery: {query[:100]}{'...' if len(query) > 100 else ''}"
        try:
            if 'st' in globals():
                st.error(f"Unexpected Error: {e}")
            else:
                print(error_msg)
        except:
            print(error_msg)
            
        return None if fetch else False
    finally:
        if conn:
            conn.close()

# Use the safe version for all database operations in this module
def execute_query(query, params=None, fetch=False, commit=False):
    """Wrapper to maintain compatibility with existing code"""
    return execute_query_safe(query, params, fetch, commit)

def get_tables():
    """Get list of tables in the database, prioritizing enhanced tables and hiding legacy ones"""
    try:
        result = execute_query("SELECT name FROM sqlite_master WHERE type='table';", fetch=True)
        if not result:
            return []
        
        # Get all table names
        all_tables = []
        for table in result:
            table_name = table[0]
            if (table_name and 
                isinstance(table_name, str) and 
                table_name not in HIDDEN_TABLES and
                table_name.strip() and
                not table_name.isspace()):
                all_tables.append(table_name.strip())
        
        # Remove duplicates
        unique_tables = list(set(all_tables))
        
        # Separate priority tables and others
        priority_tables_found = []
        other_tables = []
        
        for table in unique_tables:
            if table in PRIORITY_TABLES:
                priority_tables_found.append(table)
            else:
                other_tables.append(table)
        
        # Sort priority tables by their defined order
        sorted_priority = []
        for priority_table in PRIORITY_TABLES:
            if priority_table in priority_tables_found:
                sorted_priority.append(priority_table)
        
        # Sort other tables alphabetically
        other_tables.sort()
        
        # Combine: priority tables first, then others
        final_tables = sorted_priority + other_tables
        
        # Final validation - ensure no empty strings
        final_tables = [t for t in final_tables if t and len(t) > 0]
        
        return final_tables
    except Exception as e:
        st.error(f"Error getting tables: {e}")
        return []

def get_table_columns(table):
    """Get column info for a table"""
    try:
        result = execute_query(f"PRAGMA table_info({table});", fetch=True)
        return result if result else []
    except Exception as e:
        st.error(f"Error getting columns for table {table}: {e}")
        return []

def get_column_names(table):
    """Get column names for a table"""
    columns = get_table_columns(table)
    return [col[1] for col in columns]

def get_primary_key(table):
    """Get primary key column(s) for a table"""
    columns = get_table_columns(table)
    return [col[1] for col in columns if col[5] > 0]  # col[5] is the pk flag

def show_db_explorer():
    """Display database explorer with full CRUD functionality"""
    # Apply global dropdown and styling fixes
    apply_global_dropdown_fixes()
    
    st.title("SQLite Database Manager")
    st.write("Manage your database tables with this interactive tool")
    
    # Add refresh button to clear any caching issues
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 Refresh Tables", help="Refresh the table list"):
            # Clear any cached state and force refresh
            if 'selected_table' in st.session_state:
                del st.session_state.selected_table
            st.rerun()
    
    # Initialize session state with current data - FIXED INCONSISTENCY
    current_tables = get_tables()
    
    # Display current table count for debugging
    with col1:
        st.info(f"📊 Found {len(current_tables)} tables in database")
    
    # Initialize basic session state (table selection will be handled later)
    if 'editing_row' not in st.session_state:
        st.session_state.editing_row = None
    if 'search_term' not in st.session_state:
        st.session_state.search_term = ""
    
    # Ensure we're on the Database Explorer page - prevent navigation conflicts
    if 'current_page' in st.session_state:
        st.session_state.current_page = "Database Explorer"
    
    # Create a tab for professor assignments at the top level
    tab_main, tab_prof_assign = st.tabs(["Database Tables", "Professor Assignments"])
    
    # Add enhanced CSS for better styling and user experience
    st.markdown("""
    <style>
    /* Enhance overall appearance */
    .main .block-container {
        padding-top: 1rem !important;
    }
    
    /* Compact table selection styling */
    .compact-tables {
        display: flex;
        flex-wrap: wrap;
        gap: 5px;
        margin: 5px 0;
    }
    
    /* Ultra compact table selector buttons */
    .compact-table-selector {
        background-color: #f8f9fa;
        border: 1px solid #eaeaea;
        border-radius: 4px;
        padding: 4px 8px;
        font-size: 0.8rem;
        margin: 0;
        text-align: center;
        cursor: pointer;
        transition: all 0.2s ease;
        white-space: nowrap;
        display: inline-block;
    }
    .compact-table-selector:hover {
        background-color: #e9f2fe;
        border-color: #bbd6fe;
    }
    .compact-table-selector.selected {
        background-color: #e1f5fe;
        border-color: #4fc3f7;
        color: #0277bd;
        font-weight: 600;
    }
    
    /* Category headers */
    .table-category {
        font-size: 0.85rem;
        font-weight: 500;
        color: #555;
        margin: 5px 0 2px 0;
        padding: 0;
    }
    
    /* Section dividers */
    .compact-section-divider {
        height: 1px;
        background: #e0e0e0;
        margin: 10px 0;
    }
    
    /* Horizontal scrollable container for tables */
    .table-scroll-container {
        display: flex;
        overflow-x: auto;
        padding: 5px 0;
        margin-bottom: 8px;
        -ms-overflow-style: none;  /* IE and Edge */
        scrollbar-width: thin;     /* Firefox */
    }
    
    /* Thin scrollbar for better appearance */
    .table-scroll-container::-webkit-scrollbar {
        height: 4px;
    }
    
    .table-scroll-container::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 10px;
    }
    
    .table-scroll-container::-webkit-scrollbar-thumb {
        background: #c1c1c1;
        border-radius: 10px;
    }
    
    /* Table card styling */
    .table-card {
        background-color: #f8f9fa;
        border: 1px solid #eaeaea;
        border-radius: 4px;
        padding: 5px 12px;
        margin-right: 8px;
        white-space: nowrap;
        cursor: pointer;
        transition: all 0.2s ease;
        font-size: 0.85rem;
        min-width: fit-content;
        display: inline-block;
    }
    
    .table-card:hover {
        background-color: #e9f2fe;
        border-color: #bbd6fe;
    }
    
    .table-card.selected {
        background-color: #e1f5fe;
        border-color: #4fc3f7;
        color: #0277bd;
        font-weight: 600;
    }
    
    /* Category headers with icon */
    .table-category {
        font-size: 0.85rem;
        font-weight: 500;
        color: #555;
        margin: 5px 0 2px 0;
        padding: 0;
        display: flex;
        align-items: center;
    }
    
    .category-icon {
        margin-right: 5px;
        opacity: 0.8;
    }
    
    /* Section dividers */
    .compact-section-divider {
        height: 1px;
        background: #e0e0e0;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    with tab_prof_assign:
        st.header("Professor Subject Assignments")
        
        # Try to import the professor_subject_assignment module
        try:
            # Import dynamically to avoid issues if the module isn't available
            prof_subject_module = importlib.import_module('professor_subject_assignment')
            prof_subject_module.show_professor_assignments()
        except (ImportError, AttributeError) as e:
            st.error(f"Could not load Professor Subject Assignment functionality: {e}")
            
            # Fallback implementation
            st.write("### Manual Professor Subject Assignment")
            
            # Get professors from user_accounts
            try:
                # First, let's check if the user_accounts table exists and has the expected structure
                professors_query = """
                SELECT username, full_name 
                FROM user_accounts_enhanced 
                WHERE role = 'professor' 
                ORDER BY username
                """
                professors_df = pd.read_sql_query(professors_query, sqlite3.connect('attendance_system.db'))
                
                if not professors_df.empty:
                    # Create a list of professors with both username and full_name if available
                    if 'full_name' in professors_df.columns and not professors_df['full_name'].isna().all():
                        professors = [(row['username'], f"{row['full_name']} ({row['username']})") for _, row in professors_df.iterrows()]
                    else:
                        professors = [(row['username'], row['username']) for _, row in professors_df.iterrows()]
                else:
                    professors = []
                    st.warning("No professors found in user_accounts table with role 'professor'")
                
            except Exception as e:
                st.error(f"Error getting professors: {e}")
                # Fallback: try to get from professor_profiles table if it exists
                try:
                    professors_query_fallback = """
                    SELECT username, name 
                    FROM professor_profiles 
                    ORDER BY username
                    """
                    professors_df = pd.read_sql_query(professors_query_fallback, sqlite3.connect('attendance_system.db'))
                    professors = [(row['username'], f"{row['name']} ({row['username']})") for _, row in professors_df.iterrows()] if not professors_df.empty else []
                    if professors:
                        st.info("Using professor_profiles table as fallback")
                except:
                    professors = []
                    st.error("Could not find professors in either user_accounts or professor_profiles tables")
                
                # Get subjects
                try:
                    subjects_df = pd.read_sql_query("SELECT subject_id, subject_name FROM subjects_enhanced ORDER BY subject_name", sqlite3.connect('attendance_system.db'))
                    subjects = [(row['subject_id'], row['subject_name']) for _, row in subjects_df.iterrows()] if not subjects_df.empty else []
                except Exception as e:
                    # Try alternative column name
                    try:
                        subjects_df = pd.read_sql_query("SELECT subject_id, subject_name FROM subjects_enhanced ORDER BY subject_name", sqlite3.connect('attendance_system.db'))
                        subjects = [(row['subject_id'], row['name']) for _, row in subjects_df.iterrows()] if not subjects_df.empty else []
                    except Exception as e2:
                        st.error(f"Error getting subjects: {e2}")
                        subjects = []
                
                if professors and subjects:
                    with st.form("manual_assignment"):
                        # Show professor selection with display names
                        selected_prof_display = st.selectbox("Select Professor:", 
                                                           options=[p[1] for p in professors],
                                                           key="prof_assign_select")
                        # Get the actual username from the selection
                        selected_prof = next((p[0] for p in professors if p[1] == selected_prof_display), None)
                        
                        selected_subject = st.selectbox("Select Subject:", 
                                                       options=[s[0] for s in subjects],
                                                       format_func=lambda x: next((s[1] for s in subjects if s[0] == x), "Unknown"),
                                                       key="subject_assign_select")
                        
                        if st.form_submit_button("Assign Subject"):
                            if selected_prof:
                                try:
                                    # Check if assignment already exists
                                    check_query = """
                                    SELECT id FROM professor_subject_assignments 
                                    WHERE professor_username = ? AND subject_id = ?
                                    """
                                    result = execute_query(check_query, (selected_prof, selected_subject), fetch=True)
                                    
                                    if result:
                                        st.info("This assignment already exists.")
                                    else:
                                        # Create new assignment
                                        insert_query = """
                                        INSERT INTO professor_subject_assignments 
                                        (professor_username, subject_id) VALUES (?, ?)
                                        """
                                        execute_query(insert_query, (selected_prof, selected_subject), commit=True)
                                        st.success("Subject assigned successfully!")
                                except Exception as e:
                                    st.error(f"Error assigning subject: {e}")
                            else:
                                st.error("Please select a valid professor.")
                    
                    # Show current assignments
                    st.subheader("Current Assignments")
                    try:
                        # Try different column names for subjects
                        try:
                            assignments_query = """
                            SELECT a.id, a.professor_username, s.subject_name as subject_name
                            FROM professor_subject_assignments a
                            JOIN subjects_enhanced s ON a.subject_id = s.subject_id
                            ORDER BY a.professor_username, s.subject_name
                            """
                            assignments_df = pd.read_sql_query(assignments_query, sqlite3.connect('attendance_system.db'))
                        except Exception:
                            # Fallback to 'name' column
                            assignments_query = """
                            SELECT a.id, a.professor_username, s.subject_name as subject_name
                            FROM professor_subject_assignments a
                            JOIN subjects_enhanced s ON a.subject_id = s.subject_id
                            ORDER BY a.professor_username, s.subject_name
                            """
                            assignments_df = pd.read_sql_query(assignments_query, sqlite3.connect('attendance_system.db'))
                        
                        if not assignments_df.empty:
                            st.dataframe(assignments_df)
                            
                            # Add remove functionality
                            assignment_to_remove = st.selectbox("Select assignment to remove:", 
                                                              assignments_df['id'].tolist(),
                                                              format_func=lambda x: f"{assignments_df[assignments_df['id']==x]['professor_username'].iloc[0]} - {assignments_df[assignments_df['id']==x]['subject_name'].iloc[0]}",
                                                              key="remove_assignment_select")
                            
                            if st.button("Remove Assignment", key="remove_assignment_btn"):
                                try:
                                    delete_query = "DELETE FROM professor_subject_assignments WHERE id = ?"
                                    execute_query(delete_query, (assignment_to_remove,), commit=True)
                                    st.success("Assignment removed successfully!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error removing assignment: {e}")
                        else:
                            st.info("No assignments found.")
                    except Exception as e:
                        st.error(f"Error loading assignments: {e}")
                else:
                    st.warning("No professors or subjects found in the database.")
            except Exception as e:
                st.error(f"Error setting up manual assignment: {e}")
        
        # Student Table Synchronization
        st.divider()
        st.subheader("🔄 Student Data Synchronization")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Maintain Student Table Relationships**")
            st.info("""
            Keep the `students` table synchronized with:
            • `student_profiles` (primary source)
            • `user_accounts` where role = 'student'
            """)
            
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("� Setup DB Relations", help="Create proper database relationships and constraints", key="setup_db_relations_btn"):
                    with st.spinner("Setting up database relationships..."):
                        success, message = setup_student_table_relationships()
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
            
            with col_b:
                if st.button("🔄 Sync Student Tables", type="primary", help="Synchronize all student data", key="sync_student_tables_btn"):
                    with st.spinner("Synchronizing student data..."):
                        success, message = synchronize_students_table()
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
        
        with col2:
            st.write("**Current Student Overview**")
            try:
                # Quick stats
                conn = sqlite3.connect('attendance_system.db')
                
                profile_count = pd.read_sql_query("SELECT COUNT(*) as count FROM student_profiles_enhanced", conn).iloc[0]['count']
                legacy_count = pd.read_sql_query("SELECT COUNT(*) as count FROM students", conn).iloc[0]['count']
                user_students = pd.read_sql_query("SELECT COUNT(*) as count FROM user_accounts_enhanced WHERE role = 'student'", conn).iloc[0]['count']
                
                st.metric("Student Profiles", profile_count)
                st.metric("Legacy Students", legacy_count)
                st.metric("Student Accounts", user_students)
                
                conn.close()
                
                # Show unified student data
                if st.button("📊 View Student Relationships", help="Show all students and their connection status", key="view_student_relationships_btn"):
                    with st.spinner("Loading student data..."):
                        unified_df = get_unified_student_list()
                        if not unified_df.empty:
                            st.dataframe(
                                unified_df[['name', 'username', 'connection_status', 'department', 'section']].head(20), 
                                use_container_width=True
                            )
                            
                            # Show connection status summary
                            status_counts = unified_df['connection_status'].value_counts()
                            st.write("**Connection Status Summary:**")
                            for status, count in status_counts.items():
                                st.write(f"• {status}: {count}")
                        else:
                            st.warning("No student data found")
                
            except Exception as e:
                st.error(f"Could not load student statistics: {e}")

    with tab_main:
        # Get fresh list of tables - ALWAYS CURRENT
        tables = get_tables()
        
        if not tables:
            st.info("No tables found in the database. Create a new table below.")
            create_new_table()
            return
        
        # Filter and clean tables - MAXIMUM ROBUSTNESS
        clean_tables = []
        for table in tables:
            if (table and 
                isinstance(table, str) and 
                table.strip() and 
                not table.isspace() and 
                len(table.strip()) > 0 and
                table.strip() != ''):  # Extra check for empty strings
                cleaned = table.strip()
                if cleaned and cleaned not in clean_tables:  # Avoid duplicates inline
                    clean_tables.append(cleaned)
        
        # Sort alphabetically for consistent display
        clean_tables = sorted(clean_tables)
        
        # Final validation - remove any remaining empty or invalid entries
        clean_tables = [t for t in clean_tables if t and isinstance(t, str) and len(t.strip()) > 0]
        
        if not clean_tables:
            st.warning("No valid tables found in the database.")
            create_new_table()
            return
        
        # Ensure selected table is valid and exists in current list
        if ('selected_table' not in st.session_state or 
            not st.session_state.selected_table or 
            st.session_state.selected_table not in clean_tables):
            st.session_state.selected_table = clean_tables[0] if clean_tables else None
            # Clear related state when table is reset
            if 'editing_row' in st.session_state:
                st.session_state.editing_row = None
            if 'search_term' in st.session_state:
                st.session_state.search_term = ""
         # Create tabs for each table - all tables displayed as individual tabs
        st.markdown("### Database Tables")
        
        # Show all tables as tabs (no pagination)
        table_tabs = st.tabs([f"📊 {table}" for table in clean_tables])
        
        # Display content for each table in its respective tab
        for i, table in enumerate(clean_tables):
            with table_tabs[i]:
                st.session_state.selected_table = table
                display_table_content(table)
        
        return  # Exit here since we're handling all table display in tabs

def display_table_content(table):
    """Display the complete content and operations for a specific table"""
    columns = get_column_names(table)
    primary_keys = get_primary_key(table)
    
    # Get row count
    try:
        row_count_result = execute_query(f"SELECT COUNT(*) FROM {table};", fetch=True)
        row_count = row_count_result[0][0] if row_count_result else 0
    except Exception as e:
        st.error(f"Error getting row count: {e}")
        row_count = 0
    
    # Table header with stats
    st.markdown(f"""
    <div class="table-info-card">
        <h3 style="margin:0; color:#0277bd; display:flex; align-items:center;">
            <span style="margin-right:8px;">📊</span> {table}
        </h3>
        <div style="margin-top:10px; display:flex; gap:15px; color:#555;">
            <div><strong>Columns:</strong> {len(columns)}</div>
            <div><strong>Rows:</strong> {row_count}</div>
            <div><strong>Primary Key:</strong> {', '.join(primary_keys) if primary_keys else 'None'}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Create tabs for different operations
    view_tab, add_tab, delete_tab, sql_tab, analytics_tab, manage_tab = st.tabs(
        ["📄 View Data", "➕ Add Row", "🗑️ Delete Records", "🔍 SQL Query", "📊 Analytics", "⚙️ Database Operations"]
    )
    
    # VIEW DATA TAB
    with view_tab:
        display_view_data_section(table, columns, row_count)
    
    # ADD ROW TAB  
    with add_tab:
        display_add_row_section(table, columns, primary_keys)
    
    # DELETE RECORDS TAB
    with delete_tab:
        display_delete_records_section(table, columns, primary_keys)
    
    # SQL QUERY TAB
    with sql_tab:
        display_sql_query_section(table)
    
    # ANALYTICS TAB
    with analytics_tab:
        display_analytics_section(table, columns)
    
    # DATABASE OPERATIONS TAB
    with manage_tab:
        display_database_operations_section(table)

def display_view_data_section(table, columns, row_count):
    """Display the view data section with all original functionality"""
    try:
        # Simple query to get all data
        df = pd.read_sql_query(f"SELECT * FROM {table};", sqlite3.connect('attendance_system.db'))
    except Exception as e:
        st.error(f"Error querying data: {e}")
        df = pd.DataFrame()
    
    # Show record count
    st.markdown(f"""
        <div style="margin:10px 0;">
            <div>Showing <b>{len(df)}</b> of <b>{row_count:,}</b> records</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Display table data
    if not df.empty:
        # Create a copy for display to avoid modifying original
        df_display = df.copy()
        
        # Format time columns if they exist
        time_columns = ['start_time', 'end_time', 'time', 'created_at', 'last_login']
        for col in time_columns:
            if col in df_display.columns:
                try:
                    df_display[col] = df_display[col].apply(display_formatted_time)
                except:
                    pass  # Keep original format if formatting fails
        
        st.dataframe(df_display, use_container_width=True)
    else:
        st.info("No data found in this table.")

def display_add_row_section(table, columns, primary_keys):
    """Display the add row section with form for new records"""
    st.subheader(f"➕ Add New Record to {table}")
    
    # Create form for adding new row
    with st.form(f"add_row_{table}"):
        st.write("**Enter values for new record:**")
        
        # Create input fields for each column
        input_values = {}
        cols = st.columns(min(3, len(columns)))
        
        for i, column in enumerate(columns):
            col_idx = i % len(cols)
            with cols[col_idx]:
                # Skip auto-increment primary keys
                if column.lower() in ['id'] and column in primary_keys:
                    st.write(f"**{column}** (auto-generated)")
                    input_values[column] = None
                else:
                    input_values[column] = st.text_input(f"**{column}**", key=f"input_{table}_{column}")
        
        # Submit button
        if st.form_submit_button("Add Record", type="primary"):
            try:
                # Filter out None values (auto-generated fields)
                insert_data = {k: v for k, v in input_values.items() if v is not None and v != ""}
                
                if insert_data:
                    # Create INSERT query
                    cols_str = ", ".join(insert_data.keys())
                    placeholders = ", ".join(["?" for _ in insert_data])
                    query = f"INSERT INTO {table} ({cols_str}) VALUES ({placeholders})"
                    
                    # Execute insert
                    result = execute_query(query, tuple(insert_data.values()), commit=True)
                    if result is not False:
                        st.success(f"✅ Record added successfully to {table}!")
                        st.rerun()
                    else:
                        st.error("Failed to add record")
                else:
                    st.warning("Please fill in at least one field")
            except Exception as e:
                st.error(f"Error adding record: {e}")

def display_delete_records_section(table, columns, primary_keys):
    """Display the delete records section"""
    st.subheader(f"🗑️ Delete Records from {table}")
    
    # Warning message
    st.warning("⚠️ **Warning:** Deleting records is permanent and cannot be undone!")
    
    # Show current data for reference
    try:
        df = pd.read_sql_query(f"SELECT * FROM {table} LIMIT 20;", sqlite3.connect('attendance_system.db'))
        if not df.empty:
            st.write("**Current records (showing first 20):**")
            st.dataframe(df, use_container_width=True)
            
            # Delete options
            delete_method = st.radio("Choose delete method:", 
                                   ["Delete by ID", "Delete by condition", "Delete all records"],
                                   key=f"delete_method_{table}")
            
            if delete_method == "Delete by ID" and primary_keys:
                pk_column = primary_keys[0]  # Use first primary key
                if pk_column in df.columns:
                    record_id = st.selectbox(f"Select {pk_column} to delete:", 
                                           options=df[pk_column].tolist(),
                                           key=f"delete_record_{table}")
                    
                    if st.button("🗑️ Delete Selected Record", type="secondary", key=f"delete_selected_record_{table}"):
                        try:
                            query = f"DELETE FROM {table} WHERE {pk_column} = ?"
                            result = execute_query(query, (record_id,), commit=True)
                            if result is not False:
                                st.success(f"✅ Record with {pk_column}={record_id} deleted!")
                                st.rerun()
                            else:
                                st.error("Failed to delete record")
                        except Exception as e:
                            st.error(f"Error deleting record: {e}")
            
            elif delete_method == "Delete by condition":
                condition = st.text_input("Enter WHERE condition (without WHERE):", 
                                        placeholder="e.g., name = 'John' OR age > 30",
                                        key=f"condition_input_{table}")
                if condition and st.button("🗑️ Delete Matching Records", type="secondary", key=f"delete_matching_records_{table}"):
                    try:
                        query = f"DELETE FROM {table} WHERE {condition}"
                        result = execute_query(query, commit=True)
                        if result is not False:
                            st.success("✅ Records deleted successfully!")
                            st.rerun()
                        else:
                            st.error("Failed to delete records")
                    except Exception as e:
                        st.error(f"Error deleting records: {e}")
            
            elif delete_method == "Delete all records":
                confirm = st.text_input("Type 'DELETE ALL' to confirm:", "", key=f"confirm_delete_all_{table}")
                if confirm == "DELETE ALL" and st.button("🗑️ Delete All Records", type="secondary", key=f"delete_all_records_{table}"):
                    try:
                        query = f"DELETE FROM {table}"
                        result = execute_query(query, commit=True)
                        if result is not False:
                            st.success("✅ All records deleted!")
                            st.rerun()
                        else:
                            st.error("Failed to delete records")
                    except Exception as e:
                        st.error(f"Error deleting records: {e}")
        else:
            st.info("No records to delete.")
    except Exception as e:
        st.error(f"Error loading data: {e}")

def display_sql_query_section(table):
    """Display the SQL query section"""
    st.subheader(f"🔍 SQL Query for {table}")
    
    # Predefined queries
    predefined_queries = {
        "Select All": f"SELECT * FROM {table};",
        "Count Records": f"SELECT COUNT(*) FROM {table};",
        "First 10 Records": f"SELECT * FROM {table} LIMIT 10;",
        "Table Schema": f"PRAGMA table_info({table});",
    }
    
    query_type = st.selectbox("Choose a predefined query or write custom:", 
                             ["Custom"] + list(predefined_queries.keys()),
                             key=f"query_type_{table}")
    
    if query_type == "Custom":
        query = st.text_area("Enter your SQL query:", 
                           value=f"SELECT * FROM {table} LIMIT 10;", 
                           height=100,
                           key=f"sql_query_{table}")
    else:
        query = predefined_queries[query_type]
        st.code(query, language="sql")
    
    if st.button("▶️ Execute Query", key=f"execute_query_{table}"):
        try:
            if query.strip().upper().startswith(('SELECT', 'PRAGMA')):
                # Read-only queries
                result_df = pd.read_sql_query(query, sqlite3.connect('attendance_system.db'))
                st.success("✅ Query executed successfully!")
                st.dataframe(result_df, use_container_width=True)
            else:
                # Write queries
                st.warning("⚠️ This appears to be a write operation. Use with caution!")
                if st.checkbox("I understand this will modify the database", key=f"modify_db_confirm_{table}"):
                    result = execute_query(query, commit=True)
                    if result is not False:
                        st.success("✅ Query executed successfully!")
                    else:
                        st.error("Query failed")
        except Exception as e:
            st.error(f"Query error: {e}")

def display_analytics_section(table, columns):
    """Display the analytics section"""
    st.subheader(f"📊 Analytics for {table}")
    
    try:
        df = pd.read_sql_query(f"SELECT * FROM {table};", sqlite3.connect('attendance_system.db'))
        
        if not df.empty:
            # Basic statistics
            st.write("**Basic Statistics:**")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Records", len(df))
            with col2:
                st.metric("Total Columns", len(df.columns))
            with col3:
                null_count = df.isnull().sum().sum()
                st.metric("Null Values", null_count)
            
            # Column analysis
            if len(df.columns) > 0:
                st.write("**Column Analysis:**")
                selected_column = st.selectbox("Select column to analyze:", df.columns.tolist(),
                                              key=f"analyze_column_{table}")
                
                if selected_column:
                    col_data = df[selected_column]
                    
                    # Show column stats
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**{selected_column} Statistics:**")
                        st.write(f"- Unique values: {col_data.nunique()}")
                        st.write(f"- Null values: {col_data.isnull().sum()}")
                        st.write(f"- Data type: {col_data.dtype}")
                    
                    with col2:
                        if col_data.dtype in ['int64', 'float64']:
                            st.write(f"**Numeric Statistics:**")
                            st.write(f"- Mean: {col_data.mean():.2f}")
                            st.write(f"- Min: {col_data.min()}")
                            st.write(f"- Max: {col_data.max()}")
                    
                    # Value counts
                    if col_data.nunique() < 50:  # Only for columns with reasonable unique values
                        st.write(f"**Value Distribution for {selected_column}:**")
                        value_counts = col_data.value_counts().head(10)
                        st.bar_chart(value_counts)
        else:
            st.info("No data available for analysis.")
    except Exception as e:
        st.error(f"Error loading analytics: {e}")

def display_database_operations_section(table):
    """Display the database operations section"""
    st.subheader(f"⚙️ Database Operations for {table}")
    
    # Export data
    st.write("**📤 Export Data**")
    export_format = st.selectbox("Export format:", ["CSV", "JSON", "Excel"],
                                key=f"export_format_{table}")
    
    if st.button("💾 Export Data", key=f"export_data_btn_{table}"):
        try:
            df = pd.read_sql_query(f"SELECT * FROM {table};", sqlite3.connect('attendance_system.db'))
            
            if export_format == "CSV":
                csv_data = df.to_csv(index=False)
                st.download_button("📥 Download CSV", csv_data, f"{table}.csv", "text/csv")
            elif export_format == "JSON":
                json_data = df.to_json(orient="records", indent=2)
                st.download_button("📥 Download JSON", json_data, f"{table}.json", "application/json")
            elif export_format == "Excel":
                excel_buffer = io.BytesIO()
                df.to_excel(excel_buffer, index=False)
                excel_data = excel_buffer.getvalue()
                st.download_button("📥 Download Excel", excel_data, f"{table}.xlsx", 
                                 "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            
            st.success("✅ Export ready for download!")
        except Exception as e:
            st.error(f"Export error: {e}")
    
    # Table operations
    st.write("**🔧 Table Operations**")
    
    # Drop table (dangerous operation)
    with st.expander("🚨 Dangerous Operations", expanded=False):
        st.warning("⚠️ **These operations are irreversible!**")
        st.info("💡 **Tip**: Make sure to backup your data before dropping tables!")
        
        if st.checkbox(f"I want to delete the table '{table}'", key=f"want_delete_table_{table}"):
            confirm_name = st.text_input("Type the table name to confirm deletion:", key=f"confirm_table_name_{table}")
            
            if confirm_name and confirm_name != table:
                st.error("❌ Table name doesn't match. Please type the exact table name.")
            elif confirm_name == table:
                st.success("✅ Table name confirmed!")
                
                if st.button("🗑️ DROP TABLE", type="secondary", key=f"drop_table_{table}"):
                    with st.spinner(f"Dropping table '{table}'..."):
                        try:
                            # Use direct SQLite connection for DROP operations
                            conn = sqlite3.connect('attendance_system.db')
                            cursor = conn.cursor()
                            
                            # Check if table exists first
                            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
                            table_exists = cursor.fetchone()
                            
                            if table_exists:
                                # Enable foreign keys temporarily to check for dependencies
                                cursor.execute("PRAGMA foreign_keys = ON")
                                
                                # Try to drop the table
                                cursor.execute(f"DROP TABLE `{table}`")
                                conn.commit()
                                
                                # Verify the table was dropped
                                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
                                still_exists = cursor.fetchone()
                                
                                if not still_exists:
                                    st.success(f"✅ Table '{table}' has been successfully deleted!")
                                    st.balloons()
                                    
                                    # Clear the form
                                    if f"want_delete_table_{table}" in st.session_state:
                                        del st.session_state[f"want_delete_table_{table}"]
                                    if f"confirm_table_name_{table}" in st.session_state:
                                        del st.session_state[f"confirm_table_name_{table}"]
                                    
                                    st.info("🔄 Refreshing page to update table list...")
                                    st.rerun()
                                else:
                                    st.error(f"❌ Table '{table}' still exists after DROP command!")
                            else:
                                st.error(f"❌ Table '{table}' does not exist!")
                                
                        except sqlite3.IntegrityError as e:
                            st.error(f"❌ Cannot drop table due to foreign key constraints: {e}")
                        except sqlite3.OperationalError as e:
                            st.error(f"❌ Operational error: {e}")
                        except sqlite3.Error as e:
                            st.error(f"❌ SQLite error: {e}")
                        except Exception as e:
                            st.error(f"❌ Unexpected error: {e}")
                        finally:
                            if 'conn' in locals():
                                conn.close()
        
        return  # Exit here since we're handling all table display in tabs

def create_new_table():
    """Placeholder for create new table functionality"""
    st.info("Create new table functionality will be implemented")

# Add the missing functions for compatibility
def setup_student_table_relationships():
    """Placeholder function"""
    return True, "Function not implemented in this version"

def synchronize_students_table():
    """Placeholder function"""
    return True, "Function not implemented in this version"

def get_unified_student_list():
    """Placeholder function"""
    return pd.DataFrame()

def create_new_table():
    """Placeholder function for creating new tables"""
    st.info("Create new table functionality will be implemented here")

def render_add_row_form(table, columns, primary_keys):
    """Placeholder function for adding rows"""
    st.info("Add row functionality will be implemented here")