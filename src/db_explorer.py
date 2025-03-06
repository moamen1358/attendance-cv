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
    if 'page_number' not in st.session_state:
        st.session_state.page_number = 0
    if 'rows_per_page' not in st.session_state:
        st.session_state.rows_per_page = 10
    
    # Sidebar for table selection and operations
    with st.sidebar:
        st.header("Database Tables")
        
        # Refresh tables button
        if st.button("🔄 Refresh Tables"):
            st.session_state.tables = get_tables()
            st.rerun()
        
        # Table selection
        selected_table = st.selectbox(
            "Select Table",
            st.session_state.tables,
            index=st.session_state.tables.index(st.session_state.selected_table) if st.session_state.selected_table in st.session_state.tables else 0,
            key="table_selector"
        )
        
        if selected_table != st.session_state.selected_table:
            st.session_state.selected_table = selected_table
            st.session_state.editing_row = None
            st.session_state.page_number = 0
            st.session_state.search_term = ""
            st.rerun()
        
        # Table operations
        st.subheader("Table Operations")
        
        with st.expander("Create New Table"):
            new_table_name = st.text_input("Table Name", key="new_table_name")
            
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
                    col_name = st.text_input("", value=col["name"], key=f"col_name_{i}")
                with col2:
                    col_type = st.selectbox("", ["TEXT", "INTEGER", "REAL", "BLOB", "DATETIME"], 
                                           index=["TEXT", "INTEGER", "REAL", "BLOB", "DATETIME"].index(col["type"]),
                                           key=f"col_type_{i}")
                with col3:
                    col_pk = st.checkbox("", value=col["pk"], key=f"col_pk_{i}")
                with col4:
                    # Only show delete button if there's more than one column
                    if len(st.session_state.new_table_columns) > 1:
                        if st.button("❌", key=f"del_col_{i}"):
                            st.session_state.new_table_columns.pop(i)
                            st.rerun()
                            
                columns_to_add.append({"name": col_name, "type": col_type, "pk": col_pk})
            
            # Update column definitions
            st.session_state.new_table_columns = columns_to_add
            
            # Add column button
            if st.button("➕ Add Column"):
                st.session_state.new_table_columns.append({"name": "", "type": "TEXT", "pk": False})
                st.rerun()
            
            # Create table button
            if st.button("Create Table"):
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
        
        # Delete table option
        with st.expander("Delete Table"):
            st.warning(f"Are you sure you want to delete table '{selected_table}'?\nThis action cannot be undone!")
            confirm_name = st.text_input("Type the table name to confirm deletion:", key="confirm_delete")
            
            if st.button("🗑️ DELETE TABLE", type="primary", use_container_width=True):
                if confirm_name == selected_table:
                    execute_query(f"DROP TABLE {selected_table};", commit=True)
                    st.success(f"Table '{selected_table}' deleted successfully!")
                    st.session_state.tables = get_tables()
                    if st.session_state.tables:
                        st.session_state.selected_table = st.session_state.tables[0]
                    else:
                        st.session_state.selected_table = None
                    st.rerun()
                else:
                    st.error("Table name doesn't match. Deletion cancelled.")
    
    # Main content area
    if not st.session_state.selected_table:
        st.info("No tables found in the database. Create a new table using the sidebar.")
        return
    
    table = st.session_state.selected_table
    columns = get_column_names(table)
    primary_keys = get_primary_key(table)
    
    # Get row count
    row_count_result = execute_query(f"SELECT COUNT(*) FROM {table};", fetch=True)
    row_count = row_count_result[0][0] if row_count_result else 0
    
    # Table header with stats
    st.header(f"Table: {table}")
    st.write(f"Columns: {', '.join(columns)}")
    st.write(f"Primary Key: {', '.join(primary_keys) if primary_keys else 'None'}")
    st.write(f"Total Rows: {row_count}")
    
    # Search and pagination controls
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        search_term = st.text_input("🔍 Search in any column:", value=st.session_state.search_term)
        if search_term != st.session_state.search_term:
            st.session_state.search_term = search_term
            st.session_state.page_number = 0
            st.rerun()
    
    with col2:
        rows_per_page = st.selectbox("Rows per page:", [10, 25, 50, 100], index=[10, 25, 50, 100].index(st.session_state.rows_per_page))
        if rows_per_page != st.session_state.rows_per_page:
            st.session_state.rows_per_page = rows_per_page
            st.session_state.page_number = 0
            st.rerun()
    
    with col3:
        page_count = max(1, (row_count + rows_per_page - 1) // rows_per_page)
        page = st.number_input("Page:", min_value=1, max_value=page_count, value=st.session_state.page_number + 1)
        if page != st.session_state.page_number + 1:
            st.session_state.page_number = page - 1
            st.rerun()
    
    # Build query with search and pagination
    offset = st.session_state.page_number * st.session_state.rows_per_page
    
    if st.session_state.search_term:
        # Build search condition for each column
        search_conditions = []
        for col in columns:
            search_conditions.append(f"{col} LIKE ?")
        
        # Combine conditions with OR
        search_query = f"SELECT * FROM {table} WHERE " + " OR ".join(search_conditions)
        search_query += f" LIMIT {rows_per_page} OFFSET {offset}"
        
        # Prepare search parameters
        search_params = [f"%{st.session_state.search_term}%"] * len(columns)
        
        # Execute search query
        conn = sqlite3.connect('attendance_system.db')
        df = pd.read_sql_query(search_query, conn, params=search_params)
        conn.close()
    else:
        # Simple pagination query
        query = f"SELECT * FROM {table} LIMIT {rows_per_page} OFFSET {offset};"
        conn = sqlite3.connect('attendance_system.db')
        df = pd.read_sql_query(query, conn)
        conn.close()
    
    # Add new row form
    with st.expander("➕ Add New Row"):
        with st.form("add_row_form"):
            # Create input fields for each column
            new_row_data = {}
            for col in columns:
                # Skip auto-increment primary keys
                if col in primary_keys and len(primary_keys) == 1 and "INTEGER" in get_table_columns(table)[columns.index(col)][2].upper():
                    st.text_input(col, value="(Auto)", disabled=True)
                else:
                    new_row_data[col] = st.text_input(col, key=f"new_{col}")
            
            submitted = st.form_submit_button("Add Row")
            if submitted:
                # Prepare column names and values for non-auto-increment fields
                cols_to_insert = []
                vals_to_insert = []
                for col, val in new_row_data.items():
                    # Skip empty auto-increment primary keys
                    if col in primary_keys and len(primary_keys) == 1 and "INTEGER" in get_table_columns(table)[columns.index(col)][2].upper() and not val:
                        continue
                    cols_to_insert.append(col)
                    vals_to_insert.append(val)
                
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
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error adding row: {e}")
    
    # Display table data with edit/delete buttons
    if not df.empty:
        # Add edit/delete buttons to each row
        edit_col, table_container, delete_col = st.columns([0.5, 10, 0.5])
        
        with table_container:
            edited_df = st.data_editor(
                df,
                hide_index=True,
                use_container_width=True,
                num_rows="fixed",
                key="data_editor"
            )
            
            # Detect changes and update database
            if not df.equals(edited_df):
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
        
        # Delete buttons
        with delete_col:
            for i in range(len(df)):
                if st.button("🗑️", key=f"delete_{i}"):
                    try:
                        # If no primary key exists, use all columns for matching
                        if not primary_keys:
                            # Use all columns as identifiers
                            where_conditions = []
                            delete_vals = []
                            for col in columns:
                                where_conditions.append(f"{col} = ?")
                                # Handle None/NaN values
                                val = df.iloc[i][col]
                                if pd.isna(val):
                                    where_conditions[-1] = f"{col} IS NULL"
                                else:
                                    delete_vals.append(val)
                        else:
                            # Use primary keys
                            where_conditions = []
                            delete_vals = []
                            for pk in primary_keys:
                                val = df.iloc[i][pk]
                                if pd.isna(val):
                                    where_conditions.append(f"{pk} IS NULL")
                                else:
                                    where_conditions.append(f"{pk} = ?")
                                    delete_vals.append(val)
                        
                        # Build and execute DELETE statement
                        delete_stmt = f"DELETE FROM {table} WHERE " + " AND ".join(where_conditions)
                        
                        # Show debug info
                        st.info(f"Executing: {delete_stmt} with values: {delete_vals}")
                        
                        # Execute delete
                        execute_query(delete_stmt, tuple(delete_vals), commit=True)
                        st.success("Row deleted successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error deleting row: {str(e)}")
    else:
        st.info("No data to display. Add some rows using the form above.")
    
    # Custom SQL query section
    with st.expander("Run Custom SQL Query"):
        query = st.text_area("Enter SQL Query:", height=100)
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔍 Execute SELECT Query"):
                if query.strip().upper().startswith("SELECT"):
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
            if st.button("⚠️ Execute Action Query", type="primary"):
                if query.strip().upper().startswith(("INSERT", "UPDATE", "DELETE")):
                    try:
                        execute_query(query, commit=True)
                        st.success("Query executed successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error executing query: {e}")
                else:
                    st.error("Only INSERT, UPDATE, or DELETE queries are allowed with this button.")

if __name__ == "__main__":
    show_db_explorer()