import streamlit as st
import sqlite3
import pandas as pd
import os

# Database path
DATABASE_PATH = 'attendance_system.db'

def get_db_connection():
    """Get a connection to the database"""
    return sqlite3.connect(DATABASE_PATH)

def check_db_schema():
    """Check database schema and return issues"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    issues = []
    fixes = []
    
    try:
        # Check if subjects table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='subjects'")
        if not cursor.fetchone():
            issues.append("Subjects table does not exist")
            fixes.append("""
            CREATE TABLE subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                course_code TEXT,
                credit_hours INTEGER DEFAULT 3,
                description TEXT
            )
            """)
        else:
            # Check subjects table columns
            cursor.execute("PRAGMA table_info(subjects)")
            columns = {col[1].lower(): col for col in cursor.fetchall()}
            
            # Check for id/subject_id column
            if 'id' not in columns and 'subject_id' not in columns:
                issues.append("Subjects table is missing primary key column (id or subject_id)")
                fixes.append("Schema repair required - please contact administrator")
            
            # Check for name/subject_name column
            if 'name' not in columns and 'subject_name' not in columns:
                issues.append("Subjects table is missing name column (name or subject_name)")
                fixes.append("Schema repair required - please contact administrator")
        
        # Check if professor_subject_assignments table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='professor_subject_assignments'")
        if not cursor.fetchone():
            issues.append("Professor subject assignments table does not exist")
            fixes.append("""
            CREATE TABLE professor_subject_assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                professor_username TEXT NOT NULL,
                subject_id INTEGER NOT NULL,
                assigned_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(professor_username, subject_id)
            )
            """)
        
        # Check if teacher_subjects table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='teacher_subjects'")
        if not cursor.fetchone():
            issues.append("Teacher subjects table does not exist")
            fixes.append("""
            CREATE TABLE teacher_subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id INTEGER,
                teacher_name TEXT
            )
            """)
        else:
            # Check teacher_subjects table columns
            cursor.execute("PRAGMA table_info(teacher_subjects)")
            columns = {col[1].lower(): col for col in cursor.fetchall()}
            
            if 'subject_id' not in columns:
                issues.append("Teacher subjects table is missing subject_id column")
                fixes.append("ALTER TABLE teacher_subjects ADD COLUMN subject_id INTEGER")
            
            if 'teacher_name' not in columns:
                issues.append("Teacher subjects table is missing teacher_name column")
                fixes.append("ALTER TABLE teacher_subjects ADD COLUMN teacher_name TEXT")
        
        # Check student profiles table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND (name='student_profiles' OR name='students')")
        student_table = cursor.fetchone()
        
        if not student_table:
            issues.append("No student profiles table found")
            fixes.append("""
            CREATE TABLE student_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                name TEXT,
                student_id TEXT,
                section TEXT,
                email TEXT,
                phone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
        else:
            # Check if we have the right table name
            student_table_name = student_table[0]
            if student_table_name != 'student_profiles':
                issues.append(f"Student table exists as '{student_table_name}' but code expects 'student_profiles'")
                fixes.append(f"""
                CREATE VIEW student_profiles AS
                SELECT * FROM {student_table_name}
                """)
            
            # Check for required columns
            cursor.execute(f"PRAGMA table_info({student_table_name})")
            columns = {col[1].lower(): col for col in cursor.fetchall()}
            
            missing_columns = []
            for required_col in ['username', 'name', 'section']:
                if required_col not in columns:
                    missing_columns.append(required_col)
            
            if missing_columns:
                issues.append(f"Student table is missing columns: {', '.join(missing_columns)}")
                fix_sql = []
                for col in missing_columns:
                    if col == 'username':
                        fix_sql.append(f"ALTER TABLE {student_table_name} ADD COLUMN username TEXT")
                    elif col == 'name':
                        fix_sql.append(f"ALTER TABLE {student_table_name} ADD COLUMN name TEXT")
                    elif col == 'section':
                        fix_sql.append(f"ALTER TABLE {student_table_name} ADD COLUMN section TEXT")
                
                fixes.append("\n".join(fix_sql))
    
    except Exception as e:
        issues.append(f"Error checking schema: {str(e)}")
        fixes.append("Manual database repair required")
    finally:
        conn.close()
    
    return issues, fixes

