import streamlit as st
import sqlite3
import os
import pandas as pd
from database_utils import execute_query, execute_query_df

def force_fix_teacher_subjects():
    """
    Completely rebuild the teacher_subjects table from scratch
    """
    conn = sqlite3.connect('attendance_system.db')
    cursor = conn.cursor()
    
    try:
        # Force drop the table, ignore if it doesn't exist
        cursor.execute("DROP TABLE IF EXISTS teacher_subjects")
        
        # Create the table with the correct structure
        cursor.execute("""
        CREATE TABLE teacher_subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER,
            teacher_name TEXT
        )
        """)
        
        # First check if professor_subject_assignments exists and has data
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='professor_subject_assignments'")
        if cursor.fetchone():
            # Try to copy data from professor_subject_assignments
            try:
                cursor.execute("""
                INSERT INTO teacher_subjects (subject_id, teacher_name)
                SELECT subject_id, professor_username
                FROM professor_subject_assignments
                """)
                st.success(f"Copied {cursor.rowcount} assignments from professor_subject_assignments")
            except Exception as e:
                st.error(f"Error copying data: {str(e)}")
        
        # Make sure we have some test data if the table is empty
        cursor.execute("SELECT COUNT(*) FROM teacher_subjects")
        if cursor.fetchone()[0] == 0:
            # No assignments found, create test data if we have subjects
            cursor.execute("SELECT COUNT(*) FROM subjects")
            if cursor.fetchone()[0] > 0:
                # Get first subject ID
                cursor.execute("SELECT subject_id FROM subjects LIMIT 1")
                subject = cursor.fetchone()
                if subject:
                    subject_id = subject[0]
                    # Check if we have professors in user_accounts
                    cursor.execute("SELECT username FROM user_accounts WHERE role='professor' LIMIT 1")
                    professor = cursor.fetchone()
                    if professor:
                        teacher_name = professor[0]
                        # Add test assignment
                        cursor.execute(
                            "INSERT INTO teacher_subjects (subject_id, teacher_name) VALUES (?, ?)",
                            (subject_id, teacher_name)
                        )
                        st.info(f"Added test assignment: Subject {subject_id} assigned to {teacher_name}")
        
        conn.commit()
        
        # Verify the table structure
        cursor.execute("PRAGMA table_info(teacher_subjects)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if not columns:
            st.error("Table was created but has no columns! This indicates a serious SQLite issue.")
            return False
        
        if 'subject_id' in column_names and 'teacher_name' in column_names:
            st.success(f"Table fixed successfully with columns: {', '.join(column_names)}")
            
            # Show table data
            cursor.execute("SELECT * FROM teacher_subjects LIMIT 10")
            rows = cursor.fetchall()
            if rows:
                df = pd.DataFrame(rows, columns=['id', 'subject_id', 'teacher_name'])
                st.write("Sample data:")
                st.dataframe(df)
            else:
                st.warning("Table is empty - no assignments found")
                
            return True
        else:
            st.error(f"Table has incorrect structure. Columns: {', '.join(column_names)}")
            return False
            
    except Exception as e:
        conn.rollback()
        st.error(f"Error fixing table: {str(e)}")
        return False
    finally:
        conn.close()

def check_database_file():
    """Check if the database file exists and is accessible"""
    db_path = 'attendance_system.db'
    exists = os.path.isfile(db_path)
    readable = os.access(db_path, os.R_OK) if exists else False
    writable = os.access(db_path, os.W_OK) if exists else False
    
    st.write(f"Database file check:")
    st.write(f"- File exists: {'✅' if exists else '❌'}")
    st.write(f"- File readable: {'✅' if readable else '❌'}")
    st.write(f"- File writable: {'✅' if writable else '❌'}")
    
    if exists:
        # Check file size
        size_mb = os.path.getsize(db_path) / (1024 * 1024)
        st.write(f"- File size: {size_mb:.2f} MB")
        
        # Try opening the database
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            integrity = cursor.fetchone()[0]
            st.write(f"- Database integrity: {'✅ OK' if integrity == 'ok' else '❌ ' + integrity}")
            
            # List all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            st.write(f"- Tables found: {len(tables)}")
            st.write(f"  {', '.join(tables)}")
            
            conn.close()
            return True
        except Exception as e:
            st.error(f"Error accessing database: {str(e)}")
            return False
    else:
        st.error("Database file not found!")
        return False

if __name__ == "__main__":
    st.set_page_config(page_title="Fix Database Tables")
    st.title("📊 Database Table Repair Tool")
    
    st.write("This tool will fix issues with the teacher_subjects table")
    
    # Check database file first
    db_ok = check_database_file()
    
    if db_ok:
        if st.button("🔧 Force Fix Teacher Subjects Table", type="primary", use_container_width=True):
            if force_fix_teacher_subjects():
                st.balloons()
                st.success("Table fixed successfully! You can now return to the subject management page.")
