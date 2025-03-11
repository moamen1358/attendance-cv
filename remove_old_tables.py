import sqlite3
import os
import time
import pandas as pd
from datetime import datetime

# Constants
DATABASE_PATH = 'attendance_system.db'

# Old to new table name mappings
TABLE_MAPPINGS = {
    'students': 'student_profiles',
    'users': 'user_accounts',
    'presidents_embeds': 'facial_recognition_data',
    'attendance_log': 'attendance_records',
    'control_4': 'class_schedules',
    'class_attendance': 'class_attendance_records'
}

def create_backup():
    """Create a backup of the database before making any changes"""
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
        return True, backup_path
    except Exception as e:
        print(f"❌ Error creating backup: {str(e)}")
        return False, None

def list_tables():
    """List all tables in the database"""
    if not os.path.exists(DATABASE_PATH):
        print(f"❌ Error: Database file '{DATABASE_PATH}' not found")
        return
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row[0] for row in cursor.fetchall()]
    
    print("\n=== Database Tables ===")
    table_data = []
    
    for table in tables:
        # Count records
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        
        # Check if this is an old or new table
        status = "Current"
        for old_name, new_name in TABLE_MAPPINGS.items():
            if table == old_name and new_name in tables:
                status = f"Old (→ {new_name})"
                break
            elif table == new_name:
                status = "New"
                break
        
        # Add to data for display
        table_data.append({
            'Table': table,
            'Status': status,
            'Records': count
        })
    
    # Create and display a DataFrame
    df = pd.DataFrame(table_data)
    df = df.sort_values('Status')
    print(df.to_string(index=False))
    
    conn.close()
    
    # Return list of old tables
    old_tables = [t['Table'] for t in table_data if t['Status'].startswith('Old')]
    return old_tables

def verify_data_migration(old_table, new_table):
    """Verify that all data has been properly migrated"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Get tables
    cursor.execute(f"SELECT COUNT(*) FROM {old_table}")
    old_count = cursor.fetchone()[0]
    
    cursor.execute(f"SELECT COUNT(*) FROM {new_table}")
    new_count = cursor.fetchone()[0]
    
    # In some cases, the new table might have more records due to data normalization
    # but it should never have fewer records than the old table
    if new_count < old_count:
        print(f"⚠️  Warning: {new_table} ({new_count} records) has fewer records than {old_table} ({old_count} records)")
        return False
    
    # Get sample data if available
    print(f"Comparing data from {old_table} → {new_table}...")
    
    # Get column names for the old table
    cursor.execute(f"PRAGMA table_info({old_table})")
    old_columns = [col[1] for col in cursor.fetchall()]
    
    # Get column names for the new table
    cursor.execute(f"PRAGMA table_info({new_table})")
    new_columns = [col[1] for col in cursor.fetchall()]
    
    # Find common columns to compare
    common_columns = []
    for col in old_columns:
        if col in new_columns:
            common_columns.append(col)
    
    if not common_columns:
        print(f"⚠️  Warning: No common columns found between {old_table} and {new_table}")
        return False
    
    # Choose a key column to compare records
    key_column = None
    for possible_key in ['id', 'name', 'username', 'student_name']:
        if possible_key in common_columns:
            key_column = possible_key
            break
    
    if not key_column:
        key_column = common_columns[0]  # Use first common column as key
    
    print(f"Using column '{key_column}' for comparison")
    
    # Compare a few sample records
    cursor.execute(f"SELECT {key_column} FROM {old_table} LIMIT 5")
    keys = [row[0] for row in cursor.fetchall() if row[0] is not None]
    
    if not keys:
        print(f"⚠️  Warning: Could not find sample keys in {old_table}")
        return False
    
    # Check if these keys exist in the new table
    matched_keys = 0
    for key in keys:
        cursor.execute(f"SELECT COUNT(*) FROM {new_table} WHERE {key_column} = ?", (key,))
        if cursor.fetchone()[0] > 0:
            matched_keys += 1
    
    match_rate = matched_keys / len(keys) if keys else 0
    print(f"Sample data match rate: {match_rate*100:.1f}% ({matched_keys}/{len(keys)} keys)")
    
    conn.close()
    
    # Consider migration successful if at least 80% of sample keys match
    return match_rate >= 0.8

def remove_old_tables(tables_to_remove):
    """Remove old tables from the database"""
    if not os.path.exists(DATABASE_PATH):
        print(f"❌ Error: Database file '{DATABASE_PATH}' not found")
        return
    
    # First create a backup
    success, backup_path = create_backup()
    if not success:
        print("❌ Aborting: Could not create backup")
        return
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    removed_tables = []
    skipped_tables = []
    
    for old_table in tables_to_remove:
        # Find the corresponding new table
        new_table = None
        for old_name, new_name in TABLE_MAPPINGS.items():
            if old_table == old_name:
                new_table = new_name
                break
        
        if not new_table:
            print(f"⚠️  Skipping {old_table}: Could not identify the corresponding new table")
            skipped_tables.append(old_table)
            continue
        
        # Check if the new table exists
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{new_table}'")
        if not cursor.fetchone():
            print(f"⚠️  Skipping {old_table}: New table {new_table} does not exist")
            skipped_tables.append(old_table)
            continue
        
        # Verify that data has been migrated properly
        if not verify_data_migration(old_table, new_table):
            confirm = input(f"⚠️  Data migration issues detected. Remove {old_table} anyway? (yes/no): ")
            if confirm.lower() != 'yes':
                print(f"Skipping {old_table}")
                skipped_tables.append(old_table)
                continue
        
        # Remove the old table
        try:
            print(f"🔄 Dropping table {old_table}...")
            cursor.execute(f"DROP TABLE {old_table}")
            removed_tables.append(old_table)
            print(f"✅ Removed {old_table}")
        except Exception as e:
            print(f"❌ Error removing {old_table}: {str(e)}")
            skipped_tables.append(old_table)
    
    # Remove any views that reference old tables
    for old_table in removed_tables:
        try:
            cursor.execute(f"DROP VIEW IF EXISTS {old_table}_view")
        except Exception:
            pass
    
    # Commit changes
    conn.commit()
    conn.close()
    
    # Print summary
    print("\n=== Summary ===")
    print(f"Removed tables: {', '.join(removed_tables) if removed_tables else 'None'}")
    print(f"Skipped tables: {', '.join(skipped_tables) if skipped_tables else 'None'}")
    print(f"Database backup: {backup_path}")

def main():
    print("🗑️  Database Old Table Cleanup Utility")
    print("This tool helps you safely remove old tables after data migration")
    
    # Get all existing tables and identify old tables
    old_tables = list_tables()
    
    if not old_tables:
        print("No old tables found! Your database is already clean.")
        return
    
    print("\n📋 Old tables found:")
    for table in old_tables:
        new_table = [new for old, new in TABLE_MAPPINGS.items() if old == table][0]
        print(f"  • {table} → {new_table}")
    
    # Ask for confirmation
    confirm = input("\n⚠️  Are you sure you want to remove these old tables? This cannot be undone! (yes/no): ")
    if confirm.lower() != 'yes':
        print("Operation cancelled by user")
        return
    
    # Remove old tables
    remove_old_tables(old_tables)
    
    print("\n✅ Operation complete!")
    print("Run 'python verify_database.py' to verify your database is working correctly.")

if __name__ == "__main__":
    main()
