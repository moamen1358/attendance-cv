import streamlit as st
import sqlite3
import pandas as pd
from time_format_utils import convert_to_ampm_format

DATABASE_PATH = 'attendance_system.db'

def get_table_columns(table_name):
    """
    Get the columns of a specified table.
    
    Args:
        table_name (str): The name of the table.
        
    Returns:
        list: List of tuples containing column information.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(f"PRAGMA table_info({table_name})")
        return cursor.fetchall()
    except Exception as e:
        st.error(f"Error fetching columns for table {table_name}: {str(e)}")
        return []
    finally:
        conn.close()

def insert_row_into_table(table_name, column_values):
    """
    Insert a new row into the specified database table with proper time formatting.
    
    Args:
        table_name (str): The name of the table to insert into.
        column_values (dict): Dictionary of column names and values.
        
    Returns:
        tuple: (success, message)
    """
    formatted_values = {}
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns_info = cursor.fetchall()
        for col_name, value in column_values.items():
            is_time_field = any(keyword in col_name.lower() for keyword in ['time', 'hour', 'start_', 'end_'])
            if is_time_field and isinstance(value, str):
                try:
                    formatted_values[col_name] = convert_to_ampm_format(value)
                except:
                    formatted_values[col_name] = value
            else:
                formatted_values[col_name] = value
        columns = ", ".join(formatted_values.keys())
        placeholders = ", ".join(["?"] * len(formatted_values))
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        cursor.execute(query, list(formatted_values.values()))
        conn.commit()
        return True, f"Row inserted successfully into {table_name}"
    except Exception as e:
        conn.rollback()
        return False, f"Error inserting row: {str(e)}"
    finally:
        conn.close()

def update_row_in_table(table_name, id_column, id_value, column_values):
    """
    Update a row in the specified database table, ensuring time values use 12-hour format.
    
    Args:
        table_name (str): The name of the table to update.
        id_column (str): The primary key column name.
        id_value: The value of the primary key for the row to update.
        column_values (dict): Dictionary of column names and values.
        
    Returns:
        tuple: (success, message)
    """
    formatted_values = {}
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    try:
        for col_name, value in column_values.items():
            is_time_field = any(keyword in col_name.lower() for keyword in ['time', 'hour', 'start_', 'end_'])
            if is_time_field and isinstance(value, str):
                try:
                    formatted_values[col_name] = convert_to_ampm_format(value)
                except:
                    formatted_values[col_name] = value
            else:
                formatted_values[col_name] = value
        
        set_clause = ", ".join([f"{col} = ?" for col in formatted_values.keys()])
        query = f"UPDATE {table_name} SET {set_clause} WHERE {id_column} = ?"
        params = list(formatted_values.values()) + [id_value]
        cursor.execute(query, params)
        conn.commit()
        return True, f"Row updated successfully in {table_name}"
    except Exception as e:
        conn.rollback()
        return False, f"Error updating row: {str(e)}"
    finally:
        conn.close()

def format_table_data(rows, columns):
    """
    Format table data to ensure time values are displayed in 12-hour format
    
    Args:
        rows (list): List of row tuples from the database
        columns (list): Column names
        
    Returns:
        pandas.DataFrame: Formatted dataframe
    """
    df = pd.DataFrame(rows, columns=columns)
    for col in df.columns:
        if any(keyword in col.lower() for keyword in ['time', 'start_', 'end_']):
            df[col] = df[col].apply(
                lambda x: convert_to_ampm_format(str(x)) if isinstance(x, str) and ':' in str(x) else x
            )
    return df

def show_database_explorer():
    """
    Display the Database Explorer page.
    """
    st.title("Database Explorer")
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
    except Exception as e:
        st.error(f"Error fetching tables: {str(e)}")
        return
    finally:
        conn.close()
    
    selected_table = st.selectbox("Select a table to explore:", tables)
    if selected_table:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute(f"SELECT * FROM {selected_table}")
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            df = format_table_data(rows, columns)
            st.write(f"Table: {selected_table}")
            st.dataframe(df)
        except Exception as e:
            st.error(f"Error fetching data from table {selected_table}: {str(e)}")
        finally:
            conn.close()
    
    if st.button("Insert Row"):
        st.session_state.action = 'insert'
    
    if st.session_state.get('action') == 'insert':
        st.subheader(f"Insert New Row into {selected_table}")
        
        with st.form(key=f"insert_form_{selected_table}"):
            columns = get_table_columns(selected_table)
            form_values = {}
            
            # Special handling for class_schedules table
            is_class_schedule_table = selected_table.lower() == 'class_schedules'
            
            if is_class_schedule_table:
                st.markdown("""
                <div style="background-color: #e3f2fd; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                    <h3 style="margin-top: 0; color: #1565c0;">Adding Class Schedule</h3>
                    <p style="margin-bottom: 0;">All time values will be stored in 12-hour format with AM/PM.</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Setup special fields for class_schedules with clear labeling
                st.markdown("### Class Details")
                
                # Day selection
                day_options = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                form_values["day"] = st.selectbox("Day of Week*", day_options)
                
                # Subject selection - try to get from subjects table if possible
                try:
                    conn = sqlite3.connect(DATABASE_PATH)
                    cursor = conn.cursor()
                    cursor.execute("SELECT subject_name FROM subjects ORDER BY subject_name")
                    subjects = [row[0] for row in cursor.fetchall()]
                    if subjects:
                        form_values["subject"] = st.selectbox("Subject*", subjects)
                    else:
                        form_values["subject"] = st.text_input("Subject*", help="Enter the subject name")
                except:
                    form_values["subject"] = st.text_input("Subject*", help="Enter the subject name")
                finally:
                    try:
                        conn.close()
                    except:
                        pass
                
                # Type of class
                form_values["type"] = st.selectbox("Class Type*", ["lec", "sec", "lab"], 
                                                   format_func=lambda x: {"lec": "Lecture", "sec": "Section", "lab": "Laboratory"}[x])
                
                # Room entry
                form_values["room"] = st.text_input("Room/Location*", help="Enter the room number or location")
                
                # Time selection with AM/PM - Make this section stand out
                st.markdown("""
                <div style="background-color: #f5f5f5; padding: 15px; border-radius: 8px; margin-top: 20px;">
                    <h3 style="margin-top: 0; color: #2e7d32;">Time Schedule (12-hour format)</h3>
                </div>
                """, unsafe_allow_html=True)
                
                # Start time with clear AM/PM selection
                st.markdown("#### Start Time")
                start_cols = st.columns([2, 1, 1])
                with start_cols[0]:
                    start_hour = st.number_input("Hour", min_value=1, max_value=12, value=8, step=1, key="start_hour")
                    start_minute = st.number_input("Minute", min_value=0, max_value=59, value=0, step=5, format="%02d", key="start_minute")
                with start_cols[1]:
                    start_ampm = st.radio("AM/PM", ["AM", "PM"], horizontal=True, key="start_ampm")
                
                # Format the start time
                start_time = f"{start_hour}:{start_minute:02d} {start_ampm}"
                st.caption(f"Start time will be saved as: **{start_time}**")
                form_values["start_time"] = start_time
                
                # End time with clear AM/PM selection
                st.markdown("#### End Time")
                end_cols = st.columns([2, 1, 1])
                with end_cols[0]:
                    end_hour = st.number_input("Hour", min_value=1, max_value=12, value=9, step=1, key="end_hour")
                    end_minute = st.number_input("Minute", min_value=0, max_value=59, value=30, step=5, format="%02d", key="end_minute")
                with end_cols[1]:
                    end_ampm = st.radio("AM/PM", ["AM", "PM"], horizontal=True, key="end_ampm")
                
                # Format the end time
                end_time = f"{end_hour}:{end_minute:02d} {end_ampm}"
                st.caption(f"End time will be saved as: **{end_time}**")
                form_values["end_time"] = end_time
                
                # Try to get a subject_id (if exists in table schema)
                try:
                    conn = sqlite3.connect(DATABASE_PATH)
                    cursor = conn.cursor()
                    cursor.execute("SELECT subject_id FROM subjects WHERE subject_name = ?", (form_values["subject"],))
                    subject_id = cursor.fetchone()
                    if subject_id:
                        form_values["subject_id"] = subject_id[0]
                except:
                    pass  # Skip if we can't get the subject_id
                finally:
                    try:
                        conn.close()
                    except:
                        pass
                
                # Preview the data to be inserted
                with st.expander("Preview Data to be Inserted", expanded=False):
                    st.json(form_values)
            else:
                # Regular form handling for other tables
                for col in columns:
                    col_name = col[1]
                    col_type = col[2].upper()
                    is_time_field = any(keyword in col_name.lower() for keyword in ['time', 'hour', 'start_', 'end_'])
                    
                    if col_name == 'id' and 'NOT NULL' in col_type and 'PRIMARY KEY' in col_type:
                        st.text_input(f"{col_name} (auto)", value="Auto-generated", disabled=True)
                    elif 'DATETIME' in col_type or 'DATE' in col_type:
                        form_values[col_name] = st.date_input(col_name)
                    elif is_time_field:
                        hour = st.number_input(
                            f"{col_name} Hour", 
                            min_value=1, 
                            max_value=12, 
                            value=8, 
                            step=1, 
                            key=f"hour_{col_name}"
                        )
                        minute = st.number_input(
                            f"{col_name} Minute", 
                            min_value=0, 
                            max_value=59, 
                            value=0, 
                            step=1, 
                            format="%02d", 
                            key=f"minute_{col_name}"
                        )
                        am_pm = st.selectbox(
                            f"{col_name} AM/PM", 
                            options=["AM", "PM"], 
                            index=0, 
                            key=f"ampm_{col_name}"
                        )
                        form_values[col_name] = f"{hour}:{minute:02d} {am_pm}"
                    elif 'INT' in col_type:
                        form_values[col_name] = st.number_input(col_name, step=1, format="%d")
                    elif 'REAL' in col_type or 'FLOAT' in col_type or 'DOUBLE' in col_type:
                        form_values[col_name] = st.number_input(col_name, step=0.1)
                    elif 'BOOL' in col_type:
                        form_values[col_name] = st.checkbox(col_name)
                    else:
                        form_values[col_name] = st.text_input(col_name)
            
            # Submit button
            submit_button = st.form_submit_button("Insert Row", use_container_width=True)
            if submit_button:
                success, message = insert_row_into_table(selected_table, form_values)
                
                if success:
                    st.success(message)
                    st.session_state.action = None
                    st.rerun()
                else:
                    st.error(message)

if __name__ == "__main__":
    show_database_explorer()