
import sqlite3

def add_day_column():
    """Add day_of_week column to attendance_log table"""
    conn = sqlite3.connect('attendance_system.db')
    cursor = conn.cursor()
    
    # Check if column already exists
    cursor.execute("PRAGMA table_info(attendance_log)")
    columns = [info[1] for info in cursor.fetchall()]
    
    if 'day_of_week' not in columns:
        # Add column
        cursor.execute("ALTER TABLE attendance_log ADD COLUMN day_of_week TEXT")
        
        # Update existing records with day of week
        cursor.execute("""
        UPDATE attendance_log 
        SET day_of_week = strftime('%A', timestamp)
        """)
        
        print("Added day_of_week column and updated existing records")
        conn.commit()
    else:
        print("day_of_week column already exists")
    
    conn.close()

if __name__ == "__main__":
    add_day_column()
