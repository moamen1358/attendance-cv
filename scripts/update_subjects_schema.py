import sqlite3
import os
import sys

# Add project root to path
sys.path.append('/home/invisa/Desktop/my_grad_streamlit')

def update_subjects_schema():
    """Update the subjects table with any missing columns"""
    db_path = os.path.abspath('attendance_system.db')
    print(f"Updating subjects table schema in database: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if subjects table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='subjects'")
        if not cursor.fetchone():
            print("Subjects table does not exist. Creating it...")
            cursor.execute('''
            CREATE TABLE subjects (
                subject_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                course_code TEXT,
                credit_hours INTEGER DEFAULT 3,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            print("Subjects table created successfully")
        else:
            print("Subjects table exists. Checking columns...")
            
            # Get current columns
            cursor.execute("PRAGMA table_info(subjects)")
            columns = {info[1].lower(): info for info in cursor.fetchall()}
            print(f"Current columns: {list(columns.keys())}")
            
            # Check for subject_id column
            if 'id' in columns and 'subject_id' not in columns:
                print("Found 'id' column but no 'subject_id'. Creating temporary table to rename column...")
                # Create temp table with correct schema
                cursor.execute('''
                CREATE TABLE subjects_temp (
                    subject_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    course_code TEXT,
                    credit_hours INTEGER DEFAULT 3,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                ''')
                
                # Get columns that exist in both old and new schema
                copy_columns = ['id AS subject_id', 'name']
                if 'description' in columns:
                    copy_columns.append('description')
                if 'created_at' in columns:
                    copy_columns.append('created_at')
                    
                # Copy data
                cursor.execute(f"INSERT INTO subjects_temp ({', '.join(col.split(' AS ')[1] if ' AS ' in col else col for col in copy_columns)}) SELECT {', '.join(copy_columns)} FROM subjects")
                
                # Drop old table and rename new one
                cursor.execute("DROP TABLE subjects")
                cursor.execute("ALTER TABLE subjects_temp RENAME TO subjects")
                print("Renamed 'id' column to 'subject_id'")
            
            # Check for name vs subject_name situation
            elif 'subject_name' in columns and 'name' not in columns:
                print("Found 'subject_name' but no 'name'. Creating name column...")
                cursor.execute("ALTER TABLE subjects ADD COLUMN name TEXT")
                cursor.execute("UPDATE subjects SET name = subject_name WHERE name IS NULL")
                print("Added 'name' column and copied data from 'subject_name'")
            
            # Check for course_code
            if 'course_code' not in columns:
                print("Adding missing course_code column...")
                cursor.execute("ALTER TABLE subjects ADD COLUMN course_code TEXT")
                print("Added course_code column")
            
            # Check for credit_hours
            if 'credit_hours' not in columns:
                print("Adding missing credit_hours column...")
                cursor.execute("ALTER TABLE subjects ADD COLUMN credit_hours INTEGER DEFAULT 3")
                print("Added credit_hours column")
        
        # Commit all changes
        conn.commit()
        
        # Verify the schema after changes
        cursor.execute("PRAGMA table_info(subjects)")
        final_columns = [info[1] for info in cursor.fetchall()]
        print(f"Final subjects table schema: {final_columns}")
        
        print("Schema update completed successfully")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"Error updating subjects schema: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    update_subjects_schema()