def fix_database_schema():
    """Apply fixes to database schema"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    results = []
    
    try:
        # Check and create subjects table if needed
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='subjects'")
        if not cursor.fetchone():
            cursor.execute("""
            CREATE TABLE subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                course_code TEXT,
                credit_hours INTEGER DEFAULT 3,
                description TEXT
            )
            """)
            results.append("Created subjects table")
        
        # Create compatibility view for subjects
        try:
            cursor.execute("DROP VIEW IF EXISTS subjects_compatible")
            cursor.execute("""
            CREATE VIEW subjects_compatible AS 
            SELECT 
                id as subject_id,
                name as subject_name,
                * 
            FROM subjects
            """)
            results.append("Created subjects compatibility view")
        except Exception as e:
            results.append(f"Error creating subjects compatibility view: {e}")
        
        # Check and create professor_subject_assignments table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='professor_subject_assignments'")
        if not cursor.fetchone():
            cursor.execute("""
            CREATE TABLE professor_subject_assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                professor_username TEXT NOT NULL,
                subject_id INTEGER NOT NULL,
                assigned_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(professor_username, subject_id)
            )
            """)
            results.append("Created professor_subject_assignments table")
        
        # Check and create teacher_subjects table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='teacher_subjects'")
        if not cursor.fetchone():
            cursor.execute("""
            CREATE TABLE teacher_subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id INTEGER,
                teacher_name TEXT
            )
            """)
            results.append("Created teacher_subjects table")
        else:
            # Check teacher_subjects columns and add if missing
            cursor.execute("PRAGMA table_info(teacher_subjects)")
            columns = {col[1].lower(): col for col in cursor.fetchall()}
            
            if 'subject_id' not in columns:
                cursor.execute("ALTER TABLE teacher_subjects ADD COLUMN subject_id INTEGER")
                results.append("Added subject_id column to teacher_subjects")
            
            if 'teacher_name' not in columns:
                cursor.execute("ALTER TABLE teacher_subjects ADD COLUMN teacher_name TEXT")
                results.append("Added teacher_name column to teacher_subjects")
        
        # Sync professor_subject_assignments with teacher_subjects
        cursor.execute("""
        INSERT OR IGNORE INTO teacher_subjects (subject_id, teacher_name)
        SELECT subject_id, professor_username FROM professor_subject_assignments
        """)
        
        cursor.execute("""
        INSERT OR IGNORE INTO professor_subject_assignments (professor_username, subject_id)
        SELECT teacher_name, subject_id FROM teacher_subjects
        WHERE teacher_name IS NOT NULL AND subject_id IS NOT NULL
        """)
        
        results.append("Synchronized professor_subject_assignments and teacher_subjects tables")
        
        # Fix student profiles table issues - IMPROVED VERSION
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND (name='student_profiles' OR name='students')")
        student_table = cursor.fetchone()
        
        if not student_table:
            # Create student profiles table
            cursor.execute("""
            CREATE TABLE student_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                name TEXT,
                student_id TEXT,
                section TEXT,
                email TEXT,
                phone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # Add a default record for better compatibility
            try:
                import streamlit as st
                username = st.session_state.get('username', 'default_user')
            except:
                username = 'default_user'
                
            cursor.execute("""
            INSERT OR IGNORE INTO student_profiles (username, name) VALUES (?, ?)
            """, (username, username))
            
            results.append("Created student_profiles table with default user")
        else:
            student_table_name = student_table[0]
            
            # ALWAYS create the view for maximum compatibility
            cursor.execute("DROP VIEW IF EXISTS student_profiles_view")
            cursor.execute(f"""
            CREATE VIEW student_profiles_view AS
            SELECT * FROM {student_table_name}
            """)
            results.append(f"Created student_profiles_view mapping to {student_table_name}")
            
            # If table name is 'students', also create a view named student_profiles
            if student_table_name != 'student_profiles':
                cursor.execute("DROP VIEW IF EXISTS student_profiles")
                cursor.execute(f"""
                CREATE VIEW student_profiles AS
                SELECT * FROM {student_table_name}
                """)
                results.append(f"Created student_profiles view mapping to {student_table_name}")
            
            # Add missing columns if needed
            cursor.execute(f"PRAGMA table_info({student_table_name})")
            columns = {col[1].lower(): True for col in cursor.fetchall()}
            
            if 'username' not in columns:
                cursor.execute(f"ALTER TABLE {student_table_name} ADD COLUMN username TEXT")
                results.append(f"Added username column to {student_table_name}")
            
            if 'name' not in columns:
                cursor.execute(f"ALTER TABLE {student_table_name} ADD COLUMN name TEXT")
                results.append(f"Added name column to {student_table_name}")
            
            if 'section' not in columns:
                cursor.execute(f"ALTER TABLE {student_table_name} ADD COLUMN section TEXT")
                results.append(f"Added section column to {student_table_name}")
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        results.append(f"Error fixing database schema: {str(e)}")
    finally:
        conn.close()
    
    return results

def show_schema_repair_tool():
    st.title("Database Schema Repair Tool")
    
    st.info("This tool helps fix database schema issues that might be causing errors in the application.")
    
    # Check current schema and show issues
    issues, fixes = check_db_schema()
    
    if issues:
        st.error("The following issues were found in your database schema:")
        for i, issue in enumerate(issues):
            st.write(f"{i+1}. {issue}")
            if i < len(fixes):
                with st.expander("Fix"):
                    st.code(fixes[i])
        
        # Add repair button
        if st.button("Repair Database Schema", type="primary"):
            with st.spinner("Repairing database schema..."):
                results = fix_database_schema()
            
            st.success("Database repair completed!")
            for result in results:
                st.write(f"✅ {result}")
            
            # Check if there are still issues after repair
            remaining_issues, _ = check_db_schema()
            if remaining_issues:
                st.warning("Some issues could not be fixed automatically:")
                for issue in remaining_issues:
                    st.write(f"⚠️ {issue}")
            else:
                st.success("All issues were fixed successfully!")
    else:
        st.success("No issues found in the database schema!")
    
    # Show database tables
    st.subheader("Database Tables")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        for table in tables:
            with st.expander(f"Table: {table}"):
                cursor.execute(f"PRAGMA table_info({table})")
                columns = cursor.fetchall()
                
                # Create a DataFrame for better display
                columns_df = pd.DataFrame(columns, columns=['cid', 'name', 'type', 'notnull', 'dflt_value', 'pk'])
                st.dataframe(columns_df)
                
                # Show sample data
                cursor.execute(f"SELECT * FROM {table} LIMIT 5")
                data = cursor.fetchall()
                if data:
                    data_df = pd.DataFrame(data, columns=[col[1] for col in columns])
                    st.write("Sample data:")
                    st.dataframe(data_df)
    except Exception as e:
        st.error(f"Error displaying tables: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    show_schema_repair_tool()
