import sqlite3
import streamlit as st
import pandas as pd

DATABASE_PATH = '../attendance_system.db'

def check_student_profiles_structure():
    """Check and fix the structure of the student_profiles table"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Check if student_profiles table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='student_profiles'")
    if not cursor.fetchone():
        st.error("Student profiles table does not exist!")
        # Create the table with proper structure
        cursor.execute('''
        CREATE TABLE student_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            name TEXT NOT NULL,
            username TEXT,
            section TEXT,
            password TEXT
        )
        ''')
        conn.commit()
        st.success("Created student_profiles table with correct structure")
        conn.close()
        return
    
    # Check if username column exists
    cursor.execute("PRAGMA table_info(student_profiles)")
    columns = [info[1] for info in cursor.fetchall()]
    
    # Add missing username column if needed
    if "username" not in columns:
        cursor.execute("ALTER TABLE student_profiles ADD COLUMN username TEXT")
        
        # Update username column to match name (as a fallback)
        cursor.execute("UPDATE student_profiles SET username = name WHERE username IS NULL")
        
        conn.commit()
        st.success("Added username column to student_profiles table")
    
    # Check if section column exists
    if "section" not in columns:
        cursor.execute("ALTER TABLE student_profiles ADD COLUMN section TEXT")
        conn.commit()
        st.success("Added section column to student_profiles table")
    
    # Check if student_id column exists
    if "student_id" not in columns:
        cursor.execute("ALTER TABLE student_profiles ADD COLUMN student_id TEXT")
        conn.commit()
        st.success("Added student_id column to student_profiles table")
        
    # Create indexes for better performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_student_name ON student_profiles(name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_student_username ON student_profiles(username)")
    conn.commit()
    
    # Show current table structure
    cursor.execute("PRAGMA table_info(student_profiles)")
    structure = cursor.fetchall()
    structure_df = pd.DataFrame(structure, columns=["cid", "name", "type", "notnull", "dflt_value", "pk"])
    
    conn.close()
    return structure_df

def show_ui():
    st.title("Fix Student Profiles Table")
    st.write("This utility will check and fix the structure of the student_profiles table.")
    
    if st.button("Check and Fix Table Structure", key="fix_button"):
        structure_df = check_student_profiles_structure()
        
        if structure_df is not None:
            st.write("### Current Table Structure")
            st.dataframe(structure_df)
            
            # Test the table with a sample query
            conn = sqlite3.connect(DATABASE_PATH)
            try:
                # Count records
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM student_profiles")
                count = cursor.fetchone()[0]
                
                if count == 0:
                    st.warning("Student profiles table exists but contains no data.")
                    
                    # Add demo student
                    st.write("### Adding Demo Student")
                    cursor.execute('''
                    INSERT INTO student_profiles (student_id, name, username, section, password)
                    VALUES (?, ?, ?, ?, ?)
                    ''', ('S12345', 'Demo Student', 'student', 'A', 'student'))
                    
                    conn.commit()
                    st.success("Added demo student to database")
                else:
                    # Show sample data
                    df = pd.read_sql_query("SELECT * FROM student_profiles LIMIT 5", conn)
                    st.write("### Sample Data")
                    st.dataframe(df)
            except Exception as e:
                st.error(f"Error testing table: {e}")
            finally:
                conn.close()
            
        st.success("Done! Your student_profiles table should now be correctly structured.")

if __name__ == "__main__":
    show_ui()
