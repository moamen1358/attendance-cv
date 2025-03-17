# Add this to your database initialization script

def create_professor_assignments_table():
    execute_query("""
    CREATE TABLE IF NOT EXISTS professor_subject_assignments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        professor_username TEXT,
        subject_id TEXT,
        assigned_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(professor_username, subject_id)
    )
    """)
    
    # Also create or update the teacher_subjects table for compatibility
    execute_query("""
    CREATE TABLE IF NOT EXISTS teacher_subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject_id INTEGER,
        teacher_name TEXT
    )
    """)
    
    # Import and run sync to ensure tables are in sync
    from sync_professor_tables import sync_professor_tables
    sync_professor_tables()
