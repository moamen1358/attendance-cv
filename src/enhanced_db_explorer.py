import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import json
import re
import io
from PIL import Image
import base64

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

# Table icons dictionary - add icons for known tables
TABLE_ICONS = {
    'class_schedules': '📅',
    'attendance_records': '📝',
    'student_profiles': '👨‍🎓',
    'user_accounts': '👤',
    'facial_recognition_data': '👁️',
    'teacher_subjects': '👩‍🏫',
    'class_attendance_records': '✓',
    'system_metadata': '⚙️',
    'sqlite_sequence': '🔢'
}

# Color scheme for tables
TABLE_COLORS = {
    'class_schedules': '#4CAF50',
    'attendance_records': '#2196F3',
    'student_profiles': '#FF9800',
    'user_accounts': '#9C27B0',
    'facial_recognition_data': '#F44336',
    'teacher_subjects': '#3F51B5',
    'class_attendance_records': '#607D8B',
    'system_metadata': '#795548',
}

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

def get_table_stats(table_name):
    """Get statistics about a table"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    stats = {
        'name': table_name,
        'icon': TABLE_ICONS.get(table_name, '📊'),
        'color': TABLE_COLORS.get(table_name, '#757575'),
        'row_count': 0,
        'column_count': 0,
        'has_primary_key': False,
        'last_updated': None,
        'size_kb': 0,
        'related_tables': []
    }
    
    try:
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        stats['row_count'] = cursor.fetchone()[0]
        
        # Get column count and check for primary key
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        stats['column_count'] = len(columns)
        
        # Check for primary key
        for col in columns:
            if col[5] == 1:  # pk flag
                stats['has_primary_key'] = True
                break
        
        # Get last updated time (if created_at or updated_at column exists)
        try:
            cursor.execute(f"SELECT MAX(created_at) FROM {table_name}")
            stats['last_updated'] = cursor.fetchone()[0]
        except:
            try:
                cursor.execute(f"SELECT MAX(updated_at) FROM {table_name}")
                stats['last_updated'] = cursor.fetchone()[0]
            except:
                pass
        
        # Get foreign keys to find related tables
        cursor.execute(f"PRAGMA foreign_key_list({table_name})")
        foreign_keys = cursor.fetchall()
        
        for fk in foreign_keys:
            stats['related_tables'].append(fk[2])  # [2] is the referenced table
        
        # Get approximate size (very rough estimate)
        try:
            # Sample some rows to get average row size
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 10")
            sample = cursor.fetchall()
            
            if sample:
                # Estimate row size based on sample
                sample_str = str(sample)
                avg_row_size = len(sample_str) / len(sample)
                stats['size_kb'] = round((avg_row_size * stats['row_count']) / 1024, 2)
        except:
            pass
        
    except Exception as e:
        print(f"Error getting stats for table {table_name}: {e}")
    
    conn.close()
    return stats

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

def delete_record_by_column(table_name, column_name, column_value):
    """Delete a record from a table based on any column value"""
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
        cursor.execute(f"DELETE FROM {table_name} WHERE {column_name} = ?", (column_value,))
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

def render_editable_table(df, table_name, column_info):
    """Render an editable table with enhanced delete buttons"""
    # Identify primary key column
    pk_column = next((col['name'] for col in column_info if col['pk'] == 1), None)
    
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
                    pk_value = df.loc[idx, pk_column] if pk_column else idx  # Use index if no PK
                    new_values = edited_df.loc[idx].to_dict()  # Get new values
                    
                    # Update the record
                    if pk_column:
                        update_record(table_name, pk_column, pk_value, new_values)
                    else:
                        st.warning(f"Cannot update row {idx} - no primary key available")
                
                st.rerun()  # Refresh to show updated data

    # Add delete functionality
    with st.expander("Delete Records", expanded=False):
        st.subheader("Delete Options")
        
        # Option 1: Delete by any column
        st.markdown("#### Delete by Column Value")
        
        # Select any column
        column_options = df.columns.tolist()
        selected_column = st.selectbox("Select column:", column_options)
        
        # Get unique values from the selected column
        unique_values = df[selected_column].unique()
        selected_value = st.selectbox(f"Select value from {selected_column}:", unique_values)
        
        if st.button("Delete Records with Selected Value"):
            confirm = st.checkbox("I confirm I want to delete records where " + 
                               f"{selected_column} = '{selected_value}'")
            if confirm:
                if delete_record_by_column(table_name, selected_column, selected_value):
                    st.rerun()
        
        # Option 2: Bulk delete with WHERE clause
        st.markdown("#### Advanced: Delete with WHERE Clause")
        where_clause = st.text_input("WHERE clause:", placeholder="e.g., active = 0 or name = 'John'")
        
        if where_clause and st.button("Preview Matching Records"):
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

def create_data_visualization(df, table_name):
    """Create visualizations for data exploration"""
    if df.empty:
        st.info("No data available for visualization")
        return
    
    # Only show visualization options if there's enough data
    if len(df) < 2:
        st.info("Not enough data for visualization")
        return
    
    st.subheader("Data Visualization")
    
    # Determine which columns might be good for visualization
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
    date_cols = []
    
    # Try to identify date columns
    for col in df.columns:
        if 'date' in col.lower() or 'time' in col.lower():
            try:
                pd.to_datetime(df[col])
                date_cols.append(col)
            except:
                pass
    
    # Let user choose visualization type
    viz_type = st.selectbox(
        "Select Visualization Type:",
        options=[
            "Bar Chart (Categorical)",
            "Line Chart (Time Series)",
            "Scatter Plot (Correlation)",
            "Histogram (Distribution)",
            "Box Plot (Distribution)"
        ]
    )
    
    if viz_type == "Bar Chart (Categorical)":
        if not categorical_cols:
            st.warning("No categorical columns available for bar chart")
            return
            
        col1, col2 = st.columns(2)
        
        with col1:
            cat_col = st.selectbox("Select Category Column:", categorical_cols)
        
        with col2:
            if numeric_cols:
                value_col = st.selectbox("Select Value Column (optional):", ["Count"] + numeric_cols)
            else:
                value_col = "Count"
        
        # Create dataframe for the chart
        if value_col == "Count":
            chart_data = df[cat_col].value_counts().reset_index()
            chart_data.columns = [cat_col, 'Count']
            
            # Create bar chart
            fig = px.bar(
                chart_data,
                x=cat_col,
                y='Count',
                title=f"Count of {cat_col} in {table_name}",
                labels={cat_col: cat_col, 'Count': 'Count'},
                color_discrete_sequence=['#2196F3'],
                template="plotly_white"
            )
        else:
            # Group by category and calculate mean of value column
            chart_data = df.groupby(cat_col)[value_col].agg(['mean', 'sum', 'count']).reset_index()
            
            # Create bar chart with option to show mean or sum
            agg_func = st.radio("Aggregation:", ["Mean", "Sum", "Count"], horizontal=True)
            
            agg_map = {"Mean": "mean", "Sum": "sum", "Count": "count"}
            selected_agg = agg_map[agg_func]
            
            fig = px.bar(
                chart_data,
                x=cat_col,
                y=selected_agg,
                title=f"{agg_func} of {value_col} by {cat_col} in {table_name}",
                labels={cat_col: cat_col, selected_agg: f"{agg_func} of {value_col}"},
                color_discrete_sequence=['#2196F3'],
                template="plotly_white"
            )
        
        st.plotly_chart(fig, use_container_width=True)
        
    elif viz_type == "Line Chart (Time Series)":
        if not date_cols:
            st.warning("No date/time columns detected for time series chart")
            return
            
        col1, col2 = st.columns(2)
        
        with col1:
            date_col = st.selectbox("Select Date/Time Column:", date_cols)
        
        with col2:
            if numeric_cols:
                value_col = st.selectbox("Select Value Column:", ["Count"] + numeric_cols)
            else:
                value_col = "Count"
        
        # Create dataframe for time series
        try:
            # Convert to datetime
            chart_df = df.copy()
            chart_df[date_col] = pd.to_datetime(chart_df[date_col])
            
            # Group by date
            if value_col == "Count":
                # Count records by date
                chart_data = chart_df.groupby(pd.Grouper(key=date_col, freq='D')).size().reset_index()
                chart_data.columns = [date_col, 'Count']
                y_col = 'Count'
            else:
                # Group by date and calculate mean
                chart_data = chart_df.groupby(pd.Grouper(key=date_col, freq='D'))[value_col].mean().reset_index()
                y_col = value_col
            
            # Create line chart
            fig = px.line(
                chart_data,
                x=date_col,
                y=y_col,
                title=f"{y_col} Over Time in {table_name}",
                labels={date_col: "Date", y_col: y_col},
                template="plotly_white"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error creating time series chart: {e}")
    
    elif viz_type == "Scatter Plot (Correlation)":
        if len(numeric_cols) < 2:
            st.warning("Need at least 2 numeric columns for scatter plot")
            return
            
        col1, col2, col3 = st.columns(3)
        
        with col1:
            x_col = st.selectbox("Select X-Axis:", numeric_cols)
        
        with col2:
            y_col = st.selectbox("Select Y-Axis:", [col for col in numeric_cols if col != x_col])
        
        with col3:
            if categorical_cols:
                color_col = st.selectbox("Color By (optional):", ["None"] + categorical_cols)
            else:
                color_col = "None"
        
        # Create scatter plot
        if color_col == "None":
            fig = px.scatter(
                df,
                x=x_col,
                y=y_col,
                title=f"Correlation between {x_col} and {y_col} in {table_name}",
                labels={x_col: x_col, y_col: y_col},
                template="plotly_white"
            )
        else:
            fig = px.scatter(
                df,
                x=x_col,
                y=y_col,
                color=color_col,
                title=f"Correlation between {x_col} and {y_col} by {color_col} in {table_name}",
                labels={x_col: x_col, y_col: y_col, color_col: color_col},
                template="plotly_white"
            )
        
        # Add trendline
        add_trendline = st.checkbox("Add Trendline")
        if add_trendline:
            fig.update_layout(
                shapes=[
                    dict(
                        type='line',
                        yref='paper', y0=0, y1=1,
                        xref='paper', x0=0, x1=1,
                        line=dict(color="red", width=2, dash="dash")
                    )
                ]
            )
            
            # Add correlation coefficient
            corr = df[[x_col, y_col]].corr().iloc[0, 1]
            fig.add_annotation(
                text=f"Correlation: {corr:.2f}",
                x=0.05,
                y=0.95,
                showarrow=False,
                font=dict(color="black", size=12),
                bgcolor="white",
                bordercolor="black",
                borderwidth=1
            )
        
        st.plotly_chart(fig, use_container_width=True)

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
    
    # Display editable table with enhanced deletion capability
    render_editable_table(df, table_name, column_info)
    
    # Add form to add new records with smart suggestions
    add_new_record_form(table_name, column_info)
    
    # Add data visualization
    create_data_visualization(df, table_name)

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

def create_table_card(table_name, stats):
    """Create a visual card for table selection using native Streamlit components"""
    # Get icon and color, or use defaults
    icon = stats.get('icon', '📊')
    color = stats.get('color', '#757575')
    row_count = stats.get('row_count', 0)
    col_count = stats.get('column_count', 0)
    has_pk = "✓" if stats.get('has_primary_key', False) else "✗"
    
    # Use standard HTML with styling for the card
    return f"""
    <div style="border: 2px solid {color}; border-radius: 10px; padding: 15px; 
                height: 100%; background-color: white; margin-bottom: 10px;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
            <div style="font-size: 18px; font-weight: bold; color: {color};">
                <span style="font-size: 24px; margin-right: 10px;">{icon}</span>{table_name}
            </div>
        </div>
        <div style="display: flex; justify-content: space-between; font-size: 14px; color: #555;">
            <div>{row_count:,} rows</div>
            <div>{col_count} columns</div>
            <div>PK: {has_pk}</div>
        </div>
    </div>
    """

def show_db_explorer():
    """Main function for database explorer"""
    # Apply styling - keeping most of the existing CSS for styling consistency
    st.markdown("""
    <style>
    /* Modern UI styling for database explorer */
    /* ... existing CSS styles ... */
    </style>
    """, unsafe_allow_html=True)
    
    st.title("Database Explorer")
    
    # Get list of tables
    tables = get_all_tables()
    
    if not tables:
        # Enhanced empty state
        st.markdown("""
            <div style="text-align:center; padding:50px 0;">
                <img src="https://cdn-icons-png.flaticon.com/512/1548/1548682.png" width="100">
                <h2>No tables found</h2>
                <p>The database exists but doesn't contain any tables yet.</p>
            </div>
        """, unsafe_allow_html=True)
        return
    
    # Main tabbed interface - simplified to just 2 tabs
    tab1, tab2 = st.tabs(["Browse Tables", "Delete Records"])
    
    # Maintain selected table in session state for consistency between tabs
    if 'selected_table' not in st.session_state:
        st.session_state.selected_table = None
    
    with tab1:
        # First tab: Table selection and visualization
        st.subheader("Select and Browse Tables")
        
        # Create a dropdown to select tables
        selected_table = st.selectbox(
            "Choose a table to view:",
            options=tables,
            index=tables.index(st.session_state.selected_table) if st.session_state.selected_table in tables else 0
        )
        
        # Update session state
        st.session_state.selected_table = selected_table
        
        # Get table structure and stats
        column_info = get_table_structure(selected_table)
        stats = get_table_stats(selected_table)
        
        # Show table info
        st.info(f"Table: {selected_table} - {stats.get('row_count', 0):,} rows, {stats.get('column_count', 0)} columns")
        
        # Different approach for student_profiles table vs other tables
        where_clause = ""
        order_by = ""
        
        if selected_table == "student_profiles":
            # Simple search functionality for student_profiles instead of Filter & Sort
            search_term = st.text_input(
                "🔍 Search students:", 
                placeholder="Enter name, ID, or any keyword...",
                help="Search across all columns"
            )
            
            if search_term:
                # Create search conditions for each text column
                search_conditions = []
                for col in column_info:
                    col_name = col['name']
                    col_type = col['type'].lower()
                    # Only include text-like columns in search
                    if any(text_type in col_type for text_type in ['char', 'text', 'varchar']):
                        search_conditions.append(f"{col_name} LIKE '%{search_term}%'")
                
                # Include numeric columns for exact matches if the search term is numeric
                if search_term.isdigit():
                    for col in column_info:
                        col_name = col['name']
                        col_type = col['type'].lower()
                        if any(num_type in col_type for num_type in ['int', 'integer', 'numeric']):
                            search_conditions.append(f"{col_name} = {search_term}")
                
                if search_conditions:
                    where_clause = " OR ".join(search_conditions)
        else:
            # Standard Filter & Sort for other tables
            with st.expander("Filter & Sort", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    # Column names for WHERE clause
                    column_names = [col['name'] for col in column_info]
                    filter_col = st.selectbox(
                        "Filter column:", 
                        ["None"] + column_names, 
                        key="filter_column"
                    )
                    
                    if filter_col != "None":
                        # Get unique values for the selected column
                        unique_vals = get_unique_values(selected_table, filter_col)
                        
                        # Show dropdown or text input based on number of unique values
                        if len(unique_vals) <= 30:
                            filter_val = st.selectbox("Value:", ["All"] + unique_vals)
                            where_clause = f"{filter_col} = '{filter_val}'" if filter_val != "All" else ""
                        else:
                            filter_val = st.text_input("Filter value:", placeholder="Enter value...")
                            filter_type = st.radio("Filter type:", ["Contains", "Equals", "Starts with"], horizontal=True)
                            
                            if filter_val:
                                if filter_type == "Contains":
                                    where_clause = f"{filter_col} LIKE '%{filter_val}%'"
                                elif filter_type == "Equals":
                                    where_clause = f"{filter_col} = '{filter_val}'"
                                else:  # Starts with
                                    where_clause = f"{filter_col} LIKE '{filter_val}%'"
                
                with col2:
                    # Order by options
                    order_col = st.selectbox("Order by:", ["None"] + column_names, key="order_column")
                    
                    if order_col != "None":
                        order_dir = st.radio("Direction:", ["ASC", "DESC"], horizontal=True)
                        order_by = f"{order_col} {order_dir}"
        
        # Add a limit control (common for both approaches)
        limit = st.slider("Maximum rows to display:", min_value=10, max_value=500, value=100, step=10)
        
        # Get and display data
        with st.spinner("Loading data..."):
            df, total_rows = get_filtered_table_data(selected_table, where_clause, order_by, limit=limit)
            
            # Show record count
            showing = min(len(df), limit)
            
            if selected_table == "student_profiles" and search_term:
                st.write(f"Found {showing} of {total_rows:,} records matching '{search_term}'")
            else:
                st.write(f"Showing {showing} of {total_rows:,} records {f'(filtered)' if where_clause else ''}")
            
            # Display the dataframe
            st.dataframe(df, use_container_width=True)
        
        # Add visualization option if data is available
        if not df.empty and len(df) > 1:
            with st.expander("Data Visualization", expanded=False):
                create_data_visualization(df, selected_table)
    
    with tab2:
        # Second tab: Delete records by column value
        st.subheader("Delete Records")
        
        # Show warning message
        st.warning("⚠️ Warning: Deletion cannot be undone. Please backup your database first.")
        
        # If the user has already selected a table in the first tab, use that table
        delete_table = st.selectbox(
            "Select table:", 
            tables,
            index=tables.index(st.session_state.selected_table) if st.session_state.selected_table in tables else 0,
            key="delete_table_select"
        )
        
        # Get table structure for the selected table
        delete_column_info = get_table_structure(delete_table)
        
        # Show current row count
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {delete_table}")
        row_count = cursor.fetchone()[0]
        conn.close()
        
        st.info(f"Table '{delete_table}' has {row_count:,} records")
        
        # Get column names for the selected table
        delete_columns = [col['name'] for col in delete_column_info]
        
        # Select column to filter by
        selected_column = st.selectbox("Select column to filter by:", delete_columns)
        
        # Get unique values for the selected column
        unique_values = get_unique_values(delete_table, selected_column, limit=100)
        
        if not unique_values:
            st.error(f"No values found in column '{selected_column}' or column is empty")
        else:
            # Select value to delete
            selected_value = st.selectbox(f"Select value from {selected_column}:", unique_values)
            
            # Preview data to be deleted
            st.subheader("Records to be deleted")
            preview_query = f"SELECT * FROM {delete_table} WHERE {selected_column} = ?"
            
            conn = get_db_connection()
            try:
                preview_df = pd.read_sql_query(preview_query, conn, params=(selected_value,))
                conn.close()
                
                if preview_df.empty:
                    st.info(f"No records found with {selected_column} = '{selected_value}'")
                else:
                    st.dataframe(preview_df, use_container_width=True)
                    st.warning(f"This will delete {len(preview_df)} record(s). This action cannot be undone.")
                    
                    # Add confirmation checkbox and delete button
                    confirm = st.checkbox(f"I confirm I want to delete records where {selected_column} = '{selected_value}'")
                    
                    if confirm:
                        if st.button("Delete Records", type="primary"):
                            if delete_record_by_column(delete_table, selected_column, selected_value):
                                st.success(f"Successfully deleted records where {selected_column} = '{selected_value}'")
                                st.rerun()
            except Exception as e:
                conn.close()
                st.error(f"Error previewing records: {e}")