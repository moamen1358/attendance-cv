import streamlit as st
import sqlite3
from database_utils import execute_query, execute_query_df
import pandas as pd
import re
from datetime import datetime
# Add import for professor assignments functionality
import importlib

# Define a list of tables that should be hidden from the UI
HIDDEN_TABLES = [
    'sqlite_sequence',  # SQLite internal table for autoincrement
    'sqlite_stat1',     # SQLite statistics table
    'sqlite_master',    # SQLite schema table 
    'facial_recognition_data',  # Sensitive data table with face embeddings
    'embedding_store',     # Internal table for embeddings
    'control_4'         # Legacy control table
]

def execute_query(query, params=(), fetch=False, commit=False):
    """
    Execute a SQL query with error handling
    
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
        cursor.execute(query, params)
        
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
        st.error(error_msg)
        raise Exception(error_msg)  # Re-raise for caller to handle
    finally:
        if conn:
            conn.close()

def get_tables():
    """Get list of all tables in the database, filtering out system tables"""
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

def get_table_columns(table):
    """Get column info for a table"""
    result = execute_query(f"PRAGMA table_info({table});", fetch=True)
    return result if result else []

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
                professors_df = execute_query_df("SELECT username FROM user_accounts WHERE role = 'professor' ORDER BY username")
                professors = professors_df['username'].tolist() if not professors_df.empty else []
                
                # Get subjects
                subjects_df = execute_query_df("SELECT subject_id, name FROM subjects ORDER BY name")
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
                        assignments_df = execute_query_df(assignments_query)
                        
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
        else:
            # Create a compact table filter
            col1, col2 = st.columns([4, 1])
            with col1:
                filter_term = st.text_input("🔍 Filter:", key="table_filter", placeholder="Type to filter tables")
            with col2:
                st.markdown("<div style='height: 32px;'></div>", unsafe_allow_html=True)  # Empty space to align with input
                total_tables = len(tables)
                st.caption(f"{total_tables} tables")
            
            # Filter tables if needed
            if filter_term:
                filtered_tables = [t for t in tables if filter_term.lower() in t.lower()]
            else:
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
            
            # Get current selected table or default to first available
            current_table = st.session_state.selected_table
            
            # Default to first table if current selection isn't valid
            if current_table not in table_options and table_options:
                current_table = table_options[0]
            
            # Find index of current table in our options list
            try:
                default_index = table_options.index(current_table)
            except ValueError:
                # If not found, default to first item
                default_index = 0
            
            # Create the dropdown for table selection - without disabled parameter
            st.write("### Select Table")
            
            # Create category headers
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                if student_tables:
                    st.markdown("**👨‍🎓 STUDENT TABLES**")
            with col2:
                if attendance_tables:
                    st.markdown("**📋 ATTENDANCE TABLES**")
            with col3:
                if user_tables:
                    st.markdown("**👤 USER TABLES**")
            with col4:
                if other_tables:
                    st.markdown("**📊 OTHER TABLES**")
            
            # Simple selectbox without disabled parameter
            selected_option = st.selectbox(
                "Choose a table to view or edit:",
                options=table_options,
                index=default_index,
                key="table_dropdown"
            )
            
            # Handle selection
            if selected_option != st.session_state.selected_table:
                st.session_state.selected_table = selected_option
                st.session_state.editing_row = None
                st.session_state.search_term = ""
                st.rerun()
            
            # Add thin separator line
            st.markdown('<div class="compact-section-divider"></div>', unsafe_allow_html=True)
            
            # Check if we have a selected table
            if st.session_state.selected_table:
                table = st.session_state.selected_table
                columns = get_column_names(table)
                primary_keys = get_primary_key(table)
                
                # Get row count
                row_count_result = execute_query(f"SELECT COUNT(*) FROM {table};", fetch=True)
                row_count = row_count_result[0][0] if row_count_result else 0
                
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
                
                # Create tabs for different operations - UPDATED to include Database Operations tab
                view_tab, add_tab, delete_tab, sql_tab, manage_tab = st.tabs(["📄 View Data", "➕ Add Row", "🗑️ Delete Records", "🔍 SQL Query", "⚙️ Database Operations"])
                
                # VIEW DATA TAB
                with view_tab:
                    # Search control only (REMOVE pagination controls)
                    search_col = st.columns(1)[0]
                    
                    with search_col:
                        search_term = st.text_input("🔍 Search in any column:", value=st.session_state.search_term)
                        if search_term != st.session_state.search_term:
                            st.session_state.search_term = search_term
                            st.rerun()
                    
                    # Get row count
                    row_count_result = execute_query(f"SELECT COUNT(*) FROM {table};", fetch=True)
                    row_count = row_count_result[0][0] if row_count_result else 0
                    
                    # Build query without pagination limits
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
                        conn = sqlite3.connect('attendance_system.db')
                        df = execute_query_df(search_query, search_params)
                        conn.close()
                    else:
                        # Simple query without pagination
                        query = f"SELECT * FROM {table};"
                        conn = sqlite3.connect('attendance_system.db')
                        df = execute_query_df(query)
                        conn.close()
                    
                    # Show record count with filter info
                    showing = len(df)
                    st.markdown(f"""
                        <div style="margin:10px 0;">
                            <div>Showing <b>{showing}</b> of <b>{row_count:,}</b> records {f"(filtered)" if st.session_state.search_term else ""}</div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Display table data with edit functionality
                    if not df.empty:
                        edited_df = st.data_editor(
                            df,
                            hide_index=True,
                            use_container_width=True,
                            num_rows="fixed",
                            key="data_editor"
                        )
                        
                        # Detect changes and update database
                        if not df.equals(edited_df):
                            if st.button("Save Changes", type="primary"):
                                try:
                                    # Find the changed rows
                                    for index, row in edited_df.iterrows():
                                        if not df.iloc[index].equals(row):
                                            # Get primary key value for this row
                                            pk_values = {}
                                            for pk in primary_keys:
                                                pk_values[pk] = df.iloc[index][pk]
                                            
                                            # Build UPDATE statement
                                            update_cols = []
                                            update_vals = []
                                            
                                            for col in columns:
                                                if df.iloc[index][col] != row[col]:
                                                    update_cols.append(f"{col} = ?")
                                                    update_vals.append(row[col])
                                            
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
                        st.info("No data to display.")
                    
                # ADD ROW TAB
                with add_tab:
                    render_add_row_form(table, columns, primary_keys)
                
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
                                preview_query = f"SELECT * FROM {table} WHERE {where_clause} LIMIT 10"
                                conn = sqlite3.connect('attendance_system.db')
                                preview_df = execute_query_df(preview_query)
                                conn.close()
                                
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
                                    conn = sqlite3.connect('attendance_system.db')
                                    result_df = execute_query_df(query)
                                    conn.close()
                                    
                                    st.success("Query executed successfully!")
                                    st.dataframe(result_df, use_container_width=True)
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
            else:
                st.info("Select a table from above to view and manage its data.")
                st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
                create_new_table()

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
            if not new_table_name:
                st.error("Please provide a table name")
            else:
                # Check if any columns are defined and have names
                if not any(col["name"] for col in st.session_state.new_table_columns):
                    st.error("Please define at least one column with a name")
                else:
                    # Build CREATE TABLE statement
                    column_defs = []
                    for col in st.session_state.new_table_columns:
                        if col["name"]:
                            col_def = f"{col['name']} {col['type']}"
                            if col["pk"]:
                                col_def += " PRIMARY KEY"
                            column_defs.append(col_def)
                            
                    if column_defs:
                        create_stmt = f"CREATE TABLE {new_table_name} (\n" + ",\n".join(column_defs) + "\n);"
                        
                        # Execute create table
                        try:
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
    conn = sqlite3.connect('attendance_system.db')
    cursor = conn.cursor()
    
    # Get foreign key info
    execute_query(f"PRAGMA foreign_key_list({table_name})")
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
        execute_query(f"PRAGMA table_info({ref_table})")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'name' in columns:
            # Include both ID and name for better display
            execute_query(f"SELECT {ref_col}, name FROM {ref_table} ORDER BY name")
            values = [(str(row[0]), f"{row[0]} - {row[1]}") for row in cursor.fetchall()]
        else:
            # Just use the referenced column value
            execute_query(f"SELECT {ref_col} FROM {ref_table} ORDER BY {ref_col}")
            values = [(str(row[0]), str(row[0])) for row in cursor.fetchall()]
        
        return values
    except Exception as e:
        st.warning(f"Error fetching foreign key values: {e}")
        return []
    finally:
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
                        value = st.time_input(
                            col_name,
                            value=datetime.now().time(),
                            key=f"time_{table}_{col_name}"
                        )
                        # Format time as string for storage
                        new_row_data[col_name] = value.strftime("%H:%M:%S")
                        
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
        conn = self._get_db_connection()
        
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
                execute_query(f"PRAGMA table_info({self.table_name})")
                columns = [col[1] for col in cursor.fetchall()]
                if time_col in columns:
                    order_by = f"{time_col} DESC"
                    break
        
        # Apply order_by clause
        if order_by:
            query += f" ORDER BY {order_by}"
        elif self.primary_key:
            query += f" ORDER BY {self.primary_key}"
            
        query += f" LIMIT {limit} OFFSET {offset}"
        
        df = execute_query_df(query)
        
        # Get total row count
        count_query = f"SELECT COUNT(*) FROM {self.table_name}"
        if where_clause:
            count_query += f" WHERE {where_clause}"
        
        total_rows = execute_query_df(count_query).iloc[0, 0]
        
        conn.close()
        return df, total_rows

    # ... rest of the class methods ...

if __name__ == "__main__":
    show_db_explorer()