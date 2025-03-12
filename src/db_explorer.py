import sqlite3
import os
import pandas as pd
import numpy as np
from tabulate import tabulate
import re
from datetime import datetime
import json

# Constants
DATABASE_PATH = 'attendance_system.db'
MAX_DISPLAY_ROWS = 20  # Maximum rows to display at once

def get_db_connection():
    """Create a connection to the database"""
    return sqlite3.connect(DATABASE_PATH)

def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def pause():
    """Wait for user to press Enter"""
    input("\nPress Enter to continue...")

def backup_database():
    """Create a backup of the database before making changes"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"attendance_system_backup_{timestamp}.db"
    
    try:
        with sqlite3.connect(DATABASE_PATH) as src_conn:
            with sqlite3.connect(backup_file) as backup_conn:
                src_conn.backup(backup_conn)
        print(f"✅ Created database backup: {backup_file}")
        return True, backup_file
    except Exception as e:
        print(f"❌ Failed to create backup: {e}")
        return False, None

def list_tables():
    """List all tables in the database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get all tables (excluding SQLite system tables)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = cursor.fetchall()
        
        # Get table row counts
        table_info = []
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            
            # Get column count
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            table_info.append({
                'Table': table_name,
                'Rows': count,
                'Columns': len(columns)
            })
        
        # Convert to DataFrame for nice display
        df = pd.DataFrame(table_info)
        
        clear_screen()
        print("📋 Tables in Database")
        print("====================\n")
        print(tabulate(df, headers='keys', tablefmt='pretty', showindex=True))
        
        # Return list of table names
        return [t[0] for t in tables]
    
    except Exception as e:
        print(f"❌ Error listing tables: {e}")
        return []
        
    finally:
        conn.close()

