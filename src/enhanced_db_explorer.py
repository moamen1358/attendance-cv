import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import json
import re

# Constants
DATABASE_PATH = 'attendance_system.db'

# Field suggestions for common fields
DAY_SUGGESTIONS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
TIME_SUGGESTIONS = ['8:00 AM', '9:00 AM', '10:00 AM', '11:00 AM', '12:00 PM', '1:00 PM', '2:00 PM', 
                   '3:00 PM', '4:00 PM', '5:00 PM', '6:00 PM', '7:00 PM', '8:00 PM']
TYPE_SUGGESTIONS = ['lec', 'sec', 'lab', 'tut', 'sem']
SECTION_SUGGESTIONS = ['SEC 1', 'SEC 2']
TEACHER_TITLE_SUGGESTIONS = ['Dr.', 'Prof.', 'Mr.', 'Ms.', 'Mrs.']
ROLE_SUGGESTIONS = ['student', 'professor', 'admin']

def get_db_connection():
    """Create a connection to the database"""
    return sqlite3.connect(DATABASE_PATH)

def get_table_structure(table_name):
    """Get the structure of a table"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    
    # Column info format: (cid, name, type, notnull, dflt_value, pk)
    column_info = [{
        'cid': col[0],
        'name': col[1],
        'type': col[2].lower(),
        'notnull': col[3],
        'default': col[4],
        'pk': col[5]
    } for col in columns]
    
    conn.close()
    return column_info

def backup_database():
    """Create a backup of the database"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"attendance_system_backup_{timestamp}.db"
    
    try:
        with sqlite3.connect(DATABASE_PATH) as src_conn:
            with sqlite3.connect(backup_file) as backup_conn:
                src_conn.backup(backup_conn)
        st.success(f"Created database backup: {backup_file}")
        return True, backup_file
    except Exception as e:
        st.error(f"Failed to create backup: {e}")
        return False, None

def get_all_tables():
    """Get a list of all tables in the database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    return tables

def get_filtered_table_data(table_name, where_clause="", order_by="", limit=1000, offset=0):
    """Get data from a table with optional filtering"""
    conn = get_db_connection()
    
    query = f"SELECT * FROM {table_name}"
    
    if where_clause:
        query += f" WHERE {where_clause}"
        
    if order_by:
        query += f" ORDER BY {order_by}"
    else:
        # Try to order by primary key
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        for col in columns:
            if col[5] == 1:  # Primary key
                query += f" ORDER BY {col[1]}"
                break
    
    query += f" LIMIT {limit} OFFSET {offset}"
    
    df = pd.read_sql_query(query, conn)
    
    # Get total row count
    count_query = f"SELECT COUNT(*) FROM {table_name}"
    if where_clause:
        count_query += f" WHERE {where_clause}"
    
    total_rows = pd.read_sql_query(count_query, conn).iloc[0, 0]
    
    conn.close()
    return df, total_rows

def get_field_suggestions(column_name, column_type):
    """Get suggestions for common field types"""
    column_name = column_name.lower()
    
    # Check for day field
    if 'day' in column_name:
        return DAY_SUGGESTIONS
    
    # Check for time fields
    if 'time' in column_name:
        return TIME_SUGGESTIONS
    
    # Check for class type field
    if column_name == 'type':
        return TYPE_SUGGESTIONS
    
    # Check for section field
    if 'section' in column_name:
        return SECTION_SUGGESTIONS
        
    # Check for role field
    if 'role' in column_name:
        return ROLE_SUGGESTIONS
    
    # Boolean fields
    if column_type in ('boolean', 'bool'):
        return [True, False]
    
    # Default - no suggestions
    return None

def get_unique_values(table_name, column_name, limit=100):
    """Get unique values from a column for suggestions"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(f"SELECT DISTINCT {column_name} FROM {table_name} LIMIT {limit}")
        values = [row[0] for row in cursor.fetchall() if row[0] is not None]
        return values
    except:
        return []
    finally:
        conn.close()

