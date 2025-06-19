import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime
import subprocess

# Constants
DATABASE_PATH = 'attendance_system.db'

def get_db_connection():
    """Create a connection to the database"""
    return sqlite3.connect(DATABASE_PATH)

def load_table_data(table_name, limit=1000):
    """Load data from a table with pagination"""
    conn = get_db_connection()
    query = f"SELECT * FROM {table_name} LIMIT {limit}"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_tables():
    """Get list of all tables in the database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    return tables

def create_backup():
    """Create a backup of the database"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"attendance_system_backup_{timestamp}.db"
    
    try:
        with sqlite3.connect(DATABASE_PATH) as src_conn:
            with sqlite3.connect(backup_file) as backup_conn:
                src_conn.backup(backup_conn)
        
        return True, backup_file
    except Exception as e:
        st.error(f"Failed to create backup: {e}")
        return False, None

def db_operations():
    """Streamlit interface for database operations"""
    st.title("Database Operations")
    
    # Sidebar menu
    operation = st.sidebar.selectbox(
        "Select Operation",
        ["Browse Tables", "Execute SQL", "Insert Record", "Export Data", "Database Info"]
    )
    
    if operation == "Browse Tables":
        tables = get_tables()
        
        if not tables:
            st.warning("No tables found in the database.")
            return
        
        table_name = st.selectbox("Select Table", tables)
        
        # Show table data
        st.subheader(f"Data from {table_name}")
        
        # Pagination
        row_limit = st.slider("Maximum rows to show", min_value=10, max_value=5000, value=1000, step=10)
        
        # Filter option
        use_filter = st.checkbox("Filter data")
        where_clause = ""
        
        if use_filter:
            where_clause = st.text_input("Enter WHERE clause (e.g., name LIKE '%Smith%')")
        
        # Execute query
        conn = get_db_connection()
        query = f"SELECT * FROM {table_name}"
        
        if where_clause:
            query += f" WHERE {where_clause}"
            
        query += f" LIMIT {row_limit}"
        
        try:
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            # Display data
            st.dataframe(df)
            
            # Show row count
            st.info(f"Showing {len(df)} rows from {table_name}")
            
            # Export option
            if st.button("Export to CSV"):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{table_name}_export_{timestamp}.csv"
                df.to_csv(filename, index=False)
                st.success(f"Data exported to {filename}")
                
        except Exception as e:
            st.error(f"Error executing query: {e}")
            conn.close()
    
    elif operation == "Execute SQL":
        st.subheader("SQL Query Editor")
        
        query = st.text_area("Enter SQL query", height=200)
        
        if st.button("Execute"):
            if not query:
                st.warning("Please enter a query to execute.")
                return
                
            conn = get_db_connection()
            
            try:
                # Check if it's a SELECT query
                if query.strip().lower().startswith('select'):
                    df = pd.read_sql_query(query, conn)
                    conn.close()
                    
                    # Display results
                    st.subheader("Query Results")
                    st.dataframe(df)
                    
                    # Show row count
                    st.info(f"Query returned {len(df)} rows")
                    
                    # Export option
                    if st.button("Export Results"):
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"query_results_{timestamp}.csv"
                        df.to_csv(filename, index=False)
                        st.success(f"Results exported to {filename}")
                        
                else:
                    # For non-SELECT queries
                    cursor = conn.cursor()
                    cursor.execute(query)
                    conn.commit()
                    conn.close()
                    
                    st.success(f"Query executed successfully. Rows affected: {cursor.rowcount}")
                    
            except Exception as e:
                st.error(f"Error executing query: {e}")
                conn.close()
    
    elif operation == "Insert Record":
        tables = get_tables()
        
        if not tables:
            st.warning("No tables found in the database.")
            return
        
        table_name = st.selectbox("Select Table", tables)
        
        # Get table structure
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        conn.close()
        
        if not columns:
            st.warning(f"No columns found in table {table_name}")
            return
            
        # Show form to input values
        st.subheader(f"Insert Record into {table_name}")
        
        with st.form(key=f"insert_form_{table_name}"):
            # Dictionary to store column values
            column_values = {}
            
            for col in columns:
                col_name = col[1]
                col_type = col[2]
                not_null = col[3]
                default_val = col[4]
                is_pk = col[5]
                
                # Skip autoincrement primary key columns
                if is_pk and col_type.lower() == 'integer':
                    continue
                
                # Format label based on column characteristics
                label = f"{col_name} ({col_type})"
                if not_null:
                    label += " *"
                
                # Different input widgets based on type
                if "int" in col_type.lower():
                    column_values[col_name] = st.number_input(label, step=1)
                elif "real" in col_type.lower() or "float" in col_type.lower():
                    column_values[col_name] = st.number_input(label)
                elif "bool" in col_type.lower():
                    column_values[col_name] = st.checkbox(label)
                elif "date" in col_type.lower():
                    column_values[col_name] = st.date_input(label)
                else:
                    column_values[col_name] = st.text_input(label)
            
            submit = st.form_submit_button("Insert Record")
            
            if submit:
                # Build and execute INSERT query
                columns_str = ', '.join(column_values.keys())
                placeholders = ', '.join(['?' for _ in column_values.keys()])
                values = list(column_values.values())
                
                query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
                
                conn = get_db_connection()
                cursor = conn.cursor()
                
                try:
                    cursor.execute(query, values)
                    conn.commit()
                    
                    st.success(f"Record inserted successfully (ID: {cursor.lastrowid})")
                except Exception as e:
                    st.error(f"Error inserting record: {e}")
                finally:
                    conn.close()
    
    elif operation == "Export Data":
        st.subheader("Export Database Data")
        
        export_type = st.radio("Export Type", ["Single Table", "All Tables", "Database Backup"])
        
        if export_type == "Single Table":
            tables = get_tables()
            table_name = st.selectbox("Select Table", tables)
            
            export_format = st.selectbox("Export Format", ["CSV", "JSON", "Excel"])
            
            if st.button("Export"):
                conn = get_db_connection()
                try:
                    df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
                    conn.close()
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    
                    if export_format == "CSV":
                        filename = f"{table_name}_export_{timestamp}.csv"
                        df.to_csv(filename, index=False)
                    elif export_format == "JSON":
                        filename = f"{table_name}_export_{timestamp}.json"
                        df.to_json(filename, orient="records")
                    else:  # Excel
                        filename = f"{table_name}_export_{timestamp}.xlsx"
                        df.to_excel(filename, index=False)
                    
                    st.success(f"Data exported to {filename}")
                    
                except Exception as e:
                    st.error(f"Error exporting data: {e}")
                    conn.close()
                    
        elif export_type == "All Tables":
            if st.button("Export All Tables"):
                export_dir = f"db_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                os.makedirs(export_dir, exist_ok=True)
                
                conn = get_db_connection()
                
                try:
                    # Get all tables
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
                    tables = [row[0] for row in cursor.fetchall()]
                    
                    for table in tables:
                        try:
                            df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
                            export_path = os.path.join(export_dir, f"{table}.csv")
                            df.to_csv(export_path, index=False)
                        except Exception as e:
                            st.error(f"Error exporting {table}: {e}")
                    
                    conn.close()
                    st.success(f"All tables exported to directory: {export_dir}")
                    
                except Exception as e:
                    st.error(f"Error during batch export: {e}")
                    conn.close()
                    
        elif export_type == "Database Backup":
            if st.button("Create Database Backup"):
                success, backup_file = create_backup()
                if success:
                    st.success(f"Backup created successfully: {backup_file}")
    
    elif operation == "Database Info":
        st.subheader("Database Information")
        
        # Connect to database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Get database size
            db_size = os.path.getsize(DATABASE_PATH) / (1024 * 1024)  # Convert to MB
            st.write(f"**Database Size:** {db_size:.2f} MB")
            
            # Get number of tables
            cursor.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            table_count = cursor.fetchone()[0]
            st.write(f"**Number of Tables:** {table_count}")
            
            # Table information
            st.subheader("Tables")
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            tables = [row[0] for row in cursor.fetchall()]
            
            table_info = []
            for table in tables:
                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                row_count = cursor.fetchone()[0]
                
                # Get column count
                cursor.execute(f"PRAGMA table_info({table})")
                columns = cursor.fetchall()
                
                # Get size estimate (very approximate)
                cursor.execute(f"SELECT COUNT(*), SUM(LENGTH(CAST(rowid AS text))) FROM {table}")
                count, id_size = cursor.fetchone()
                size_kb = (id_size or 0) / 1024  # KB
                
                table_info.append({
                    "Table": table,
                    "Rows": row_count,
                    "Columns": len(columns),
                    "Est. Size (KB)": round(size_kb, 2)
                })
            
            st.dataframe(pd.DataFrame(table_info))
            
        except Exception as e:
            st.error(f"Error getting database info: {e}")
        
        finally:
            conn.close()
            
def launch_terminal_explorer():
    """Launch the terminal-based database explorer"""
    explorer_path = os.path.join(os.path.dirname(__file__), 'advanced_db_explorer.py')
    
    if not os.path.exists(explorer_path):
        st.error(f"Database explorer script not found: {explorer_path}")
        return
    
    try:
        subprocess.Popen(['python', explorer_path], 
                         stdout=subprocess.PIPE, 
                         stderr=subprocess.PIPE)
        st.success("Terminal database explorer launched. Check your terminal window.")
    except Exception as e:
        st.error(f"Failed to launch terminal explorer: {e}")

def show_db_operations():
    """Main function to show in Streamlit"""
    st.sidebar.title("Database Tools")
    
    option = st.sidebar.radio(
        "Choose Interface",
        ["Web Interface", "Terminal Explorer"]
    )
    
    if option == "Web Interface":
        db_operations()
    else:
        st.title("Terminal Database Explorer")
        st.write("This will launch the advanced database explorer in a terminal window.")
        st.write("Note: This requires access to the terminal and is best run directly on the server.")
        
        if st.button("Launch Terminal Explorer"):
            launch_terminal_explorer()

if __name__ == "__main__":
    show_db_operations()
