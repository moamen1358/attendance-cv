import sqlite3
from database_utils import execute_query
import streamlit as st
import sync_professor_tables

def initialize_all_tables():
    """
    Initialize and fix all required tables in the database
    """
    st.write("Starting database table initialization...")
    
    conn = sqlite3.connect('attendance_system.db')
    cursor = conn.cursor()
    
    try:
        # 1. Make sure subjects table exists
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS subjects (
            subject_id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_name TEXT NOT NULL,
            course_code TEXT,
            credit_hours INTEGER DEFAULT 3,
            description TEXT
        )
        ''')
        st.write("✅ Subject table initialized")
        
        # 2. Fix teacher_subjects table
        success, msg = sync_professor_tables.fix_teacher_subjects_table()
        st.write(f"{'✅' if success else '❌'} Teacher subjects table: {msg}")
        
        # 3. Sync professor assignments
        success, msg = sync_professor_tables.sync_professor_tables()
        st.write(f"{'✅' if success else '❌'} Professor assignments: {msg}")
        
        # 4. Verify that the tables have the expected structure
        cursor.execute("PRAGMA table_info(teacher_subjects)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'teacher_name' in column_names and 'subject_id' in column_names:
            st.write("✅ Teacher subjects table has the correct columns")
        else:
            st.error(f"❌ Teacher subjects table has incorrect structure: {', '.join(column_names)}")
            
        # Count of records in tables
        cursor.execute("SELECT COUNT(*) FROM subjects")
        subjects_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM teacher_subjects")
        teacher_subjects_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM professor_subject_assignments")
        prof_assignments_count = cursor.fetchone()[0]
        
        st.write(f"📊 Table counts - Subjects: {subjects_count}, Teacher assignments: {teacher_subjects_count}, Professor assignments: {prof_assignments_count}")
        
        st.success("Database initialization completed!")
        return True
    
    except Exception as e:
        conn.rollback()
        st.error(f"Error initializing tables: {e}")
        return False
    
    finally:
        conn.close()

if __name__ == "__main__":
    st.set_page_config(page_title="Database Initialization")
    st.title("Database Tables Initialization")
    
    if st.button("Initialize All Tables", use_container_width=True):
        if initialize_all_tables():
            st.balloons()