def view_table_structure(table_name):
    """View the structure of a specific table"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get table info
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        if not columns:
            print(f"❌ Table '{table_name}' not found or has no columns")
            return
        
        # Convert to DataFrame
        columns_df = pd.DataFrame(columns, columns=[
            'cid', 'name', 'type', 'notnull', 'dflt_value', 'pk'
        ])
        
        # Get index information
        cursor.execute(f"PRAGMA index_list({table_name})")
        indices = cursor.fetchall()
        
        # Create a better formatted column list
        formatted_columns = []
        for _, row in columns_df.iterrows():
            constraints = []
            if row['pk'] == 1:
                constraints.append("PRIMARY KEY")
            if row['notnull'] == 1:
                constraints.append("NOT NULL")
            if row['dflt_value'] is not None:
                constraints.append(f"DEFAULT {row['dflt_value']}")
            
            formatted_columns.append({
                'ID': row['cid'],
                'Column': row['name'],
                'Type': row['type'],
                'Constraints': ' '.join(constraints)
            })
        
        clear_screen()
        print(f"📊 Table Structure: {table_name}")
        print("=" * (20 + len(table_name)) + "\n")
        
        # Display column information
        print("Columns:")
        print(tabulate(formatted_columns, headers='keys', tablefmt='pretty', showindex=False))
        
        # Display index information
        if indices:
            index_info = []
            for index in indices:
                idx_name = index[1]
                idx_unique = "UNIQUE" if index[2] == 1 else "NON-UNIQUE"
                
                # Get columns in this index
                cursor.execute(f"PRAGMA index_info({idx_name})")
                idx_columns = cursor.fetchall()
                idx_column_names = [columns_df['name'][col[2]] for col in idx_columns]
                
                index_info.append({
                    'Name': idx_name,
                    'Type': idx_unique,
                    'Columns': ', '.join(idx_column_names)
                })
                
            print("\nIndices:")
            print(tabulate(index_info, headers='keys', tablefmt='pretty', showindex=False))
        
    except Exception as e:
        print(f"❌ Error viewing table structure: {e}")
        
    finally:
        conn.close()

def view_table_data(table_name, page=0, where_clause="", order_by=""):
    """View data from a specific table with pagination"""
    conn = get_db_connection()
    
    try:
        # Calculate pagination
        offset = page * MAX_DISPLAY_ROWS
        limit = MAX_DISPLAY_ROWS
        
        # Build the query
        query = f"SELECT * FROM {table_name}"
        
        if where_clause:
            query += f" WHERE {where_clause}"
            
        if order_by:
            query += f" ORDER BY {order_by}"
        else:
            # Try to find a primary key for default ordering
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            pk_column = None
            for col in columns:
                if col[5] == 1:  # The 6th element (index 5) is the PK flag
                    pk_column = col[1]  # The 2nd element (index 1) is the column name
                    break
            
            if pk_column:
                query += f" ORDER BY {pk_column}"
        
        # Add pagination
        query += f" LIMIT {limit} OFFSET {offset}"
        
        # Execute query
        df = pd.read_sql_query(query, conn)
        
        # Get total row count for pagination info
        count_query = f"SELECT COUNT(*) as count FROM {table_name}"
        if where_clause:
            count_query += f" WHERE {where_clause}"
        total_rows = pd.read_sql_query(count_query, conn).iloc[0]['count']
        total_pages = (total_rows + MAX_DISPLAY_ROWS - 1) // MAX_DISPLAY_ROWS  # Ceiling division
        
        clear_screen()
        print(f"📋 Table Data: {table_name}")
        if where_clause:
            print(f"Filter: {where_clause}")
        if order_by:
            print(f"Ordered by: {order_by}")
        print(f"Page {page + 1} of {total_pages} (Total rows: {total_rows})")
        print("=" * 40 + "\n")
        
        if df.empty:
            print("No data found.")
        else:
            # Truncate large text fields for display
            for col in df.columns:
                if df[col].dtype == object:  # String columns
                    df[col] = df[col].apply(lambda x: str(x)[:50] + '...' if isinstance(x, str) and len(str(x)) > 50 else x)
            
            print(tabulate(df, headers='keys', tablefmt='pretty', showindex=False))
        
        return df, total_pages
        
    except Exception as e:
        print(f"❌ Error viewing table data: {e}")
        return pd.DataFrame(), 0
        
    finally:
        conn.close()

def execute_custom_query(query):
    """Execute a custom SQL query"""
    conn = get_db_connection()
    
    try:
        # Check if it's a SELECT query
        if query.strip().lower().startswith('select'):
            # It's a SELECT query, return results as DataFrame
            df = pd.read_sql_query(query, conn)
            clear_screen()
            print("🔍 Query Results")
            print("===============\n")
            print(f"Query: {query}\n")
            
            if df.empty:
                print("No results returned.")
            else:
                print(tabulate(df, headers='keys', tablefmt='pretty', showindex=False))
                
                # Export options
                export = input("\nExport results to CSV? (y/n): ").lower()
                if export == 'y':
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"query_results_{timestamp}.csv"
                    df.to_csv(filename, index=False)
                    print(f"✅ Results exported to {filename}")
            
            return True, df
        else:
            # It's a modification query
            cursor = conn.cursor()
            cursor.execute(query)
            conn.commit()
            row_count = cursor.rowcount
            clear_screen()
            print("✅ Query executed successfully")
            print(f"Rows affected: {row_count}")
            return True, row_count
    
    except Exception as e:
        print(f"❌ Error executing query: {e}")
        return False, None
        
    finally:
        conn.close()

def insert_record(table_name):
    """Insert a new record into a table"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get table structure
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        if not columns:
            print(f"❌ Table '{table_name}' not found")
            return False
        
        clear_screen()
        print(f"➕ Insert New Record into {table_name}")
        print("=" * (24 + len(table_name)) + "\n")
        
        # Get values for each column
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
                
            # Format prompts based on column characteristics
            prompt = f"{col_name} ({col_type})"
            if not_null:
                prompt += " [Required]"
            if default_val:
                prompt += f" [Default: {default_val}]"
            
            # Get user input
            value = input(f"{prompt}: ")
            
            # Use default value if available and no input provided
            if not value and default_val:
                value = default_val
                
            # Convert empty strings to None (NULL) if allowed
            if not value and not not_null:
                value = None
                
            # Special handling for booleans
            if col_type.lower() == 'boolean' and value is not None:
                value = value.lower() in ('1', 'true', 't', 'yes', 'y')
                
            column_values[col_name] = value
        
        # Build and execute INSERT query
        columns_str = ', '.join([k for k, v in column_values.items() if v is not None])
        placeholders = ', '.join(['?' for v in column_values.values() if v is not None])
        values = [v for v in column_values.values() if v is not None]
        
        query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
        
        # Confirm before inserting
        print("\nAbout to insert:")
        for col, val in column_values.items():
            if val is not None:
                print(f"  {col}: {val}")
        
        confirm = input("\nProceed with insert? (y/n): ").lower()
        if confirm != 'y':
            print("❌ Insert cancelled")
            return False
            
        cursor.execute(query, values)
        conn.commit()
        
        print(f"✅ Record inserted successfully (ID: {cursor.lastrowid})")
        return True
        
    except Exception as e:
        print(f"❌ Error inserting record: {e}")
        return False
        
    finally:
        conn.close()

