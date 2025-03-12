import sqlite3
import os
import pandas as pd
from tabulate import tabulate

# Constants
DATABASE_PATH = 'attendance_system.db'

def get_db_connection():
    """Create a connection to the database"""
    return sqlite3.connect(DATABASE_PATH)

def update_section_names():
    """Update section names: WC1 -> SEC 1, keep SEC 2 as is"""
    print("\n🔄 Updating section names in class schedule...")
    
    if not os.path.exists(DATABASE_PATH):
        print(f"❌ Error: Database file '{DATABASE_PATH}' not found.")
        return False
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # First check if we have the class_schedules table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='class_schedules'")
        if not cursor.fetchone():
            print("❌ Table 'class_schedules' not found!")
            return False
        
        # Check if we have any section values as 'WC1'
        cursor.execute("SELECT COUNT(*) FROM class_schedules WHERE section='WC1'")
        wc1_count = cursor.fetchone()[0]
        
        if wc1_count == 0:
            print("✅ No 'WC1' sections found - they may already be updated")
            
            # Double check if we have SEC 1 instead
            cursor.execute("SELECT COUNT(*) FROM class_schedules WHERE section='SEC 1'")
            sec1_count = cursor.fetchone()[0]
            
            if sec1_count > 0:
                print(f"✅ Found {sec1_count} 'SEC 1' sections - table appears to be already updated")
                
                # Show current distribution
                cursor.execute("SELECT section, COUNT(*) FROM class_schedules GROUP BY section")
                distribution = cursor.fetchall()
                print("\nCurrent section distribution:")
                for section, count in distribution:
                    print(f"- {section}: {count} classes")
                
                return True
        
        # Start a transaction
        cursor.execute("BEGIN TRANSACTION")
        
        # Update WC1 to SEC 1
        cursor.execute("UPDATE class_schedules SET section='SEC 1' WHERE section='WC1'")
        rows_affected = cursor.rowcount
        
        # Commit the changes
        cursor.execute("COMMIT")
        
        print(f"✅ Updated {rows_affected} rows from 'WC1' to 'SEC 1'")
        
        # Show updated data
        print("\nShowing updated section data:")
        cursor.execute("""
        SELECT subject, day, start_time, end_time, type, section, teacher
        FROM class_schedules
        ORDER BY subject, section, day
        LIMIT 10
        """)
        
        rows = cursor.fetchall()
        if rows:
            df = pd.DataFrame(rows, columns=['Subject', 'Day', 'Start Time', 'End Time', 'Type', 'Section', 'Teacher'])
            print(tabulate(df, headers='keys', tablefmt='pretty', showindex=False))
        
        # Show distribution of sections
        cursor.execute("SELECT section, COUNT(*) FROM class_schedules GROUP BY section")
        distribution = cursor.fetchall()
        print("\nUpdated section distribution:")
        for section, count in distribution:
            print(f"- {section}: {count} classes")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating section names: {e}")
        if 'cursor' in locals():
            cursor.execute("ROLLBACK")
        return False
        
    finally:
        conn.close()

def main():
    """Main function"""
    print("🔧 Class Schedule Section Update Tool")
    print("This will update all 'WC1' section names to 'SEC 1' while keeping 'SEC 2' as is.")
    
    # Ask for confirmation
    confirm = input("\nDo you want to continue with updating section names? (yes/no): ")
    
    if confirm.lower() != 'yes':
        print("Operation cancelled.")
        return
    
    # Update section names
    update_section_names()
    
    print("\nDone! Section names have been updated in the class_schedules table.")

if __name__ == "__main__":
    main()
