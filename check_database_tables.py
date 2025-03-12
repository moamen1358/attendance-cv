import sqlite3
import os
import pandas as pd
from tabulate import tabulate

# Constants
DATABASE_PATH = 'attendance_system.db'

def get_db_connection():
    """Create a connection to the database"""
    return sqlite3.connect(DATABASE_PATH)

def check_tables():
    """Check existing tables in the database"""
    print("\n📊 Checking database tables...")
    
    if not os.path.exists(DATABASE_PATH):
        print(f"❌ Error: Database file '{DATABASE_PATH}' not found.")
        return False
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"Found {len(tables)} tables in the database:")
        for table in tables:
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            
            # Get column count
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            
            print(f"- {table}: {count} rows, {len(columns)} columns")
        
        # Check specifically for class schedule tables
        schedule_tables = [t for t in tables if t in ['class_schedules', 'control_4']]
        
        if schedule_tables:
            print("\n📅 Found these class schedule tables:")
            for table in schedule_tables:
                # Show table structure
                cursor.execute(f"PRAGMA table_info({table})")
                columns = cursor.fetchall()
                columns_df = pd.DataFrame(columns, columns=['ID', 'Name', 'Type', 'NotNull', 'DefaultValue', 'PK'])
                
                print(f"\n=== Table: {table} ===")
                print(tabulate(columns_df[['ID', 'Name', 'Type']], headers='keys', tablefmt='pretty'))
                
                # Check for teacher column
                has_teacher = any(col[1] == 'teacher' for col in columns)
                if has_teacher:
                    print("✅ This table has a 'teacher' column")
                else:
                    print("❌ This table is missing a 'teacher' column")
                
                # Show sample data
                try:
                    cursor.execute(f"SELECT * FROM {table} LIMIT 3")
                    rows = cursor.fetchall()
                    if rows:
                        column_names = [col[1] for col in columns]
                        sample_df = pd.DataFrame(rows, columns=column_names)
                        
                        print("\nSample data:")
                        print(tabulate(sample_df, headers='keys', tablefmt='pretty', showindex=False))
                except Exception as e:
                    print(f"Could not fetch sample data: {e}")
        else:
            print("\n⚠️ No class schedule tables found in the database")
            print("Run reset_class_schedule.py to create the table with sample data")
        
        return True
    
    except Exception as e:
        print(f"❌ Error checking tables: {e}")
        return False
    
    finally:
        conn.close()

def main():
    """Main function"""
    print("🔍 Database Table Check Tool")
    check_tables()

if __name__ == "__main__":
    main()