def delete_record(table_name, pk_column, pk_value):
    """Delete a record from a table"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Create a backup before deleting
        backup_success, _ = backup_database()
        if not backup_success:
            if not st.warning("Failed to create backup. Continue anyway?", icon="⚠️"):
                st.error("Delete operation canceled")
                return False
        
        # Delete the record
        cursor.execute(f"DELETE FROM {table_name} WHERE {pk_column} = ?", (pk_value,))
        conn.commit()
        
        rows_affected = cursor.rowcount
        if rows_affected > 0:
            st.success(f"Deleted {rows_affected} record(s)")
            return True
        else:
            st.warning("No records were deleted")
            return False
    except Exception as e:
        st.error(f"Error deleting record: {e}")
        return False
    finally:
        conn.close()

def bulk_delete_records(table_name, where_clause):
    """Delete multiple records based on a WHERE clause"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # First count how many records will be deleted
        cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE {where_clause}")
        count = cursor.fetchone()[0]
        
        if count == 0:
            st.warning("No records match the criteria")
            return False
            
        # Create a backup before deleting
        backup_success, _ = backup_database()
        if not backup_success:
            if not st.warning("Failed to create backup. Continue anyway?", icon="⚠️"):
                st.error("Delete operation canceled")
                return False
        
        # Delete the records
        cursor.execute(f"DELETE FROM {table_name} WHERE {where_clause}")
        conn.commit()
        
        rows_affected = cursor.rowcount
        if rows_affected > 0:
            st.success(f"Deleted {rows_affected} record(s)")
            return True
        else:
            st.warning("No records were deleted")
            return False
    except Exception as e:
        st.error(f"Error deleting records: {e}")
        return False
    finally:
        conn.close()

def insert_record(table_name, values):
    """Insert a new record into a table"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Filter out None values from autoincrement primary keys
        columns = []
        filtered_values = []
        
        for col, val in values.items():
            if val is not None:
                columns.append(col)
                filtered_values.append(val)
        
        # Build and execute query
        columns_str = ', '.join(columns)
        placeholders = ', '.join(['?' for _ in columns])
        
        query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
        
        cursor.execute(query, filtered_values)
        conn.commit()
        
        st.success(f"Record inserted successfully (ID: {cursor.lastrowid})")
        return True
    except Exception as e:
        st.error(f"Error inserting record: {e}")
        return False
    finally:
        conn.close()

def update_record(table_name, pk_column, pk_value, values):
    """Update a record in a table"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Filter out None values and the primary key
        updates = {k: v for k, v in values.items() if k != pk_column and v is not None}
        
        if not updates:
            st.warning("No fields to update")
            return False
        
        # Build and execute query
        set_clause = ', '.join([f"{col} = ?" for col in updates.keys()])
        values_list = list(updates.values()) + [pk_value]  # Add pk_value at the end for WHERE clause
        
        query = f"UPDATE {table_name} SET {set_clause} WHERE {pk_column} = ?"
        
        cursor.execute(query, values_list)
        conn.commit()
        
        if cursor.rowcount > 0:
            st.success(f"Record updated successfully")
            return True
        else:
            st.warning("No changes made")
            return False
    except Exception as e:
        st.error(f"Error updating record: {e}")
        return False
    finally:
        conn.close()

def execute_custom_query(query, is_select=True):
    """Execute a custom SQL query"""
    conn = get_db_connection()
    
    try:
        if is_select:
            # SELECT query
            df = pd.read_sql_query(query, conn)
            return True, df
        else:
            # Non-SELECT query
            cursor = conn.cursor()
            cursor.execute(query)
            conn.commit()
            return True, cursor.rowcount
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

