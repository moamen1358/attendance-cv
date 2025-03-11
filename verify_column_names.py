import sqlite3
import pandas as pd

# Constants
DATABASE_PATH = 'attendance_system.db'

def get_db_connection():
    """Get a connection to the SQLite database"""
    return sqlite3.connect(DATABASE_PATH)

def check_attendance_summary_columns():
    """Check the columns returned by the attendance summary query"""
    conn = get_db_connection()
    
    print("=== Testing Attendance Summary Query ===")
    
    # Build the query exactly as it is in get_attendance_summary function
    query = """
    SELECT 
        ca.student_name, 
        s.student_id,
        s.section,
        COUNT(CASE WHEN ca.attended = 1 THEN 1 ELSE NULL END) as attended_classes,
        COUNT(*) as total_classes,
        SUM(ca.attended) * 100.0 / COUNT(*) as attendance_rate,
        MIN(ca.class_date) as first_date,
        MAX(ca.class_date) as last_date
    FROM class_attendance ca
    LEFT JOIN students s ON ca.student_name = s.name
    WHERE 1=1 
    GROUP BY ca.student_name, s.student_id, s.section
    LIMIT 5
    """
    
    try:
        # Execute query
        df = pd.read_sql(query, conn)
        
        # Print column info
        print(f"Query returned {len(df.columns)} columns:")
        for i, col in enumerate(df.columns):
            print(f"  {i+1}. {col}")
        
        # Check if we have the expected number of columns
        expected_columns = [
            'student_name', 
            'student_id',
            'section',
            'attended_classes',
            'total_classes',
            'attendance_rate',
            'first_date',
            'last_date'
        ]
        
        if len(df.columns) == len(expected_columns):
            print("✅ Column count matches expected (8 columns)")
        else:
            print(f"❌ Column count mismatch! Expected {len(expected_columns)}, got {len(df.columns)}")
        
        # Check for table name issues
        if df.empty:
            print("\n❓ Query returned no results. Checking table names...")
            
            # Check if tables exist
            cursor = conn.cursor()
            
            # Check class_attendance table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='class_attendance'")
            if cursor.fetchone():
                print("✓ Found table: class_attendance")
            else:
                print("✗ Missing table: class_attendance")
            
            # Check class_attendance_records table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='class_attendance_records'")
            if cursor.fetchone():
                print("✓ Found table: class_attendance_records")
            else:
                print("✗ Missing table: class_attendance_records")
            
            # Check students table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='students'")
            if cursor.fetchone():
                print("✓ Found table: students")
            else:
                print("✗ Missing table: students")
            
            # Check student_profiles table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='student_profiles'")
            if cursor.fetchone():
                print("✓ Found table: student_profiles")
            else:
                print("✗ Missing table: student_profiles")
    
    except Exception as e:
        print(f"Error executing query: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_attendance_summary_columns()
    print("\nTo fix column name issues:")
    print("1. Make sure the column names in all_students_df.columns match the query result")
    print("2. Check if table names are correct (make sure tables were properly renamed)")
    print("3. Run sync_table_names.py to update all table references")
