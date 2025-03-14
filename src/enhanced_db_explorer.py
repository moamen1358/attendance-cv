import streamlit as st
import sqlite3
import pandas as pd
import re
from datetime import datetime

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
    """Get list of all tables in the database"""
    result = execute_query("SELECT name FROM sqlite_master WHERE type='table';", fetch=True)
    return [table[0] for table in result] if result else []

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
    
    # Move table selection to main content
    tables = st.session_state.tables
    
    if not tables:
        st.info("No tables found in the database. Create a new table below.")
        
        # Move create table functionality to main content for empty database
        create_new_table()
    else:
        # Table selection at the top of main content
        # Modified to use full width instead of columns since refresh button is removed
        selected_table = st.selectbox(
            "Select Table",
            tables,
            index=tables.index(st.session_state.selected_table) if st.session_state.selected_table in tables else 0,
            key="table_selector"
        )
        
        if selected_table != st.session_state.selected_table:
            st.session_state.selected_table = selected_table
            st.session_state.editing_row = None
            st.session_state.search_term = ""
            st.rerun()
        
        table = st.session_state.selected_table
        columns = get_column_names(table)
        primary_keys = get_primary_key(table)
        
        # Get row count
        row_count_result = execute_query(f"SELECT COUNT(*) FROM {table};", fetch=True)
        row_count = row_count_result[0][0] if row_count_result else 0
        
        # Table header with stats
        st.markdown(f"""
        <div style="background-color:#f5f5f5; padding:10px; border-radius:5px; margin:10px 0;">
            <h3 style="margin:0;">📊 {table}</h3>
            <p style="margin:5px 0;"><b>Columns:</b> {len(columns)} | <b>Rows:</b> {row_count} | <b>Primary Key:</b> {', '.join(primary_keys) if primary_keys else 'None'}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Create tabs for different operations - UPDATED to include Database Operations tab
        view_tab, add_tab, delete_tab, sql_tab, manage_tab = st.tabs(["View Data", "Add Row", "Delete Records", "SQL Query", "Database Operations"])
        
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
                df = pd.read_sql_query(search_query, conn, params=search_params)
                conn.close()
            else:
                # Simple query without pagination
                query = f"SELECT * FROM {table};"
                conn = sqlite3.connect('attendance_system.db')
                df = pd.read_sql_query(query, conn)
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
                        preview_df = pd.read_sql_query(preview_query, conn)
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
                            result_df = pd.read_sql_query(query, conn)
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
        
        # DATABASE OPERATIONS TAB (new)
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
    
    # Remove database info sidebar completely - keep empty sidebar to prevent layout issues
    with st.sidebar:
        # Empty sidebar
        pass

# Add a new function for creating tables to avoid code duplication
def create_new_table():
    """Create a new table form component"""
    new_table_name = st.text_input("Table Name", key="new_table_name_main")
    
    # Column definition section
    st.write("Define Columns:")
    col1, col2, col3 = st.columns([3, 2, 1])
    with col1:
        st.write("Name")
    with col2:
        st.write("Type")
    with col3:
        st.write("PK")
        
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
    
    # Add column button
    if st.button("➕ Add Column", key="add_column_main"):
        st.session_state.new_table_columns.append({"name": "", "type": "TEXT", "pk": False})
        st.rerun()
    
    # Create table button
    if st.button("Create Table", key="create_table_main"):
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

# Add these new helper functions for improved input fields
def get_foreign_key_values(table_name, column_name):
    """Get possible values for a foreign key column"""
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

if __name__ == "__main__":
    show_db_explorer()