def render_editable_table(df, table_name, column_info):
    """Render an editable table with delete buttons"""
    # Identify primary key column
    pk_column = next((col['name'] for col in column_info if col['pk'] == 1), None)
    
    # If no primary key, we can't provide edit/delete functionality
    if not pk_column:
        st.warning("This table has no primary key. Limited edit functionality available.")
        st.dataframe(df)
        return
    
    # Allow editing with Streamlit's built-in data editor
    edited_df = st.data_editor(
        df,
        use_container_width=True,
        height=400,
        hide_index=True,
        num_rows="fixed",
    )
    
    # Check for any changes
    if not df.equals(edited_df):
        changes = ~(df == edited_df).all(axis=1)
        changed_rows = df[changes]
        
        if not changed_rows.empty:
            st.info(f"Changes detected in {len(changed_rows)} row(s)")
            
            if st.button("Save Changes"):
                # Update each changed row
                for idx in changed_rows.index:
                    pk_value = df.loc[idx, pk_column]  # Get primary key value from original data
                    new_values = edited_df.loc[idx].to_dict()  # Get new values
                    
                    # Update the record
                    update_record(table_name, pk_column, pk_value, new_values)
                
                st.rerun()  # Refresh to show updated data

    # Add delete functionality
    with st.expander("Delete Records"):
        # Option 1: Delete by primary key
        st.subheader("Delete by Primary Key")
        pk_values = df[pk_column].tolist()
        selected_pk = st.selectbox(f"Select {pk_column} to delete:", pk_values)
        
        if st.button("Delete Selected Record"):
            confirm = st.checkbox("I confirm I want to delete this record")
            if confirm:
                if delete_record(table_name, pk_column, selected_pk):
                    st.rerun()
        
        # Option 2: Bulk delete with WHERE clause
        st.subheader("Bulk Delete")
        where_clause = st.text_input("WHERE clause:", placeholder="e.g., active = 0 or name = 'John'")
        
        if where_clause and st.button("Delete Matching Records"):
            # Show preview of what will be deleted
            try:
                preview_query = f"SELECT * FROM {table_name} WHERE {where_clause} LIMIT 10"
                success, preview_data = execute_custom_query(preview_query)
                
                if success:
                    if not preview_data.empty:
                        st.write(f"Preview of records to be deleted (showing up to 10):")
                        st.dataframe(preview_data)
                        
                        # Count total
                        count_query = f"SELECT COUNT(*) FROM {table_name} WHERE {where_clause}"
                        _, count_result = execute_custom_query(count_query)
                        total_count = count_result.iloc[0, 0]
                        
                        st.warning(f"This will delete {total_count} record(s)")
                        
                        confirm = st.checkbox(f"I confirm I want to delete these {total_count} records")
                        if confirm and st.button("Confirm Delete"):
                            if bulk_delete_records(table_name, where_clause):
                                st.rerun()
                    else:
                        st.info("No records match this criteria")
                else:
                    st.error(f"Error previewing records: {preview_data}")
            except Exception as e:
                st.error(f"Error in WHERE clause: {e}")

def add_new_record_form(table_name, column_info):
    """Create a form to add a new record with smart suggestions"""
    with st.expander("Add New Record", expanded=False):
        with st.form(key=f"add_record_{table_name}"):
            # Create input fields for each column
            values = {}
            
            for col in column_info:
                col_name = col['name']
                col_type = col['type']
                is_pk = col['pk'] == 1
                not_null = col['notnull'] == 1
                default_val = col['default']
                
                # Skip autoincrement primary keys
                if is_pk and col_type == 'integer':
                    values[col_name] = None
                    continue
                
                # Format label
                label = f"{col_name} ({col_type})"
                if not_null:
                    label += " *"
                
                # Get suggestions for this field
                suggestions = get_field_suggestions(col_name, col_type)
                
                # If no predefined suggestions, try to get unique values from the table
                if not suggestions and not is_pk:
                    suggestions = get_unique_values(table_name, col_name)
                
                # Create appropriate input widget based on column type and suggestions
                if suggestions:
                    # Add "Other" option for custom input
                    if not isinstance(suggestions, (bool, int, float)):
                        suggestions = list(suggestions) + ["-- Custom --"]
                    
                    selection = st.selectbox(
                        label, 
                        options=suggestions,
                        key=f"add_{table_name}_{col_name}"
                    )
                    
                    # Handle custom input
                    if selection == "-- Custom --":
                        custom_value = st.text_input(
                            f"Custom {col_name}:",
                            key=f"custom_{table_name}_{col_name}"
                        )
                        values[col_name] = custom_value
                    else:
                        values[col_name] = selection
                
                elif 'date' in col_type:
                    # Date picker
                    values[col_name] = st.date_input(
                        label,
                        value=datetime.now().date(),
                        key=f"add_{table_name}_{col_name}"
                    )
                
                elif 'time' in col_type or ('time' in col_name.lower() and 'stamp' not in col_name.lower()):
                    # Time input for time fields
                    values[col_name] = st.time_input(
                        label,
                        value=datetime.now().time(),
                        key=f"add_{table_name}_{col_name}"
                    )
                    
                    # Convert time to string for storage
                    if values[col_name]:
                        values[col_name] = values[col_name].strftime("%H:%M:%S")
                
                elif 'int' in col_type:
                    # Integer input
                    values[col_name] = st.number_input(
                        label,
                        step=1,
                        value=0 if not_null else None,
                        key=f"add_{table_name}_{col_name}"
                    )
                
                elif col_type in ('real', 'double', 'float'):
                    # Float input
                    values[col_name] = st.number_input(
                        label,
                        value=0.0 if not_null else None,
                        key=f"add_{table_name}_{col_name}"
                    )
                
                elif col_type in ('boolean', 'bool'):
                    # Boolean input
                    values[col_name] = st.checkbox(
                        label,
                        key=f"add_{table_name}_{col_name}"
                    )
                
                else:
                    # Default text input
                    values[col_name] = st.text_input(
                        label,
                        key=f"add_{table_name}_{col_name}"
                    )
            
            submit = st.form_submit_button("Add Record")
            
            if submit:
                # Check required fields
                missing_fields = [col['name'] for col in column_info 
                                 if col['notnull'] == 1 and not col['pk'] and not values.get(col['name'])]
                
                if missing_fields:
                    st.error(f"Missing required fields: {', '.join(missing_fields)}")
                else:
                    # Insert the record
                    if insert_record(table_name, values):
                        st.rerun()  # Refresh to show the new record