def update_record(table_name):
    """Update an existing record in a table"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get table structure to find primary key
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        pk_column = None
        
        for col in columns:
            if col[5] == 1:  # Is primary key
                pk_column = col[1]
                break
        
        if not pk_column:
            print(f"❌ No primary key found for table '{table_name}'")
            input_method = input("Do you want to search by a specific column? (y/n): ").lower()
            if input_method != 'y':
                return False
            
            # Let user choose a column to search by
            print("\nAvailable columns:")
            for i, col in enumerate(columns):
                print(f"{i+1}. {col[1]} ({col[2]})")
            
            col_index = int(input("\nEnter column number to search by: ")) - 1
            if col_index < 0 or col_index >= len(columns):
                print("❌ Invalid selection")
                return False
            
            pk_column = columns[col_index][1]
        
        # Get search value
        search_value = input(f"Enter {pk_column} value to update: ")
        
        # Check if record exists
        cursor.execute(f"SELECT * FROM {table_name} WHERE {pk_column} = ?", (search_value,))
        record = cursor.fetchone()
        
        if not record:
            print(f"❌ No record found with {pk_column} = {search_value}")
            return False
            
        # Display current record
        column_names = [col[1] for col in columns]
        record_dict = dict(zip(column_names, record))
        
        clear_screen()
        print(f"✏️ Update Record in {table_name}")
        print("=" * (20 + len(table_name)) + "\n")
        print("Current values:")
        
        for col, val in record_dict.items():
            print(f"  {col}: {val}")
            
        print("\nEnter new values (leave blank to keep current value):")
        
        # Get updated values
        updates = {}
        for col in column_names:
            # Skip primary key
            if col == pk_column:
                continue
                
            new_value = input(f"{col} [Current: {record_dict[col]}]: ")
            if new_value:
                updates[col] = new_value
                
        if not updates:
            print("❌ No updates specified")
            return False
            
        # Build and execute UPDATE query
        set_clause = ', '.join([f"{col} = ?" for col in updates.keys()])
        values = list(updates.values())
        values.append(search_value)  # For WHERE clause
        
        query = f"UPDATE {table_name} SET {set_clause} WHERE {pk_column} = ?"
        
        # Confirm before updating
        print("\nAbout to update:")
        for col, val in updates.items():
            print(f"  {col}: {record_dict[col]} → {val}")
        
        confirm = input("\nProceed with update? (y/n): ").lower()
        if confirm != 'y':
            print("❌ Update cancelled")
            return False
            
        cursor.execute(query, values)
        conn.commit()
        
        print(f"✅ Record updated successfully (Rows affected: {cursor.rowcount})")
        return True
        
    except Exception as e:
        print(f"❌ Error updating record: {e}")
        return False
        
    finally:
        conn.close()

def delete_record(table_name):
    """Delete a record from a table"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get table structure to find primary key
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        pk_column = None
        
        for col in columns:
            if col[5] == 1:  # Is primary key
                pk_column = col[1]
                break
        
        clear_screen()
        print(f"🗑️ Delete Record from {table_name}")
        print("=" * (22 + len(table_name)) + "\n")
        
        # Determine delete method
        if pk_column:
            print(f"Primary key column: {pk_column}")
            delete_method = "pk"
        else:
            print("No primary key found. You'll need to specify a WHERE clause.")
            delete_method = "where"
        
        if delete_method == "pk":
            # Delete by primary key
            pk_value = input(f"Enter {pk_column} value to delete: ")
            where_clause = f"{pk_column} = '{pk_value}'"
        else:
            # Delete by custom WHERE clause
            print("\nEnter a WHERE clause to identify records to delete.")
            print("Example: name = 'John' AND age > 30")
            print("⚠️ WARNING: Without a WHERE clause, ALL records will be deleted!")
            where_clause = input("WHERE clause: ")
        
        # Verify what will be deleted
        query = f"SELECT * FROM {table_name} WHERE {where_clause}"
        try:
            df = pd.read_sql_query(query, conn)
            
            if df.empty:
                print("❌ No records match your criteria")
                return False
                
            print(f"\nThis will delete {len(df)} record(s):")
            print(tabulate(df, headers='keys', tablefmt='pretty', showindex=False))
            
        except Exception as e:
            print(f"❌ Error in WHERE clause: {e}")
            return False
        
        # Double-confirm for safety
        confirm = input("\n⚠️ Are you SURE you want to delete these records? (yes/no): ").lower()
        if confirm != 'yes':
            print("❌ Delete cancelled")
            return False
            
        # Execute DELETE
        delete_query = f"DELETE FROM {table_name} WHERE {where_clause}"
        cursor.execute(delete_query)
        conn.commit()
        
        print(f"✅ Deleted {cursor.rowcount} record(s)")
        return True
        
    except Exception as e:
        print(f"❌ Error deleting record: {e}")
        return False
        
    finally:
        conn.close()

