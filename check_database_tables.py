import sqlite3
import pandas as pd
import os

# Constants
DATABASE_PATH = 'attendance_system.db'

def get_db_connection():
    """Get a connection to the SQLite database"""
    return sqlite3.connect(DATABASE_PATH)

def check_tables_and_columns():
    """Check all tables and their columns in the database"""
    if not os.path.exists(DATABASE_PATH):
        print(f"Error: Database file '{DATABASE_PATH}' not found!")
        return
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row[0] for row in cursor.fetchall()]
    
    print(f"Found {len(tables)} tables in the database:")
    for table in tables:
        print(f"  • {table}")
    
    print("\nTable details:")
    print("=" * 60)
    
    # For each table, get the column info
    for table in tables:
        print(f"\nTABLE: {table}")
        print("-" * 60)
        
        # Get column information
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        
        # Display column info in a table format
        print(f"{'ID':<5} {'Name':<20} {'Type':<15} {'NotNull':<8} {'PK':<5} {'Default':<15}")
        print("-" * 60)
        for col in columns:
            col_id, name, type_, not_null, default_val, is_pk = col
            print(f"{col_id:<5} {name:<20} {type_:<15} {'Yes' if not_null else 'No':<8} {'Yes' if is_pk else 'No':<5} {str(default_val):<15}")
        
        # Count records
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"\nTotal records: {count}")
        
        # Show sample data if available
        if count > 0:
            cursor.execute(f"SELECT * FROM {table} LIMIT 3")
            sample = cursor.fetchall()
            print("\nSample data:")
            for row in sample:
                print(f"  {row}")
    
    conn.close()
    
    print("\nCheck complete! If you need to fix any tables, run the sync_database_tables.py script.")

if __name__ == "__main__":
    check_tables_and_columns()
