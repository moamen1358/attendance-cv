import sqlite3

# Constants
DATABASE_PATH = 'attendance_system.db'

def get_db_connection():
    """Get a connection to the SQLite database"""
    return sqlite3.connect(DATABASE_PATH)

def ensure_section_column_exists():
    """Ensure the section column exists in the student_profiles table"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if we're using the old or new table name
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND (name='students' OR name='student_profiles')")
    tables = [row[0] for row in cursor.fetchall()]
    
    if 'student_profiles' in tables:
        student_table = 'student_profiles'
    elif 'students' in tables:
        student_table = 'students'
    else:
        print("Error: Neither 'students' nor 'student_profiles' table found!")
        conn.close()
        return False
    
    # Check if section column exists
    cursor.execute(f"PRAGMA table_info({student_table})")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'section' not in columns:
        print(f"Adding section column to {student_table} table")
        cursor.execute(f"ALTER TABLE {student_table} ADD COLUMN section TEXT")
        conn.commit()
        print(f"Column 'section' added to {student_table} table")
    else:
        print(f"Column 'section' already exists in {student_table} table")
    
    conn.close()
    return True

def main():
    print("=== Database Table Synchronization ===")
    print("\nThis script will ensure that all required columns exist in your database tables.")
    
    # Ensure section column exists
    if ensure_section_column_exists():
        print("\nDatabase synchronization complete!")
    else:
        print("\nDatabase synchronization failed!")
    
    print("\nYou can run check_database_tables.py to verify your database structure.")

if __name__ == "__main__":
    main()