def export_table_data(table_name):
    """Export table data to CSV or JSON"""
    conn = get_db_connection()
    
    try:
        # Get table data
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        
        if df.empty:
            print(f"❌ Table '{table_name}' is empty")
            return False
        
        # Ask for export format
        clear_screen()
        print(f"📤 Export Table Data: {table_name}")
        print("=" * (20 + len(table_name)) + "\n")
        
        print(f"Found {len(df)} records to export.")
        print("\nChoose export format:")
        print("1. CSV")
        print("2. JSON")
        print("3. Excel")
        print("4. Cancel")
        
        choice = input("\nEnter your choice (1-4): ")
        
        if choice == '1':
            # CSV export
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{table_name}_export_{timestamp}.csv"
            df.to_csv(filename, index=False)
            print(f"✅ Data exported to {filename}")
            return True
            
        elif choice == '2':
            # JSON export
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{table_name}_export_{timestamp}.json"
            
            # Handle NaN values which can't be serialized to JSON
            df_json = df.replace({np.nan: None}).to_dict(orient='records')
            
            with open(filename, 'w') as f:
                json.dump(df_json, f, indent=2)
                
            print(f"✅ Data exported to {filename}")
            return True
            
        elif choice == '3':
            # Excel export
            try:
                import openpyxl
            except ImportError:
                print("❌ openpyxl not installed. Please install it with:")
                print("pip install openpyxl")
                return False
                
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{table_name}_export_{timestamp}.xlsx"
            df.to_excel(filename, index=False)
            print(f"✅ Data exported to {filename}")
            return True
            
        else:
            print("Export cancelled")
            return False
        
    except Exception as e:
        print(f"❌ Error exporting data: {e}")
        return False
        
    finally:
        conn.close()

