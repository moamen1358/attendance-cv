import streamlit as st
import sqlite3
from database_utils import execute_query, execute_query_df
import pandas as pd

def completely_fix_teacher_tables():
    """
    Complete fix for teacher-subject relationships
    """
    conn = sqlite3.connect('attendance_system.db')
    cursor = conn.cursor()
    
    try:
        st.write("🔄 Starting complete teacher-subject relationship fix...")
        
        # 1. Drop both tables to start fresh
        cursor.execute("DROP TABLE IF EXISTS teacher_subjects")
        cursor.execute("DROP TABLE IF EXISTS professor_subject_assignments")
        
        # 2. Create professor_subject_assignments table with correct structure
        cursor.execute("""
        CREATE TABLE professor_subject_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            professor_username TEXT,
            subject_id INTEGER,
            assigned_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(professor_username, subject_id)
        )
        """)
        st.write("✅ Created professor_subject_assignments table")
        
        # 3. Create teacher_subjects table with correct structure
        cursor.execute("""
        CREATE TABLE teacher_subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER,
            teacher_name TEXT,
            UNIQUE(subject_id, teacher_name)
        )
        """)
        st.write("✅ Created teacher_subjects table")
        
        # 4. Get professors and subjects to create some initial assignments
        cursor.execute("SELECT username FROM user_accounts WHERE role='professor'")
        professors = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT subject_id FROM subjects")
        subjects = [row[0] for row in cursor.fetchall()]
        
        if professors and subjects:
            # Create some sample assignments to demonstrate it working
            sample_count = min(len(professors) * len(subjects), 10)
            assignments_made = 0
            
            for prof in professors:
                for subj in subjects:
                    if assignments_made >= sample_count:
                        break
                        
                    try:
                        # Add to professor_subject_assignments
                        cursor.execute(
                            "INSERT INTO professor_subject_assignments (professor_username, subject_id) VALUES (?, ?)",
                            (prof, subj)
                        )
                        
                        # Add to teacher_subjects with same data
                        cursor.execute(
                            "INSERT INTO teacher_subjects (subject_id, teacher_name) VALUES (?, ?)",
                            (subj, prof)
                        )
                        
                        assignments_made += 1
                    except sqlite3.IntegrityError:
                        # Skip duplicates
                        continue
                        
                if assignments_made >= sample_count:
                    break
                    
            st.write(f"✅ Created {assignments_made} sample assignments")
            
        conn.commit()
        
        # 5. Verify the tables
        prof_assignments = execute_query_df("SELECT * FROM professor_subject_assignments")
        teacher_subjects = execute_query_df("SELECT * FROM teacher_subjects")
        
        st.write(f"📊 Professor assignments count: {len(prof_assignments)}")
        st.write(f"📊 Teacher subjects count: {len(teacher_subjects)}")
        
        # 6. Show sample data
        if not prof_assignments.empty:
            st.write("Sample professor assignments:")
            st.dataframe(prof_assignments.head(5))
            
        if not teacher_subjects.empty:
            st.write("Sample teacher subjects:")
            st.dataframe(teacher_subjects.head(5))
            
        # 7. Final verification query - check if we can join subjects to professors
        verification = execute_query_df("""
        SELECT 
            ua.username as professor_username, 
            ua.name as professor_name,
            s.subject_id,
            s.subject_name
        FROM 
            user_accounts ua
        JOIN 
            professor_subject_assignments psa ON ua.username = psa.professor_username
        JOIN 
            subjects s ON psa.subject_id = s.subject_id
        WHERE 
            ua.role = 'professor'
        LIMIT 5
        """)
        
        if not verification.empty:
            st.success("✅ Verification successful! The relationships are working correctly.")
            st.write("Sample professor-subject relationships:")
            st.dataframe(verification)
        else:
            st.error("❌ Verification failed. No relationships could be found.")
            
        return True
            
    except Exception as e:
        conn.rollback()
        st.error(f"Error during fix: {str(e)}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    st.set_page_config(page_title="Fix Teacher Subject Tables", layout="wide")
    st.title("🔧 Complete Teacher-Subject Relationship Fix")
    
    st.warning("""
    This tool will completely rebuild the teacher-subject relationship tables. 
    All existing assignments will be deleted. Use with caution!
    """)
    
    if st.button("Run Complete Fix", type="primary", use_container_width=True):
        success = completely_fix_teacher_tables()
        if success:
            st.balloons()
            st.success("""
            Tables have been fixed successfully! Now when you assign subjects to professors, 
            they will appear correctly on the professor's dashboard.
            """)
            
            # Provide a link to assign subjects
            st.markdown("""
            ### Next Steps:
            1. Go to [Subject Management](/Subject%20Management) and use the "Professor Assignments" tab
            2. Assign subjects to professors
            3. Log in as a professor to see the assignments
            """)