def show_table_browser(table_name):
    """Show table data browser with filtering and visualization"""
    st.subheader(f"Browse Table: {table_name}")
    
    # Get table structure
    column_info = get_table_structure(table_name)
    
    # Filter options
    with st.expander("Filter & Sort", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            where_clause = st.text_input("WHERE clause:", key=f"where_{table_name}", 
                                        placeholder="e.g., name LIKE '%John%'")
            
        with col2:
            # Get column names for ORDER BY suggestion
            column_names = [col['name'] for col in column_info]
            order_by = st.selectbox("Order by:", 
                                  options=[""] + [f"{col} ASC" for col in column_names] + 
                                           [f"{col} DESC" for col in column_names],
                                  key=f"order_{table_name}")
    
    # Get and display data
    df, total_rows = get_filtered_table_data(table_name, where_clause, order_by)
    
    # Show record count
    st.info(f"Showing {len(df)} of {total_rows} records")
    
    # Display editable table with deletion capability
    render_editable_table(df, table_name, column_info)
    
    # Add form to add new records with smart suggestions
    add_new_record_form(table_name, column_info)

def show_sql_editor():
    """Show SQL editor with query history"""
    st.subheader("SQL Query Editor")
    
    # Initialize query history in session state
    if 'query_history' not in st.session_state:
        st.session_state.query_history = []
    
    # Query input
    with st.expander("Query History", expanded=False):
        history = st.session_state.query_history
        
        if history:
            selected_idx = st.selectbox(
                "Select previous query:", 
                options=range(len(history)),
                format_func=lambda i: f"{i+1}. {history[i][:50]}{'...' if len(history[i]) > 50 else ''}"
            )
            
            if st.button("Load Selected Query"):
                st.session_state.current_query = history[selected_idx]
        else:
            st.info("No query history yet")
    
    # Query input
    if 'current_query' not in st.session_state:
        st.session_state.current_query = ""
        
    query = st.text_area("SQL Query:", 
                       value=st.session_state.current_query,
                       height=150, 
                       placeholder="SELECT * FROM table_name")
    
    col1, col2 = st.columns(2)
    
    with col1:
        execute = st.button("Execute Query", type="primary")
    
    with col2:
        is_select = st.checkbox("SELECT query", value=query.strip().lower().startswith('select'))
    
    if execute and query:
        # Save to history if not already there
        if query not in st.session_state.query_history:
            st.session_state.query_history.append(query)
            if len(st.session_state.query_history) > 20:  # Keep only last 20
                st.session_state.query_history.pop(0)
        
        # Execute query
        success, result = execute_custom_query(query, is_select)
        
        if success:
            if is_select:
                st.success("Query executed successfully")
                if isinstance(result, pd.DataFrame):
                    if not result.empty:
                        st.dataframe(result)
                        
                        # Export options
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            if st.button("Export to CSV"):
                                csv = result.to_csv(index=False)
                                st.download_button(
                                    label="Download CSV",
                                    data=csv,
                                    file_name=f"query_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                    mime="text/csv"
                                )
                        
                        with col2:
                            if st.button("Export to Excel"):
                                try:
                                    excel_buffer = io.BytesIO()
                                    result.to_excel(excel_buffer, index=False)
                                    excel_buffer.seek(0)
                                    
                                    st.download_button(
                                        label="Download Excel",
                                        data=excel_buffer,
                                        file_name=f"query_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                    )
                                except Exception as e:
                                    st.error(f"Error exporting to Excel: {e}")
                        
                        with col3:
                            if st.button("Export to JSON"):
                                json_str = result.to_json(orient="records")
                                st.download_button(
                                    label="Download JSON",
                                    data=json_str,
                                    file_name=f"query_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                                    mime="application/json"
                                )
                    else:
                        st.info("Query returned no rows")
                else:
                    st.write(result)
            else:
                st.success(f"Query executed successfully. Rows affected: {result}")
        else:
            st.error(f"Error executing query: {result}")

def show_db_maintenance():
    """Show database maintenance tools"""
    st.subheader("Database Maintenance")
    
    maintenance_option = st.radio(
        "Select Maintenance Operation:",
        options=["Create Backup", "Vacuum Database", "Analyze Tables", "Check Foreign Key Constraints"]
    )
    
    if maintenance_option == "Create Backup":
        if st.button("Create Database Backup", type="primary"):
            backup_database()
    
    elif maintenance_option == "Vacuum Database":
        st.info("Vacuum rebuilds the database to reclaim unused space and optimize performance.")
        if st.button("Vacuum Database", type="primary"):
            conn = get_db_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("VACUUM")
                st.success("Database vacuum completed successfully")
            except Exception as e:
                st.error(f"Error vacuuming database: {e}")
            finally:
                conn.close()
    
    elif maintenance_option == "Analyze Tables":
        st.info("Analyze collects statistics about tables that help optimize future queries.")
        if st.button("Analyze Tables", type="primary"):
            conn = get_db_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("ANALYZE")
                st.success("Tables analyzed successfully")
            except Exception as e:
                st.error(f"Error analyzing tables: {e}")
            finally:
                conn.close()
    
    elif maintenance_option == "Check Foreign Key Constraints":
        st.info("Check for foreign key constraint violations in the database.")
        if st.button("Check Foreign Key Constraints", type="primary"):
            conn = get_db_connection()
            try:
                cursor = conn.cursor()
                cursor.execute("PRAGMA foreign_key_check")
                violations = cursor.fetchall()
                
                if violations:
                    st.error("Foreign key violations found:")
                    violations_df = pd.DataFrame(violations, 
                                               columns=["Table", "RowId", "Parent", "Foreign Key"])
                    st.dataframe(violations_df)
                else:
                    st.success("No foreign key violations found")
            except Exception as e:
                st.error(f"Error checking foreign key constraints: {e}")
            finally:
                conn.close()

def show_db_explorer():
    """Main function for database explorer"""
    st.title("Enhanced Database Explorer")
    
    # Get list of tables
    tables = get_all_tables()
    
    if not tables:
        st.warning("No tables found in the database")
        return
        
    # Sidebar with navigation
    st.sidebar.title("Database Explorer")
    option = st.sidebar.radio(
        "Select Option:",
        options=["Browse Tables", "SQL Editor", "Database Maintenance"]
    )
    
    if option == "Browse Tables":
        # Table selection
        selected_table = st.sidebar.selectbox("Select Table:", tables)
        show_table_browser(selected_table)
        
    elif option == "SQL Editor":
        show_sql_editor()
        
    elif option == "Database Maintenance":
        show_db_maintenance()
        
if __name__ == "__main__":
    show_db_explorer()