def import_data(table_name):
    """Import data into a table from CSV"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get table structure
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        clear_screen()
        print(f"📥 Import Data into {table_name}")
        print("=" * (20 + len(table_name)) + "\n")
        
        # Get file path
        file_path = input("Enter path to CSV file: ")
        
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return False
            
        # Read CSV
        df = pd.read_csv(file_path)
        
        print(f"\nRead {len(df)} rows from {file_path}")
        
        # Check for column mismatches
        missing_columns = [col for col in df.columns if col not in column_names]
        extra_columns = [col for col in column_names if col not in df.columns and col != 'id']
        
        if missing_columns:
            print(f"⚠️ Warning: CSV contains columns not in the table: {', '.join(missing_columns)}")
            
        if extra_columns:
            print(f"⚠️ Warning: Table has columns not in the CSV: {', '.join(extra_columns)}")
        
        # Filter to only include valid columns
        valid_columns = [col for col in df.columns if col in column_names]
        df_filtered = df[valid_columns]
        
        # Ask how to handle the import
        print("\nHow would you like to import the data?")
        print("1. Append (add to existing data)")
        print("2. Replace (clear table first)")
        print("3. Cancel")
        
        choice = input("\nEnter your choice (1-3): ")
        
        if choice == '3':
            print("Import cancelled")
            return False
            
        # Backup before changes
        backup_success, backup_file = backup_database()
        if not backup_success:
            confirm = input("Failed to backup database. Continue anyway? (y/n): ").lower()
            if confirm != 'y':
                print("Import cancelled")
                return False
                
        # Start transaction
        cursor.execute("BEGIN TRANSACTION")
        
        if choice == '2':
            # Replace - clear table first
            cursor.execute(f"DELETE FROM {table_name}")
            print(f"Cleared all data from {table_name}")
        
        # Import data
        cols_str = ', '.join(valid_columns)
        placeholders = ', '.join(['?' for _ in valid_columns])
        
        query = f"INSERT INTO {table_name} ({cols_str}) VALUES ({placeholders})"
        
        records = df_filtered.to_dict('records')
        
        for record in records:
            values = [record[col] for col in valid_columns]
            try:
                cursor.execute(query, values)
            except Exception as e:
                print(f"❌ Error inserting record: {e}")
                print(f"Record: {record}")
                
                handle_error = input("Continue with remaining records? (y/n): ").lower()
                if handle_error != 'y':
                    cursor.execute("ROLLBACK")
                    print("Import cancelled")
                    return False
        
        # Commit changes
        cursor.execute("COMMIT")
        
        print(f"✅ Successfully imported {len(records)} records")
        return True
        
    except Exception as e:
        print(f"❌ Error importing data: {e}")
        if 'cursor' in locals():
            cursor.execute("ROLLBACK")
        return False
        
    finally:
        conn.close()

def manage_table_menu(table_name):
    """Menu for managing a specific table"""
    while True:
        clear_screen()
        print(f"📋 Table Management: {table_name}")
        print("=" * (20 + len(table_name)) + "\n")
        
        print("1. View table structure")
        print("2. Browse table data")
        print("3. Insert record")
        print("4. Update record")
        print("5. Delete record")
        print("6. Export table data")
        print("7. Import data from CSV")
        print("8. Back to main menu")
        
        choice = input("\nEnter your choice (1-8): ")
        
        if choice == '1':
            view_table_structure(table_name)
            pause()
            
        elif choice == '2':
            page = 0
            total_pages = 1
            where_clause = ""
            order_by = ""
            
            while True:
                df, total_pages = view_table_data(table_name, page, where_clause, order_by)
                
                if total_pages > 0:
                    print(f"\nPage {page + 1} of {total_pages}")
                
                print("\nNavigation options:")
                print("n - Next page")
                print("p - Previous page")
                print("f - Filter data")
                print("s - Sort data")
                print("c - Clear filters")
                print("b - Back to table menu")
                
                nav = input("\nEnter option: ").lower()
                
                if nav == 'n' and page < total_pages - 1:
                    page += 1
                elif nav == 'p' and page > 0:
                    page -= 1
                elif nav == 'f':
                    where_clause = input("Enter WHERE clause (e.g., name LIKE '%Smith%'): ")
                    page = 0  # Reset to first page
                elif nav == 's':
                    order_by = input("Enter ORDER BY clause (e.g., last_name ASC, first_name ASC): ")
                elif nav == 'c':
                    where_clause = ""
                    order_by = ""
                    page = 0  # Reset to first page
                elif nav == 'b':
                    break
            
        elif choice == '3':
            insert_record(table_name)
            pause()
            
        elif choice == '4':
            update_record(table_name)
            pause()
            
        elif choice == '5':
            delete_record(table_name)
            pause()
            
        elif choice == '6':
            export_table_data(table_name)
            pause()
            
        elif choice == '7':
            import_data(table_name)
            pause()
            
        elif choice == '8':
            break

def sql_editor():
    """SQL editor for custom queries"""
    query_history = []
    
    while True:
        clear_screen()
        print("📝 SQL Query Editor")
        print("==================\n")
        
        if query_history:
            print("Recent queries:")
            for i, query in enumerate(query_history[-5:]):
                print(f"{i+1}. {query[:50]}{'...' if len(query) > 50 else ''}")
            print()
        
        print("Enter your SQL query (or type 'exit' to return to main menu):")
        
        # Collect multi-line query
        lines = []
        while True:
            line = input()
            if line.lower() == 'exit' and not lines:
                return
            if line.lower() == 'run' or line.lower() == 'go':
                break
            lines.append(line)
            
        query = ' '.join(lines)
        
        if query.strip():
            # Add to history
            query_history.append(query)
            
            # Execute query
            success, _ = execute_custom_query(query)
            
            if success:
                # Ask if user wants to save query
                save = input("\nSave query to file? (y/n): ").lower()
                if save == 'y':
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"query_{timestamp}.sql"
                    with open(filename, 'w') as f:
                        f.write(query)
                    print(f"✅ Query saved to {filename}")
                
            pause()

def show_db_explorer():
    """Main function"""
    while True:
        clear_screen()
        print("🔧 Advanced Database Explorer")
        print("==========================\n")
        
        print("1. List tables")
        print("2. Browse table")
        print("3. SQL editor")
        print("4. Create database backup")
        print("5. Database maintenance")
        print("6. Exit")
        
        choice = input("\nEnter your choice (1-6): ")
        
        if choice == '1':
            tables = list_tables()
            
            # Allow selecting a table to manage
            if tables:
                print("\nSelect a table to manage (or 0 to go back):")
                for i, table in enumerate(tables):
                    print(f"{i+1}. {table}")
                
                try:
                    table_choice = int(input("\nEnter table number: "))
                    if 1 <= table_choice <= len(tables):
                        manage_table_menu(tables[table_choice-1])
                except ValueError:
                    pass  # Invalid input, return to main menu
            
            pause()
            
        elif choice == '2':
            tables = list_tables()
            
            if not tables:
                print("No tables found in database.")
                pause()
                continue
                
            print("\nSelect a table to browse:")
            for i, table in enumerate(tables):
                print(f"{i+1}. {table}")
                
            try:
                table_choice = int(input("\nEnter table number: "))
                if 1 <= table_choice <= len(tables):
                    # Browse the selected table data
                    page = 0
                    total_pages = 1
                    while True:
                        df, total_pages = view_table_data(tables[table_choice-1], page)
                        
                        print("\nNavigation options:")
                        print("n - Next page")
                        print("p - Previous page")
                        print("f - Filter data")
                        print("b - Back to main menu")
                        
                        nav = input("\nEnter option: ").lower()
                        
                        if nav == 'n' and page < total_pages - 1:
                            page += 1
                        elif nav == 'p' and page > 0:
                            page -= 1
                        elif nav == 'f':
                            where_clause = input("Enter WHERE clause (e.g., name LIKE '%Smith%'): ")
                            df, total_pages = view_table_data(tables[table_choice-1], 0, where_clause)
                            page = 0  # Reset to first page
                        elif nav == 'b':
                            break
            except ValueError:
                pass  # Invalid input, return to main menu
                
        elif choice == '3':
            sql_editor()
            
        elif choice == '4':
            clear_screen()
            print("📦 Database Backup")
            print("================\n")
            
            success, backup_file = backup_database()
            if success:
                print(f"Backup created successfully: {backup_file}")
            else:
                print("Failed to create backup.")
            
            pause()
            
        elif choice == '5':
            clear_screen()
            print("🔧 Database Maintenance")
            print("====================\n")
            
            print("1. Vacuum database (optimize size)")
            print("2. Analyze tables (update statistics)")
            print("3. Check foreign key constraints")
            print("4. Back to main menu")
            
            maint_choice = input("\nEnter your choice (1-4): ")
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            try:
                if maint_choice == '1':
                    print("Vacuuming database...")
                    cursor.execute("VACUUM")
                    print("✅ Database vacuumed successfully")
                    
                elif maint_choice == '2':
                    print("Analyzing tables...")
                    cursor.execute("ANALYZE")
                    print("✅ Tables analyzed successfully")
                    
                elif maint_choice == '3':
                    print("Checking foreign key constraints...")
                    cursor.execute("PRAGMA foreign_key_check")
                    violations = cursor.fetchall()
                    
                    if violations:
                        print("❌ Foreign key violations found:")
                        for v in violations:
                            print(f"  Table: {v[0]}, RowId: {v[1]}, Parent: {v[2]}, Foreign Key: {v[3]}")
                    else:
                        print("✅ No foreign key violations found")
            except Exception as e:
                print(f"❌ Error during maintenance: {e}")
            finally:
                conn.close()
                pause()
                
        elif choice == '6':
            clear_screen()
            print("Thanks for using Database Explorer. Goodbye!")
            break
            
        else:
            print("Invalid choice. Please try again.")
            pause()

def batch_operations():
    """Menu for batch operations"""
    clear_screen()
    print("🔄 Batch Operations")
    print("================\n")
    
    print("1. Execute SQL script file")
    print("2. Export all tables")
    print("3. Back to main menu")
    
    choice = input("\nEnter your choice (1-3): ")
    
    if choice == '1':
        script_path = input("Enter path to SQL script file: ")
        
        if not os.path.exists(script_path):
            print(f"❌ File not found: {script_path}")
            pause()
            return
            
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            with open(script_path, 'r') as f:
                script = f.read()
                
            # Execute script
            cursor.executescript(script)
            conn.commit()
            
            print("✅ SQL script executed successfully")
            
        except Exception as e:
            print(f"❌ Error executing SQL script: {e}")
        finally:
            conn.close()
            
    elif choice == '2':
        export_dir = f"db_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(export_dir, exist_ok=True)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            tables = [row[0] for row in cursor.fetchall()]
            
            for table in tables:
                try:
                    df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
                    export_path = os.path.join(export_dir, f"{table}.csv")
                    df.to_csv(export_path, index=False)
                    print(f"✅ Exported {table} to {export_path}")
                except Exception as e:
                    print(f"❌ Error exporting {table}: {e}")
            
            print(f"\nAll tables exported to directory: {export_dir}")
            
        except Exception as e:
            print(f"❌ Error during batch export: {e}")
        finally:
            conn.close()
    
    pause()

if __name__ == "__main__":
    show_db_explorer()
