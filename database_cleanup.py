import sqlite3
import os
import time
import pandas as pd
from datetime import datetime

# Constants
DATABASE_PATH = 'attendance_system.db'

# Dictionary of tables and columns to remove
# Format: 'table_name': ['column1', 'column2', ...]
COLUMNS_TO_REMOVE = {
    'student_profiles': ['old_section', 'unused_field', 'temp_data'],
    'attendance_records': ['old_timestamp', 'device_type', 'deprecated_field'],
    'class_attendance_records': ['old_time', 'backup_data', 'temp_field'],
    'user_accounts': ['temp_pass', 'old_token', 'reset_code'],
    'facial_recognition_data': ['old_format', 'backup_data', 'low_quality']
}

# Safety list of columns that should never be removed
PROTECTED_COLUMNS = {
    'student_profiles': ['name', 'section', 'student_id'],
    'attendance_records': ['name', 'timestamp', 'confidence'],
    'class_attendance_records': ['student_name', 'class_date', 'subject', 'attended'],
    'user_accounts': ['username', 'password', 'role'],
    'facial_recognition_data': ['name', 'embedding']
}

def create_backup():
    """Create a backup of the database before making changes"""
    if not os.path.exists(DATABASE_PATH):
        print(f"❌ Error: Database file '{DATABASE_PATH}' not found")
        return False
    
    backup_path = f"attendance_system_backup_{int(time.time())}.db"
    print(f"📦 Creating backup at {backup_path}")
    
    try:
        source_conn = sqlite3.connect(DATABASE_PATH)
        backup_conn = sqlite3.connect(backup_path)
        
        source_conn.backup(backup_conn)
        
        source_conn.close()
        backup_conn.close()
        
        print("✅ Backup created successfully")
        return True
    except Exception as e:
        print(f"❌ Error creating backup: {str(e)}")
        return False

def list_tables_and_columns():
    """List all tables and their columns in the database"""
    if not os.path.exists(DATABASE_PATH):
        print(f"❌ Error: Database file '{DATABASE_PATH}' not found")
        return
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row[0] for row in cursor.fetchall()]
    
    print("\n=== Database Structure ===")
    table_data = []
    
    for table in tables:
        # Get column information
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        
        # Count records
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        
        # Add to data for display
        table_data.append({
            'Table': table,
            'Columns': len(columns),
            'Records': count,
            'Column Names': ', '.join([col[1] for col in columns])
        })
    
    # Create and display a DataFrame
    df = pd.DataFrame(table_data)
    print(df.to_string(index=False))
    
    conn.close()

def remove_columns():
    """Remove specified columns from the database tables"""
    if not os.path.exists(DATABASE_PATH):
        print(f"❌ Error: Database file '{DATABASE_PATH}' not found")
        return
    
    # First create a backup
    if not create_backup():
        print("❌ Aborting operation: Could not create backup")
        return
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row[0] for row in cursor.fetchall()]
    
    # Prepare a report of what will be done
    operations = []
    for table in tables:
        # Get column information
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Determine which columns to remove
        if table in COLUMNS_TO_REMOVE:
            columns_to_remove = [col for col in COLUMNS_TO_REMOVE[table] if col in columns]
            if columns_to_remove:
                operations.append({
                    'Table': table,
                    'Columns to Remove': columns_to_remove,
                    'Remaining Columns': [col for col in columns if col not in columns_to_remove]
                })
    
    # Show what will be done
    if operations:
        print("\n=== Columns that will be removed ===")
        for op in operations:
            print(f"📋 Table: {op['Table']}")
            print(f"   Removing: {', '.join(op['Columns to Remove'])}")
            print(f"   Keeping: {', '.join(op['Remaining Columns'])}")
        
        # Ask for confirmation
        confirm = input("\n⚠️ Are you sure you want to remove these columns? This cannot be undone! (yes/no): ")
        if confirm.lower() != 'yes':
            print("❌ Operation cancelled by user")
            conn.close()
            return
    else:
        print("ℹ️ No columns found to remove")
        conn.close()
        return
    
    # Begin the removal process
    print("\n🔄 Removing columns...")
    cursor.execute("BEGIN TRANSACTION")
    
    try:
        for op in operations:
            table = op['Table']
            columns_to_keep = op['Remaining Columns']
            
            # Check if we're keeping protected columns
            if table in PROTECTED_COLUMNS:
                missing_protected = [col for col in PROTECTED_COLUMNS[table] if col not in columns_to_keep]
                if missing_protected:
                    print(f"❌ Error: Cannot remove protected columns from {table}: {', '.join(missing_protected)}")
                    raise Exception("Protected columns would be removed")
            
            # Create a new table without the unwanted columns
            columns_str = ', '.join(columns_to_keep)
            cursor.execute(f"""
            CREATE TABLE {table}_new (
                {', '.join([get_column_def(cursor, table, col) for col in columns_to_keep])}
            )
            """)
            
            # Copy data
            cursor.execute(f"""
            INSERT INTO {table}_new
            SELECT {columns_str} FROM {table}
            """)
            
            # Verify row count
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            old_count = cursor.fetchone()[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table}_new")
            new_count = cursor.fetchone()[0]
            
            if old_count != new_count:
                print(f"❌ Row count mismatch for table {table}: {old_count} vs {new_count}")
                raise Exception("Row count mismatch")
            
            # Drop the original table
            cursor.execute(f"DROP TABLE {table}")
            
            # Rename the new table
            cursor.execute(f"ALTER TABLE {table}_new RENAME TO {table}")
            
            print(f"✅ Successfully updated table {table}")
        
        # Commit all changes
        cursor.execute("COMMIT")
        print("\n✅ All specified columns have been successfully removed!")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("🔄 Rolling back changes...")
        cursor.execute("ROLLBACK")
        print("✅ Database restored to previous state")
    
    finally:
        conn.close()

