import sqlite3
import os
from datetime import datetime
import pandas as pd
from tabulate import tabulate

# Constants
DATABASE_PATH = 'attendance_system.db'

# Tables to keep (everything else will be considered for removal)
TABLES_TO_KEEP = [
    'attendance_records', 
    'class_attendance_records',
    'class_schedules', 
    'facial_recognition_data',
    'student_profiles',
    'system_metadata',
    'user_accounts',
    'attendance_summary'
]

# Views to keep
VIEWS_TO_KEEP = [
    'control_4'  # This is a view for backward compatibility
]

def get_db_connection():
    """Create a connection to the database"""
    return sqlite3.connect(DATABASE_PATH)

def backup_database():
    """Create a backup of the database"""
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

def list_all_tables():
    """List all tables and views in the database"""
    if not os.path.exists(DATABASE_PATH):
        print(f"❌ Error: Database file '{DATABASE_PATH}' not found.")
        return None, None
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row[0] for row in cursor.fetchall()]
    
    # Get all views
    cursor.execute("SELECT name FROM sqlite_master WHERE type='view'")
    views = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    
    return tables, views

def identify_old_tables(all_tables, all_views):
    """Identify tables that should be removed"""
    tables_to_remove = []
    views_to_remove = []
    
    # Find tables to remove
    for table in all_tables:
        # Check if this table is an old version of a renamed table
        if table in ['students', 'users', 'presidents_embeds', 'attendance_log', 'control_4']:
            tables_to_remove.append(table)
        # Check if it's not in the keep list
        elif table not in TABLES_TO_KEEP:
            tables_to_remove.append(table)
    
    # Find views to remove
    for view in all_views:
        if view not in VIEWS_TO_KEEP:
            views_to_remove.append(view)
    
    return tables_to_remove, views_to_remove

def remove_tables(tables_to_remove, views_to_remove):
    """Remove the specified tables and views"""
    if not tables_to_remove and not views_to_remove:
        print("No tables or views to remove.")
        return True
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("BEGIN TRANSACTION")
        
        # Remove views first (they might depend on tables)
        for view in views_to_remove:
            print(f"🗑️ Dropping view: {view}")
            cursor.execute(f"DROP VIEW IF EXISTS {view}")
        
        # Now remove tables
        for table in tables_to_remove:
            print(f"🗑️ Dropping table: {table}")
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
        
        cursor.execute("COMMIT")
        print("✅ Successfully removed old tables and views")
        return True
    
    except Exception as e:
        print(f"❌ Error removing tables: {e}")
        cursor.execute("ROLLBACK")
        return False
    
    finally:
        conn.close()

def verify_remaining_tables():
    """Verify that only the intended tables remain"""
    remaining_tables, remaining_views = list_all_tables()
    
    print("\n=== Remaining Database Objects ===")
    print("Tables:")
    for table in remaining_tables:
        print(f"- {table}")
    
    print("\nViews:")
    for view in remaining_views:
        print(f"- {view}")
    
    # Check if any tables are missing
    missing_tables = [table for table in TABLES_TO_KEEP if table not in remaining_tables]
    if missing_tables:
        print("⚠️ Warning! Some important tables are missing:")
        for table in missing_tables:
            print(f"- {table}")
    
    return len(missing_tables) == 0

def main():
    """Main function"""
    print("🔧 Database Cleanup - Remove Old Tables")
    print("This tool will remove old/unused tables while keeping essential ones")
    
    # List all tables
    all_tables, all_views = list_all_tables()
    if all_tables is None:
        return
    
    print("\n=== Current Database Objects ===")
    print(f"Found {len(all_tables)} tables and {len(all_views)} views")
    
    # Identify tables to remove
    tables_to_remove, views_to_remove = identify_old_tables(all_tables, all_views)
    
    if not tables_to_remove and not views_to_remove:
        print("✅ No old tables or views found. Your database is already clean!")
        return
    
    print("\n=== Objects to Remove ===")
    if tables_to_remove:
        print("Tables:")
        for table in tables_to_remove:
            print(f"- {table}")
    
    if views_to_remove:
        print("\nViews:")
        for view in views_to_remove:
            print(f"- {view}")
    
    # Ask for confirmation
    confirm = input("\n⚠️ Are you sure you want to remove these objects? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Operation cancelled.")
        return
    
    # Create backup
    backup_success, backup_file = backup_database()
    if not backup_success:
        retry = input("Continue without backup? (yes/no): ")
        if retry.lower() != 'yes':
            print("Operation cancelled.")
            return
    
    # Remove tables and views
    if remove_tables(tables_to_remove, views_to_remove):
        # Verify remaining tables
        verify_remaining_tables()

if __name__ == "__main__":
    main()
