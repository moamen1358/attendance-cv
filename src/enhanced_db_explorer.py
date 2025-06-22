import streamlit as st
import sqlite3
import pandas as pd
import re
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
# Add import for professor assignments functionality
import importlib
# Import time utilities for better formatting
from time_format_utils import display_formatted_time, convert_to_db_time_format

# Define a list of tables that should be hidden from the UI
HIDDEN_TABLES = [
    'sqlite_sequence',  # SQLite internal table for autoincrement
    'sqlite_stat1',     # SQLite statistics table
    'sqlite_master',    # SQLite schema table 
    'facial_recognition_data',  # Sensitive data table with face embeddings
    'embedding_store',     # Internal table for embeddings
    'control_4'         # Legacy control table
]

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
        error_msg = f"SQLite error: {e}\nQuery: {query}\nParams: {params}"
        if 'st' in globals():
            st.error(error_msg)
        else:
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
    """Get list of all tables in the database, filtering out system tables"""
    try:
        result = execute_query("SELECT name FROM sqlite_master WHERE type='table';", fetch=True)
        if not result:
            return []
        
        # Filter out hidden tables and strip whitespace from table names
        visible_tables = [table[0].strip() for table in result if table[0] not in HIDDEN_TABLES]
        
        # Remove any empty strings or pure whitespace strings
        visible_tables = [t for t in visible_tables if t and not t.isspace()]
        
        # Remove duplicates while preserving order
        seen = set()
        unique_tables = []
        for t in visible_tables:
            if t not in seen:
                seen.add(t)
                unique_tables.append(t)
        
        # Sort tables in logical groups
        student_tables = [t for t in unique_tables if "student" in t.lower()]
        attendance_tables = [t for t in unique_tables if "attend" in t.lower()]
        subject_tables = [t for t in unique_tables if "subject" in t.lower() or "class" in t.lower()]
        user_tables = [t for t in unique_tables if "user" in t.lower() or "account" in t.lower()]
        other_tables = [t for t in unique_tables if t not in 
                      student_tables + attendance_tables + subject_tables + user_tables]
        
        # Return tables in a logical order
        return (student_tables + attendance_tables + subject_tables + 
                user_tables + other_tables)
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
    st.title("SQLite Database Manager")
    st.write("Manage your database tables with this interactive tool")
    
    # Initialize session state
    if 'tables' not in st.session_state:
        st.session_state.tables = get_tables()
    if 'selected_table' not in st.session_state:
        st.session_state.selected_table = st.session_state.tables[0] if st.session_state.tables else None
    if 'editing_row' not in st.session_state:
        st.session_state.editing_row = None
    if 'search_term' not in st.session_state:
        st.session_state.search_term = ""
    
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
                professors_df = pd.read_sql_query("SELECT username FROM user_accounts WHERE role = 'professor' ORDER BY username", sqlite3.connect('attendance_system.db'))
                professors = professors_df['username'].tolist() if not professors_df.empty else []
                
                # Get subjects
                subjects_df = pd.read_sql_query("SELECT subject_id, name FROM subjects ORDER BY name", sqlite3.connect('attendance_system.db'))
                subjects = [(row['subject_id'], row['name']) for _, row in subjects_df.iterrows()] if not subjects_df.empty else []
                
                if professors and subjects:
                    with st.form("manual_assignment"):
                        selected_prof = st.selectbox("Select Professor:", professors)
                        selected_subject = st.selectbox("Select Subject:", 
                                                       options=[s[0] for s in subjects],
                                                       format_func=lambda x: next((s[1] for s in subjects if s[0] == x), "Unknown"))
                        
                        if st.form_submit_button("Assign Subject"):
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
                    
                    # Show current assignments
                    st.subheader("Current Assignments")
                    try:
                        assignments_query = """
                        SELECT a.id, a.professor_username, s.name as subject_name
                        FROM professor_subject_assignments a
                        JOIN subjects s ON a.subject_id = s.subject_id
                        ORDER BY a.professor_username, s.name
                        """
                        assignments_df = pd.read_sql_query(assignments_query, sqlite3.connect('attendance_system.db'))
                        
                        if not assignments_df.empty:
                            st.dataframe(assignments_df)
                            
                            # Add remove functionality
                            assignment_to_remove = st.selectbox("Select assignment to remove:", 
                                                              assignments_df['id'].tolist(),
                                                              format_func=lambda x: f"{assignments_df[assignments_df['id']==x]['professor_username'].iloc[0]} - {assignments_df[assignments_df['id']==x]['subject_name'].iloc[0]}")
                            
                            if st.button("Remove Assignment"):
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
    
    with tab_main:
        # Get fresh list of tables
        tables = get_tables()  # Get fresh list of tables
        
        if not tables:
            st.info("No tables found in the database. Create a new table below.")
            create_new_table()
            return
        else:
            # Filter tables if needed
            filtered_tables = tables
            
            # Deduplicate tables to avoid any potential duplicates
            unique_filtered_tables = []
            seen_tables = set()
            for table in filtered_tables:
                if table not in seen_tables:
                    unique_filtered_tables.append(table)
                    seen_tables.add(table)
            
            filtered_tables = unique_filtered_tables
            
            # Group tables by type for better organization
            student_tables = [t for t in filtered_tables if "student" in t.lower()]
            attendance_tables = [t for t in filtered_tables if "attend" in t.lower()]
            user_tables = [t for t in filtered_tables if "user" in t.lower() or "account" in t.lower()]
            other_tables = [t for t in filtered_tables if t not in student_tables + attendance_tables + user_tables]
            
            # Create a better organized dropdown list with proper optgroup
            st.markdown("""
            <style>
            /* Style for dropdown with optgroups */
            div[data-testid="stSelectbox"] ul {
                max-height: 240px !important;
            }
            
            /* Style option groups in dropdown */
            .table-group-header {
                font-weight: bold;
                color: #555;
                font-size: 0.9em;
                padding: 5px;
                pointer-events: none !important;
                background-color: #f0f2f6 !important;
                border-bottom: 1px solid #ddd;
                margin-top: 5px;
            }
            
            /* Style normal options */
            .table-option {
                padding-left: 10px !important;
            }
            </style>
            """, unsafe_allow_html=True)
            
            # Create a flat list with better styling for headers
            table_options = []
            table_labels = []
            is_header = []
            
            # Build lists for dropdown - removed headers to avoid selection issues
            if student_tables:
                for table in student_tables:
                    table_options.append(table)
                    table_labels.append(table)
                    is_header.append(False)
            
            if attendance_tables:
                for table in attendance_tables:
                    table_options.append(table)
                    table_labels.append(table)
                    is_header.append(False)
                
            if user_tables:
                for table in user_tables:
                    table_options.append(table)
                    table_labels.append(table)
                    is_header.append(False)
                
            if other_tables:
                for table in other_tables:
                    table_options.append(table)
                    table_labels.append(table)
                    is_header.append(False)
            
           
            current_table = st.session_state.selected_table
            
            # Default to first table if current selection isn't valid or if table_options is empty
            if not table_options:
                st.warning("No tables found in the database.")
                return
            
            if current_table not in table_options and table_options:
                current_table = table_options[0]
                st.session_state.selected_table = current_table
            
            # Find index of current table in our options list
            try:
                default_index = table_options.index(current_table)
            except ValueError:
                # If not found, default to first item
                default_index = 0
                current_table = table_options[0]
                st.session_state.selected_table = current_table
            
            # Create the dropdown for table selection - without disabled parameter
            st.write("### Select Table")
            selected_table = st.selectbox(
                "Choose a table to view or edit:",
                options=table_options,
                index=default_index,
                key="table_selector_fixed",
                on_change=None
            )
            
            # Handle selection - ensure session state is updated immediately
            if selected_table != st.session_state.selected_table:
                st.session_state.selected_table = selected_table
                st.session_state.editing_row = None
                st.session_state.search_term = ""
                # Force rerun to refresh the interface
                st.rerun()
            
            # Check if we need to rerun (set by other components)
            if st.session_state.get('needs_rerun', False):
                st.session_state.needs_rerun = False
                st.rerun()
            
            # Add thin separator line
            st.markdown('<div class="compact-section-divider"></div>', unsafe_allow_html=True)
            
            # Check if we have a selected table
            if st.session_state.selected_table:
                table = st.session_state.selected_table
                columns = get_column_names(table)
                primary_keys = get_primary_key(table)
                
                # Get row count
                try:
                    row_count_result = execute_query(f"SELECT COUNT(*) FROM {table};", fetch=True)
                    row_count = row_count_result[0][0] if row_count_result else 0
                except Exception as e:
                    st.error(f"Error getting row count: {e}")
                    row_count = 0
                
                # Table header with stats - enhanced styling
                st.markdown(f"""
                <div class="table-info-card">
                    <h2 style="margin:0; color:#0277bd; display:flex; align-items:center;">
                        <span style="margin-right:8px;">📊</span> {table}
                    </h2>
                    <div style="margin-top:10px; display:flex; gap:15px; color:#555;">
                        <div><strong>Columns:</strong> {len(columns)}</div>
                        <div><strong>Rows:</strong> {row_count}</div>
                        <div><strong>Primary Key:</strong> {', '.join(primary_keys) if primary_keys else 'None'}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Create tabs for different operations - UPDATED to include Analytics tab
                view_tab, add_tab, delete_tab, sql_tab, analytics_tab, manage_tab = st.tabs(["📄 View Data", "➕ Add Row", "🗑️ Delete Records", "🔍 SQL Query", "📊 Analytics", "⚙️ Database Operations"])
                
                # VIEW DATA TAB
                with view_tab:
                    # Enhanced search controls
                    st.subheader("🔍 Advanced Search & Filters")
                    
                    # Create expandable search section
                    with st.expander("🔧 Advanced Search Options", expanded=False):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            # Column-specific search
                            search_column = st.selectbox("Search in specific column:", 
                                                       ["All Columns"] + columns)
                            search_operator = st.selectbox("Search operator:", 
                                                         ["Contains", "Equals", "Starts with", "Ends with", "Greater than", "Less than"])
                        
                        with col2:
                            # Date range filter for date columns
                            date_columns = [col for col in columns if any(keyword in col.lower() for keyword in ['date', 'time', 'created', 'updated'])]
                            if date_columns:
                                date_filter_col = st.selectbox("Filter by date column:", 
                                                             ["No date filter"] + date_columns)
                                if date_filter_col != "No date filter":
                                    col_date1, col_date2 = st.columns(2)
                                    with col_date1:
                                        start_date = st.date_input("From date:")
                                    with col_date2:
                                        end_date = st.date_input("To date:")
                    
                    # Main search control
                    search_col1, search_col2 = st.columns([3, 1])
                    
                    with search_col1:
                        search_term = st.text_input("🔍 Search:", value=st.session_state.search_term,
                                                  placeholder="Enter search term...")
                        if search_term != st.session_state.search_term:
                            st.session_state.search_term = search_term
                            st.rerun()
                    
                    with search_col2:
                        # Quick filter buttons
                        if st.button("🗑️ Clear", use_container_width=True):
                            st.session_state.search_term = ""
                            st.rerun()
                    
                    # Get row count
                    try:
                        row_count_result = execute_query(f"SELECT COUNT(*) FROM {table};", fetch=True)
                        row_count = row_count_result[0][0] if row_count_result else 0
                    except Exception as e:
                        st.error(f"Error getting row count: {e}")
                        row_count = 0
                    
                    # Build query without pagination limits
                    try:
                        if st.session_state.search_term:
                            # Build search condition for each column
                            search_conditions = []
                            for col in columns:
                                search_conditions.append(f"{col} LIKE ?")
                            
                            # Combine conditions with OR (removed LIMIT and OFFSET)
                            search_query = f"SELECT * FROM {table} WHERE " + " OR ".join(search_conditions)
                            
                            # Prepare search parameters
                            search_params = [f"%{st.session_state.search_term}%"] * len(columns)
                            
                            # Execute search query
                            df = pd.read_sql_query(search_query, sqlite3.connect('attendance_system.db'), params=search_params)
                        else:
                            # Simple query without pagination
                            df = pd.read_sql_query(f"SELECT * FROM {table};", sqlite3.connect('attendance_system.db'))
                    except Exception as e:
                        st.error(f"Error querying data: {e}")
                        df = pd.DataFrame()  # Empty dataframe on error
                    
                    # Show record count with filter info
                    showing = len(df)
                    st.markdown(f"""
                        <div style="margin:10px 0;">
                            <div>Showing <b>{showing}</b> of <b>{row_count:,}</b> records {f"(filtered)" if st.session_state.search_term else ""}</div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Display table data with edit functionality
                    if not df.empty:
                        # Format time columns to 12-hour format before displaying
                        df_display = df.copy()
                        
                        # Check if this table has time columns
                        if 'start_time' in df.columns:
                            df_display['start_time'] = df['start_time'].apply(display_formatted_time)
                        if 'end_time' in df.columns:
                            df_display['end_time'] = df['end_time'].apply(display_formatted_time)
                        if 'time' in df.columns:
                            df_display['time'] = df['time'].apply(display_formatted_time)
                        
                        edited_df = st.data_editor(
                            df_display,
                            hide_index=True,
                            use_container_width=True,
                            num_rows="fixed",
                            key="data_editor"
                        )
                        
                        # Detect changes and update database
                        if st.button("💾 Check for Changes", use_container_width=True):
                            # Compare original and edited data
                            changes_detected = False
                            
                            try:
                                # Convert time columns back to original format for comparison
                                df_compare = df.copy()
                                edited_compare = edited_df.copy()
                                
                                # Revert time formatting for comparison
                                time_columns = ['start_time', 'end_time', 'time']
                                for time_col in time_columns:
                                    if time_col in df_compare.columns:
                                        # edited_df has formatted times, convert back for comparison
                                        # This is tricky - we need to detect if values actually changed
                                        pass  # Skip this complex comparison for now
                                
                                # Simple comparison - check if dataframes are different
                                if not df_display.equals(edited_df):
                                    changes_detected = True
                                
                                if changes_detected:
                                    st.success("Changes detected! Click 'Save Changes' to apply them.")
                                    
                                    if st.button("💾 Save Changes", type="primary", use_container_width=True):
                                        try:
                                            # Find the changed rows
                                            for index, row in edited_df.iterrows():
                                                original_row = df_display.iloc[index]
                                                if not original_row.equals(row):
                                                    # Get primary key value for this row
                                                    pk_values = {}
                                                    for pk in primary_keys:
                                                        pk_values[pk] = df.iloc[index][pk]
                                                    
                                                    # Build UPDATE statement
                                                    update_cols = []
                                                    update_vals = []
                                                    
                                                    for col in columns:
                                                        if str(original_row[col]) != str(row[col]):
                                                            update_cols.append(f"{col} = ?")
                                                            update_vals.append(row[col])
                                                    
                                                    if update_cols:  # Only update if there are changes
                                                        # Add WHERE clause parameters
                                                        where_conditions = []
                                                        for pk, val in pk_values.items():
                                                            where_conditions.append(f"{pk} = ?")
                                                            update_vals.append(val)
                                                        
                                                        update_stmt = f"UPDATE {table} SET " + ", ".join(update_cols) + " WHERE " + " AND ".join(where_conditions)
                                                        
                                                        # Execute update
                                                        execute_query(update_stmt, tuple(update_vals), commit=True)
                                                        
                                            st.success("Data updated successfully!")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Error updating data: {e}")
                                else:
                                    st.info("No changes detected.")
                            except Exception as e:
                                st.error(f"Error checking for changes: {e}")
                    else:
                        st.info("No data to display.")
                    
                # ADD ROW TAB
                with add_tab:
                    # Create sub-tabs for single vs bulk operations
                    single_tab, bulk_tab = st.tabs(["➕ Add Single Row", "📋 Bulk Operations"])
                    
                    with single_tab:
                        render_add_row_form(table, columns, primary_keys)
                    
                    with bulk_tab:
                        st.subheader(f"📋 Bulk Operations for {table}")
                        
                        # Bulk insert with CSV template
                        st.write("**Method 1: CSV Template**")
                        
                        if st.button("📄 Download CSV Template"):
                            # Create a template CSV with column headers
                            template_data = {col: [""] for col in columns}
                            template_df = pd.DataFrame(template_data)
                            
                            csv_template = template_df.to_csv(index=False)
                            st.download_button(
                                label="💾 Download Template",
                                data=csv_template,
                                file_name=f"{table}_template.csv",
                                mime="text/csv"
                            )
                        
                        # Upload and process bulk data
                        bulk_file = st.file_uploader("Upload filled CSV template:", type=['csv'])
                        
                        if bulk_file is not None:
                            try:
                                bulk_df = pd.read_csv(bulk_file)
                                
                                # Validate columns
                                missing_cols = set(columns) - set(bulk_df.columns)
                                extra_cols = set(bulk_df.columns) - set(columns)
                                
                                if missing_cols:
                                    st.warning(f"Missing columns: {', '.join(missing_cols)}")
                                if extra_cols:
                                    st.info(f"Extra columns (will be ignored): {', '.join(extra_cols)}")
                                
                                # Show preview
                                st.write("**Preview of data to insert:**")
                                st.dataframe(bulk_df.head(10), use_container_width=True)
                                
                                if st.button("📤 Insert Bulk Data", type="primary"):
                                    try:
                                        # Filter to only include valid columns
                                        valid_df = bulk_df[[col for col in columns if col in bulk_df.columns]]
                                        
                                        # Insert data
                                        conn = sqlite3.connect('attendance_system.db')
                                        valid_df.to_sql(table, conn, if_exists='append', index=False)
                                        conn.commit()
                                        conn.close()
                                        
                                        st.success(f"✅ Successfully inserted {len(valid_df)} records!")
                                        st.rerun()
                                        
                                    except Exception as e:
                                        st.error(f"Bulk insert failed: {e}")
                                        
                            except Exception as e:
                                st.error(f"Error processing CSV: {e}")
                        
                        # Manual bulk insert
                        st.write("**Method 2: Manual Entry**")
                        
                        # Initialize bulk data in session state
                        if 'bulk_rows' not in st.session_state:
                            st.session_state.bulk_rows = 3
                        
                        num_rows = st.number_input("Number of rows to add:", 
                                                  min_value=1, max_value=50, 
                                                  value=st.session_state.bulk_rows)
                        st.session_state.bulk_rows = num_rows
                        
                        with st.form("bulk_manual_form"):
                            st.write(f"Enter data for {num_rows} rows:")
                            
                            bulk_data = []
                            for row in range(num_rows):
                                st.write(f"**Row {row + 1}:**")
                                row_data = {}
                                
                                # Create columns for input fields
                                input_cols = st.columns(min(3, len(columns)))
                                
                                for i, col_name in enumerate(columns):
                                    col_idx = i % len(input_cols)
                                    with input_cols[col_idx]:
                                        row_data[col_name] = st.text_input(
                                            col_name, 
                                            key=f"bulk_{row}_{col_name}",
                                            placeholder=f"Enter {col_name}"
                                        )
                                
                                bulk_data.append(row_data)
                            
                            if st.form_submit_button("📤 Insert All Rows", use_container_width=True):
                                try:
                                    # Convert to DataFrame and insert
                                    bulk_df = pd.DataFrame(bulk_data)
                                    
                                    # Remove empty rows
                                    bulk_df = bulk_df.dropna(how='all')
                                    
                                    if not bulk_df.empty:
                                        conn = sqlite3.connect('attendance_system.db')
                                        bulk_df.to_sql(table, conn, if_exists='append', index=False)
                                        conn.commit()
                                        conn.close()
                                        
                                        st.success(f"✅ Successfully inserted {len(bulk_df)} rows!")
                                        st.rerun()
                                    else:
                                        st.warning("No data to insert (all rows empty)")
                                        
                                except Exception as e:
                                    st.error(f"Bulk insert failed: {e}")
                
                # DELETE TAB
                with delete_tab:
                    st.subheader(f"Delete Records from {table}")
                    
                    # Single record deletion
                    st.write("#### Delete Single Record")
                    if primary_keys:
                        with st.form("delete_single_form"):
                            # For each primary key, create an input field
                            pk_values = {}
                            for pk in primary_keys:
                                pk_values[pk] = st.text_input(f"{pk}:", key=f"delete_pk_{pk}")
                            
                            delete_submitted = st.form_submit_button("Delete Record", type="primary")
                            
                            if delete_submitted:
                                # Build where clause
                                where_conditions = []
                                delete_vals = []
                                
                                for pk, val in pk_values.items():
                                    if val:  # Only include non-empty values
                                        where_conditions.append(f"{pk} = ?")
                                        delete_vals.append(val)
                                
                                if not where_conditions:
                                    st.error("Please provide at least one primary key value")
                                else:
                                    # Build and execute DELETE statement
                                    delete_stmt = f"DELETE FROM {table} WHERE " + " AND ".join(where_conditions)
                                    
                                    # Execute delete with confirmation
                                    if st.checkbox("I confirm this deletion", key="confirm_single_delete"):
                                        try:
                                            affected_rows = execute_query(delete_stmt, tuple(delete_vals), commit=True)
                                            st.success("Record deleted successfully!")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Error deleting record: {str(e)}")
                    else:
                        st.info("This table doesn't have a primary key. Use the bulk delete option below.")
                    
                    # Bulk delete option
                    st.write("#### Delete Multiple Records")
                    with st.form("delete_bulk_form"):
                        where_clause = st.text_area("WHERE Clause:", placeholder=f"Example: column_name = 'value' AND other_column > 10")
                        preview_button = st.form_submit_button("Preview Records to Delete")
                        
                        if preview_button and where_clause:
                            try:
                                # Preview what will be deleted
                                preview_df = pd.read_sql_query(f"SELECT * FROM {table} WHERE {where_clause} LIMIT 10", sqlite3.connect('attendance_system.db'))
                                
                                # Get count of all records that will be deleted
                                count_query = f"SELECT COUNT(*) FROM {table} WHERE {where_clause}"
                                count_result = execute_query(count_query, fetch=True)
                                total_count = count_result[0][0] if count_result else 0
                                
                                st.write(f"This will delete {total_count} records. Here's a preview of up to 10 records:")
                                st.dataframe(preview_df, use_container_width=True)
                                
                                # Show delete button only after preview
                                if st.checkbox("I confirm deletion of these records", key="confirm_bulk_delete"):
                                    delete_stmt = f"DELETE FROM {table} WHERE {where_clause}"
                                    try:
                                        execute_query(delete_stmt, commit=True)
                                        st.success(f"Successfully deleted {total_count} records!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error during bulk delete: {str(e)}")
                            except Exception as e:
                                st.error(f"Error in WHERE clause: {str(e)}")
                
                # SQL QUERY TAB
                with sql_tab:
                    st.subheader("Run Custom SQL Query")
                    query = st.text_area("Enter SQL Query:", height=100, placeholder=f"Example: SELECT * FROM {table} WHERE column_name = 'value'")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("🔍 Execute SELECT Query", use_container_width=True):
                            if not query.strip():
                                st.warning("Please enter a SQL query")
                            elif query.strip().upper().startswith("SELECT"):
                                try:
                                    result_df = pd.read_sql_query(query, sqlite3.connect('attendance_system.db'))
                                    
                                    st.success("Query executed successfully!")
                                    
                                    # Process DataFrame to convert time formats
                                    if not result_df.empty:
                                        # Format time columns to AM/PM display format for user-friendly view
                                        if 'start_time' in result_df.columns:
                                            result_df['start_time'] = result_df['start_time'].apply(display_formatted_time)
                                        if 'end_time' in result_df.columns:
                                            result_df['end_time'] = result_df['end_time'].apply(display_formatted_time)
                                        if 'time' in result_df.columns:
                                            result_df['time'] = result_df['time'].apply(display_formatted_time)
                                        
                                        # Display the human-readable version
                                        st.dataframe(result_df, use_container_width=True)
                                    else:
                                        st.info("Query returned no results.")
                                except Exception as e:
                                    st.error(f"Error executing query: {e}")
                            else:
                                st.error("Only SELECT queries are allowed with this button.")
                    
                    with col2:
                        if st.button("⚠️ Execute Action Query", type="primary", use_container_width=True):
                            if not query.strip():
                                st.warning("Please enter a SQL query")
                            elif query.strip().upper().startswith(("INSERT", "UPDATE", "DELETE")):
                                # Show confirmation checkbox
                                if st.checkbox("I understand this will modify the database", key="confirm_action_query"):
                                    try:
                                        execute_query(query, commit=True)
                                        st.success("Query executed successfully!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error executing query: {e}")
                            else:
                                st.error("Only INSERT, UPDATE, or DELETE queries are allowed with this button.")
                
                # DATABASE OPERATIONS TAB
                with manage_tab:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("Create New Table")
                        create_new_table()
                    
                    with col2:
                        st.subheader("Delete Current Table")
                        if st.session_state.selected_table:
                            st.warning(f"Are you sure you want to delete table '{st.session_state.selected_table}'?\nThis action cannot be undone!")
                            confirm_name = st.text_input("Type the table name to confirm deletion:", key="confirm_delete_main")
                            
                            if st.button("🗑️ DELETE TABLE", type="primary", use_container_width=True):
                                if confirm_name == st.session_state.selected_table:
                                    execute_query(f"DROP TABLE {st.session_state.selected_table};", commit=True)
                                    st.success(f"Table '{st.session_state.selected_table}' deleted successfully!")
                                    st.session_state.tables = get_tables()
                                    if st.session_state.tables:
                                        st.session_state.selected_table = st.session_state.tables[0]
                                    else:
                                        st.session_state.selected_table = None
                                    st.rerun()
                                else:
                                    st.error("Table name doesn't match. Deletion cancelled.")
                        else:
                            st.info("No table selected to delete.")
                    
                    with col2:
                        st.subheader("📤 Export & Import")
                        
                        # Export functionality
                        st.write("**Export Data:**")
                        export_format = st.selectbox("Export Format:", ["CSV", "JSON", "Excel"])
                        
                        if st.button("📥 Export Current Table", use_container_width=True):
                            try:
                                # Get all data from current table
                                export_query = f"SELECT * FROM {st.session_state.selected_table}"
                                export_df = pd.read_sql_query(export_query, sqlite3.connect('attendance_system.db'))
                                
                                if export_format == "CSV":
                                    csv_data = export_df.to_csv(index=False)
                                    st.download_button(
                                        label="💾 Download CSV",
                                        data=csv_data,
                                        file_name=f"{st.session_state.selected_table}.csv",
                                        mime="text/csv"
                                    )
                                
                                elif export_format == "JSON":
                                    json_data = export_df.to_json(orient='records', indent=2)
                                    st.download_button(
                                        label="💾 Download JSON",
                                        data=json_data,
                                        file_name=f"{st.session_state.selected_table}.json",
                                        mime="application/json"
                                    )
                                
                                elif export_format == "Excel":
                                    # For Excel, we need to create a buffer
                                    from io import BytesIO
                                    buffer = BytesIO()
                                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                                        export_df.to_excel(writer, sheet_name=st.session_state.selected_table, index=False)
                                    
                                    st.download_button(
                                        label="💾 Download Excel",
                                        data=buffer.getvalue(),
                                        file_name=f"{st.session_state.selected_table}.xlsx",
                                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                    )
                                
                                st.success(f"Export prepared! Click the download button above.")
                                
                            except Exception as e:
                                st.error(f"Export failed: {e}")
                        
                        # Import functionality
                        st.write("**Import Data:**")
                        uploaded_file = st.file_uploader("Choose a file to import:", 
                                                        type=['csv', 'json', 'xlsx'])
                        
                        if uploaded_file is not None:
                            try:
                                # Read the uploaded file
                                if uploaded_file.name.endswith('.csv'):
                                    import_df = pd.read_csv(uploaded_file)
                                elif uploaded_file.name.endswith('.json'):
                                    import_df = pd.read_json(uploaded_file)
                                elif uploaded_file.name.endswith('.xlsx'):
                                    import_df = pd.read_excel(uploaded_file)
                                
                                st.write("**Preview of imported data:**")
                                st.dataframe(import_df.head(), use_container_width=True)
                                
                                # Import options
                                import_mode = st.radio("Import Mode:", 
                                                     ["Append to existing table", "Replace table data"])
                                
                                if st.button("📤 Import Data", type="primary"):
                                    conn = sqlite3.connect('attendance_system.db')
                                    
                                    if import_mode == "Replace table data":
                                        # Clear existing data
                                        conn.execute(f"DELETE FROM {st.session_state.selected_table}")
                                    
                                    # Insert new data
                                    import_df.to_sql(st.session_state.selected_table, conn, 
                                                   if_exists='append', index=False)
                                    conn.commit()
                                    conn.close()
                                    
                                    st.success(f"Successfully imported {len(import_df)} records!")
                                    st.rerun()
                                
                            except Exception as e:
                                st.error(f"Import failed: {e}")
                        
                        # Backup functionality
                        st.write("**Database Backup:**")
                        if st.button("💾 Create Database Backup", use_container_width=True):
                            try:
                                import shutil
                                from datetime import datetime
                                
                                backup_name = f"attendance_system_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                                shutil.copy2('attendance_system.db', backup_name)
                                
                                st.success(f"Backup created: {backup_name}")
                                
                                # Offer download of backup
                                with open(backup_name, 'rb') as f:
                                    st.download_button(
                                        label="📥 Download Backup",
                                        data=f.read(),
                                        file_name=backup_name,
                                        mime="application/octet-stream"
                                    )
                                    
                            except Exception as e:
                                st.error(f"Backup failed: {e}")
    # Remove database info sidebar completely - keep empty sidebar to prevent layout issues
    with st.sidebar:
        # Empty sidebar
        pass

# Clean up the create_new_table function with better styling
def create_new_table():
    """Create a new table form component with enhanced styling"""
    with st.container():
        st.markdown('<div class="clean-form">', unsafe_allow_html=True)
        
        st.markdown("### Create New Table")
        new_table_name = st.text_input("Table Name", key="new_table_name_main", placeholder="Enter a name for your new table")
        
        # Column definition section with improved styling
        st.markdown("#### Define Columns")
        st.caption("Add columns to your table structure")
        
        col1, col2, col3 = st.columns([3, 2, 1])
        with col1:
            st.markdown("**Name**")
        with col2:
            st.markdown("**Type**")
        with col3:
            st.markdown("**PK**")
        
        # Initialize columns list if not exists
        if 'new_table_columns' not in st.session_state:
            st.session_state.new_table_columns = [{"name": "", "type": "TEXT", "pk": False}]
        
        # Display column inputs
        columns_to_add = []
        for i, col in enumerate(st.session_state.new_table_columns):
            col1, col2, col3, col4 = st.columns([3, 2, 1, 0.5])
            with col1:
                col_name = st.text_input("", value=col["name"], key=f"col_name_main_{i}")
            with col2:
                col_type = st.selectbox("", ["TEXT", "INTEGER", "REAL", "BLOB", "DATETIME"], 
                                       index=["TEXT", "INTEGER", "REAL", "BLOB", "DATETIME"].index(col["type"]),
                                       key=f"col_type_main_{i}")
            with col3:
                col_pk = st.checkbox("", value=col["pk"], key=f"col_pk_main_{i}")
            with col4:
                # Only show delete button if there's more than one column
                if len(st.session_state.new_table_columns) > 1:
                    if st.button("❌", key=f"del_col_main_{i}"):
                        st.session_state.new_table_columns.pop(i)
                        st.rerun()
                        
            columns_to_add.append({"name": col_name, "type": col_type, "pk": col_pk})
        
        # Update column definitions
        st.session_state.new_table_columns = columns_to_add
        
        # Add column button with icon and better styling
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("➕ Add Column", key="add_column_main"):
                st.session_state.new_table_columns.append({"name": "", "type": "TEXT", "pk": False})
                st.rerun()
        
        # Create table button with better styling
        if st.button("Create Table", key="create_table_main", type="primary", use_container_width=True):
            if not new_table_name.strip():
                st.error("Please provide a table name")
            elif not new_table_name.replace('_', '').replace('-', '').isalnum():
                st.error("Table name should only contain letters, numbers, underscores, and hyphens")
            else:
                # Check if any columns are defined and have names
                valid_columns = [col for col in st.session_state.new_table_columns if col["name"].strip()]
                if not valid_columns:
                    st.error("Please define at least one column with a name")
                else:
                    # Build CREATE TABLE statement
                    column_defs = []
                    for col in valid_columns:
                        col_name = col["name"].strip()
                        if not col_name.replace('_', '').replace('-', '').isalnum():
                            st.error(f"Column name '{col_name}' should only contain letters, numbers, underscores, and hyphens")
                            break
                        
                        col_def = f"{col_name} {col['type']}"
                        if col["pk"]:
                            col_def += " PRIMARY KEY"
                        column_defs.append(col_def)
                    else:  # This else belongs to the for loop - executes if no break occurred
                        if column_defs:
                            create_stmt = f"CREATE TABLE {new_table_name} (\n" + ",\n".join(column_defs) + "\n);"
                            
                            # Execute create table
                            try:
                                # Check if table already exists
                                existing_tables = get_tables()
                                if new_table_name in existing_tables:
                                    st.error(f"Table '{new_table_name}' already exists")
                                else:
                                    execute_query(create_stmt, commit=True)
                                    st.success(f"Table '{new_table_name}' created successfully!")
                                    st.session_state.tables = get_tables()
                                    st.session_state.selected_table = new_table_name
                                    st.session_state.new_table_columns = [{"name": "", "type": "TEXT", "pk": False}]
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Error creating table: {e}")
        
        st.markdown('</div>', unsafe_allow_html=True)

def get_foreign_key_values(table_name, column_name):
    """Get possible values for a foreign key column"""
    conn = None
    try:
        conn = sqlite3.connect('attendance_system.db')
        cursor = conn.cursor()
        
        # Get foreign key info
        cursor.execute(f"PRAGMA foreign_key_list({table_name})")
        fk_data = cursor.fetchall()
        
        # Check if this column is a foreign key
        ref_table = None
        ref_col = None
        
        for fk in fk_data:
            if fk[3] == column_name:  # [3] is the "from" column
                ref_table = fk[2]     # [2] is the referenced table
                ref_col = fk[4]       # [4] is the referenced column
                break
        
        if not ref_table:
            return []
        
        # Get values from the referenced table
        try:
            # First check if the table has a "name" column for better display
            cursor.execute(f"PRAGMA table_info({ref_table})")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'name' in columns:
                # Include both ID and name for better display
                cursor.execute(f"SELECT {ref_col}, name FROM {ref_table} ORDER BY name")
                values = [(str(row[0]), f"{row[0]} - {row[1]}") for row in cursor.fetchall()]
            else:
                # Just use the referenced column value
                cursor.execute(f"SELECT {ref_col} FROM {ref_table} ORDER BY {ref_col}")
                values = [(str(row[0]), str(row[0])) for row in cursor.fetchall()]
            
            return values
        except Exception as e:
            st.warning(f"Error fetching foreign key values: {e}")
            return []
    except Exception as e:
        st.error(f"Error accessing foreign key info: {e}")
        return []
    finally:
        if conn:
            conn.close()

def get_common_values(column_name):
    """Return common values for known column types"""
    column_name_lower = column_name.lower()
    
    # Role columns
    if 'role' in column_name_lower:
        return [('admin', 'Administrator'), ('user', 'Regular User'), ('student', 'Student'), ('professor', 'Professor')]
    
    # Status columns
    elif 'status' in column_name_lower:
        return [('active', 'Active'), ('inactive', 'Inactive'), ('pending', 'Pending')]
        
    # Day columns
    elif 'day' in column_name_lower:
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        return [(day, day) for day in days]
        
    # Yes/No or boolean-like columns
    elif any(x in column_name_lower for x in ['is_', 'has_', 'enable', 'active', 'visible', 'allow']):
        return [('1', 'Yes'), ('0', 'No')]
    
    # No common values detected
    return []

# ADD ROW TAB - enhanced version
def render_add_row_form(table, columns, primary_keys):
    """Render an enhanced form for adding a new row with smart input fields"""
    st.subheader(f"Add New Row to {table}")
    
    with st.form("add_row_form"):
        # Create input fields for each column
        new_row_data = {}
        
        # Create 2 columns layout for better form organization
        col_size = 2
        for i in range(0, len(columns), col_size):
            cols = st.columns(min(col_size, len(columns) - i))
            for j, col_idx in enumerate(range(i, min(i + col_size, len(columns)))):
                col_name = columns[col_idx]
                
                # Get column type information
                col_info = get_table_columns(table)[col_idx]
                col_type = col_info[2].upper()  # [2] is the type
                
                with cols[j]:
                    # Skip auto-increment primary keys
                    if (col_name in primary_keys and len(primary_keys) == 1 and 
                        "INTEGER" in col_type):
                        st.text_input(col_name, value="(Auto)", disabled=True)
                        continue
                    
                    # Check if this is a foreign key
                    fk_values = get_foreign_key_values(table, col_name)
                    if fk_values:
                        # Add an empty option for nullable foreign keys
                        options = [('', '-- Select Value --')] + fk_values
                        selected = st.selectbox(
                            col_name,
                            options=options,
                            format_func=lambda x: x[1],  # Display the formatted value
                            key=f"fk_{table}_{col_name}"
                        )
                        new_row_data[col_name] = selected[0] if selected else None
                        
                    # Check for date type
                    elif 'DATE' in col_type:
                        value = st.date_input(
                            col_name,
                            value=datetime.now().date(),
                            key=f"date_{table}_{col_name}"
                        )
                        new_row_data[col_name] = value
                        
                    # Check for time type
                    elif 'TIME' in col_type or ('time' in col_name.lower() and 'stamp' not in col_name.lower()):
                        # Custom 12-hour time input with AM/PM selector
                        hour_col, minute_col, ampm_col = st.columns([1, 1, 1])
                        
                        with hour_col:
                            # Create hour selector (1-12)
                            current_hour = datetime.now().hour
                            # Convert 24h to 12h format for default selection
                            display_hour = current_hour % 12
                            if display_hour == 0:
                                display_hour = 12
                                
                            hour_value = st.selectbox(
                                "Hour",
                                options=list(range(1, 13)),  # 1-12 for 12-hour format
                                index=display_hour-1,  # Adjust for 0-based index
                                key=f"hour_{table}_{col_name}"
                            )
                            
                        with minute_col:
                            # Create minute selector (00, 15, 30, 45)
                            minute_value = st.selectbox(
                                "Minute",
                                options=[0, 15, 30, 45],
                                index=0,
                                format_func=lambda x: f"{x:02d}",  # Format as "00", "15", etc.
                                key=f"minute_{table}_{col_name}"
                            )
                            
                        with ampm_col:
                            # AM/PM selector
                            default_index = 1 if current_hour >= 12 else 0
                            am_pm = st.selectbox(
                                "AM/PM",
                                options=["AM", "PM"],
                                index=default_index,
                                key=f"ampm_{table}_{col_name}"
                            )
                        
                        # Convert to 12-hour AM/PM format for storage
                        if am_pm == "PM" and hour_value < 12:
                            hour_24 = hour_value + 12
                        elif am_pm == "AM" and hour_value == 12:
                            hour_24 = 0
                        else:
                            hour_24 = hour_value
                            
                        # Format as 12-hour AM/PM for database storage (consistent with system)
                        display_hour = hour_value
                        time_str = f"{display_hour:02d}:{minute_value:02d} {am_pm}"
                        new_row_data[col_name] = time_str
                        
                        # Show preview of the time
                        st.markdown(f"**{col_name}:** {time_str}")
                        
                    # Check for datetime/timestamp type
                    elif any(x in col_type for x in ['DATETIME', 'TIMESTAMP']):
                        date_val = st.date_input(
                            f"{col_name} (Date)",
                            value=datetime.now().date(),
                            key=f"dt_date_{table}_{col_name}"
                        )
                        time_val = st.time_input(
                            f"{col_name} (Time)",
                            value=datetime.now().time(),
                            key=f"dt_time_{table}_{col_name}"
                        )
                        # Combine date and time
                        combined = datetime.combine(date_val, time_val)
                        new_row_data[col_name] = combined.strftime("%Y-%m-%d %H:%M:%S")
                        
                    # Check for boolean type
                    elif 'BOOL' in col_type:
                        value = st.checkbox(
                            col_name,
                            key=f"bool_{table}_{col_name}"
                        )
                        new_row_data[col_name] = 1 if value else 0
                        
                    # Check for numeric types
                    elif any(x in col_type for x in ['INT', 'REAL', 'FLOAT', 'DOUBLE', 'DECIMAL']):
                        if 'INT' in col_type:
                            # Integer input
                            value = st.number_input(
                                col_name,
                                step=1,
                                key=f"int_{table}_{col_name}"
                            )
                        else:
                            # Float input
                            value = st.number_input(
                                col_name,
                                key=f"float_{table}_{col_name}"
                            )
                        new_row_data[col_name] = value
                        
                    # Check for common values
                    else:
                        common_values = get_common_values(col_name)
                        if common_values:
                            selected = st.selectbox(
                                col_name,
                                options=[('', '-- Select Value --')] + common_values,
                                format_func=lambda x: x[1],  # Display the formatted value
                                key=f"common_{table}_{col_name}"
                            )
                            new_row_data[col_name] = selected[0] if selected else None
                        else:
                            # Default to text input
                            new_row_data[col_name] = st.text_input(col_name, key=f"new_{col_name}")
        
        submitted = st.form_submit_button("Add Row", use_container_width=True)
        if submitted:
            # Prepare column names and values for non-auto-increment fields
            cols_to_insert = []
            vals_to_insert = []
            for col, val in new_row_data.items():
                # Skip empty auto-increment primary keys
                if (col in primary_keys and len(primary_keys) == 1 and 
                    "INTEGER" in get_table_columns(table)[columns.index(col)][2].upper() and not val):
                    continue
                cols_to_insert.append(col)
                vals_to_insert.append(val if val != "" else None)
            
            if not cols_to_insert:
                st.error("Please provide at least one value")
            else:
                # Build INSERT statement
                placeholders = ", ".join(["?"] * len(cols_to_insert))
                insert_stmt = f"INSERT INTO {table} ({', '.join(cols_to_insert)}) VALUES ({placeholders});"
                
                # Execute insert
                try:
                    execute_query(insert_stmt, tuple(vals_to_insert), commit=True)
                    st.success("Row added successfully!")
                    # Clear form by resetting the page
                    st.rerun()
                except Exception as e:
                    st.error(f"Error adding row: {e}")

class CustomTableView:
    # ... existing code ...

    def _get_filtered_data(self, where_clause="", order_by="", limit=1000, offset=0):
        """Get data from the table with optional filtering"""
        conn = None
        try:
            conn = sqlite3.connect('attendance_system.db')
            
            # Check if this is an attendance-related table and apply special sorting
            is_attendance_table = any(name in self.table_name.lower() for name in ['attendance', 'class_attendance'])
            
            query = f"SELECT * FROM {self.table_name}"
            
            if where_clause:
                query += f" WHERE {where_clause}"
                
            # For attendance tables, default to timestamp/date descending if no explicit order is given
            if is_attendance_table and not order_by:
                # Try to find date/time column for sorting
                for time_col in ['timestamp', 'class_date', 'date', 'created_at', 'time']:
                    cursor = conn.cursor()
                    cursor.execute(f"PRAGMA table_info({self.table_name})")
                    columns = [col[1] for col in cursor.fetchall()]
                    if time_col in columns:
                        order_by = f"{time_col} DESC"
                        break
            
            # Apply order_by clause
            if order_by:
                query += f" ORDER BY {order_by}"
            elif hasattr(self, 'primary_key') and self.primary_key:
                query += f" ORDER BY {self.primary_key}"
                
            query += f" LIMIT {limit} OFFSET {offset}"
            
            df = pd.read_sql_query(query, conn)
            
            # Get total row count
            count_query = f"SELECT COUNT(*) FROM {self.table_name}"
            if where_clause:
                count_query += f" WHERE {where_clause}"
            
            count_df = pd.read_sql_query(count_query, conn)
            total_rows = count_df.iloc[0, 0] if not count_df.empty else 0
            
            return df, total_rows
        except Exception as e:
            st.error(f"Error getting filtered data: {e}")
            return pd.DataFrame(), 0
        finally:
            if conn:
                conn.close()

    # ... rest of the class methods ...

if __name__ == "__main__":
    show_db_explorer()

def validate_data_integrity(table_name):
    """Perform comprehensive data integrity checks"""
    issues = []
    
    try:
        conn = sqlite3.connect('attendance_system.db')
        
        # Check for NULL values in NOT NULL columns
        columns_info = execute_query(f"PRAGMA table_info({table_name})", fetch=True)
        for col_info in columns_info:
            col_name, col_type, not_null = col_info[1], col_info[2], col_info[3]
            
            if not_null:
                null_count_result = execute_query(
                    f"SELECT COUNT(*) FROM {table_name} WHERE {col_name} IS NULL",
                    fetch=True
                )
                null_count = null_count_result[0][0] if null_count_result else 0
                
                if null_count > 0:
                    issues.append({
                        'Type': 'NULL Constraint Violation',
                        'Column': col_name,
                        'Issue': f'{null_count} NULL values in NOT NULL column',
                        'Severity': 'High'
                    })
        
        # Check for duplicate primary keys
        pk_columns = get_primary_key(table_name)
        if pk_columns:
            pk_list = ', '.join(pk_columns)
            dup_query = f"""
            SELECT {pk_list}, COUNT(*) as dup_count
            FROM {table_name}
            GROUP BY {pk_list}
            HAVING COUNT(*) > 1
            """
            
            dup_result = execute_query(dup_query, fetch=True)
            if dup_result:
                issues.append({
                    'Type': 'Primary Key Violation',
                    'Column': pk_list,
                    'Issue': f'{len(dup_result)} duplicate primary key values',
                    'Severity': 'Critical'
                })
        
        # Check for foreign key violations
        fk_info = execute_query(f"PRAGMA foreign_key_list({table_name})", fetch=True)
        for fk in fk_info:
            from_col, to_table, to_col = fk[3], fk[2], fk[4]
            
            orphan_query = f"""
            SELECT COUNT(*) FROM {table_name} t1
            LEFT JOIN {to_table} t2 ON t1.{from_col} = t2.{to_col}
            WHERE t1.{from_col} IS NOT NULL AND t2.{to_col} IS NULL
            """
            
            try:
                orphan_result = execute_query(orphan_query, fetch=True)
                orphan_count = orphan_result[0][0] if orphan_result else 0
                
                if orphan_count > 0:
                    issues.append({
                        'Type': 'Foreign Key Violation',
                        'Column': from_col,
                        'Issue': f'{orphan_count} orphaned records',
                        'Severity': 'Medium'
                    })
            except:
                pass  # Skip if referenced table doesn't exist
        
        conn.close()
        
    except Exception as e:
        issues.append({
            'Type': 'Validation Error',
            'Column': 'N/A',
            'Issue': f'Could not complete validation: {e}',
            'Severity': 'Low'
        })
    
    return issues

def generate_schema_diagram():
    """Generate a visual representation of the database schema"""
    try:
        import networkx as nx
        
        # Get all tables and their relationships
        tables = get_tables()
        G = nx.DiGraph()
        
        # Add tables as nodes
        for table in tables:
            G.add_node(table, node_type='table')
        
        # Add foreign key relationships as edges
        for table in tables:
            try:
                fk_info = execute_query(f"PRAGMA foreign_key_list({table})", fetch=True)
                for fk in fk_info:
                    from_table = table
                    to_table = fk[2]
                    from_col = fk[3]
                    to_col = fk[4]
                    
                    if to_table in tables:  # Only add if target table exists
                        G.add_edge(from_table, to_table, 
                                 relationship=f"{from_col} -> {to_col}")
            except:
                continue
        
        return G
    
    except ImportError:
        return None
    except Exception as e:
        st.error(f"Error generating schema diagram: {e}")
        return None