def get_column_def(cursor, table, column):
    """Get the column definition including constraints"""
    cursor.execute(f"PRAGMA table_info({table})")
    columns = cursor.fetchall()
    
    for col in columns:
        if col[1] == column:
            # Extract all properties: cid, name, type, notnull, dflt_value, pk
            col_type = col[2]
            not_null = "NOT NULL" if col[3] else ""
            default = f"DEFAULT {col[4]}" if col[4] is not None else ""
            primary_key = "PRIMARY KEY" if col[5] else ""
            
            # Combine all properties
            definition = f"{column} {col_type} {not_null} {default} {primary_key}".strip()
            return definition
    
    return f"{column} TEXT"  # Default if not found

def interactive_mode():
    """Run in interactive mode to let the user select which columns to remove"""
    print("🔍 Database Column Cleanup Utility")
    print("This tool helps you safely remove unused columns from your database tables")
    
    if not os.path.exists(DATABASE_PATH):
        print(f"❌ Error: Database file '{DATABASE_PATH}' not found")
        return
    
    # Create a backup first
    if not create_backup():
        print("❌ Aborting operation: Could not create backup")
        return
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row[0] for row in cursor.fetchall()]
    
    selected_columns = {}
    
    # For each table, let user select columns to remove
    for table in tables:
        # Get column information
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        
        print(f"\n📋 Table: {table}")
        print(f"   Columns: {len(columns)}")
        
        # List columns
        print("\n   Available columns:")
        for i, col in enumerate(columns):
            col_name = col[1]
            col_type = col[2]
            protected = table in PROTECTED_COLUMNS and col_name in PROTECTED_COLUMNS[table]
            print(f"   {i+1}. {col_name} ({col_type}){' [PROTECTED]' if protected else ''}")
        
        # Ask which columns to remove
        print("\n   Enter the numbers of columns to remove (comma-separated, or 'skip' to skip this table):")
        user_input = input("   > ")
        
        if user_input.lower() == 'skip':
            continue
        
        try:
            # Parse user input
            if user_input.strip():
                selected_indices = [int(idx.strip()) - 1 for idx in user_input.split(',')]
                selected_cols = [columns[idx][1] for idx in selected_indices if 0 <= idx < len(columns)]
                
                # Check for protected columns
                if table in PROTECTED_COLUMNS:
                    protected_selected = [col for col in selected_cols if col in PROTECTED_COLUMNS[table]]
                    if protected_selected:
                        print(f"❌ Cannot remove protected columns: {', '.join(protected_selected)}")
                        continue
                
                if selected_cols:
                    selected_columns[table] = selected_cols
                    print(f"   Selected columns for removal: {', '.join(selected_cols)}")
                else:
                    print("   No valid columns selected")
            else:
                print("   No columns selected")
        except Exception as e:
            print(f"❌ Error parsing input: {str(e)}")
    
    conn.close()
    
    # If columns were selected, ask for confirmation and remove them
    if selected_columns:
        print("\n=== Summary of columns to remove ===")
        for table, cols in selected_columns.items():
            print(f"📋 Table: {table}")
            print(f"   Columns to remove: {', '.join(cols)}")
        
        confirm = input("\n⚠️ Are you sure you want to remove these columns? This cannot be undone! (yes/no): ")
        if confirm.lower() == 'yes':
            # Update global dict with user selections and run removal
            global COLUMNS_TO_REMOVE
            COLUMNS_TO_REMOVE = selected_columns
            remove_columns()
        else:
            print("❌ Operation cancelled by user")
    else:
        print("ℹ️ No columns selected for removal")

def main():
    print("🔧 Database Column Cleanup Utility 🔧")
    print("This tool helps you remove old or unused columns from your database tables")
    
    # Show menu
    print("\nPlease select an option:")
    print("1. List all tables and columns")
    print("2. Remove columns (using predefined list)")
    print("3. Interactive mode - select columns to remove")
    print("4. Exit")
    
    choice = input("\nEnter your choice (1-4): ")
    
    if choice == '1':
        list_tables_and_columns()
    elif choice == '2':
        remove_columns()
    elif choice == '3':
        interactive_mode()
    elif choice == '4':
        print("Exiting...")
    else:
        print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
