
import sqlite3
import pandas as pd
import streamlit as st

DATABASE_PATH = '/home/invisa/Desktop/my_grad_streamlit/attendance_system.db'

def create_class_attendance_table():
    """Create the missing class_attendance table and migrate data if needed"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Create the class_attendance table if it doesn't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS class_attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_name TEXT NOT NULL,
        class_date DATE NOT NULL,
        subject TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        attended BOOLEAN NOT NULL DEFAULT 0,
        UNIQUE(student_name, class_date, subject, start_time, end_time)
    )
    """)
    
    # Add indexes for better performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_class_attendance_student ON class_attendance(student_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_class_attendance_date ON class_attendance(class_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_class_attendance_subject ON class_attendance(subject)")
    
    # Check if we need to migrate data from class_attendance_records
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='class_attendance_records'")
    table_exists = cursor.fetchone()
    
    if table_exists:
        # Check if class_attendance is empty before migrating
        cursor.execute("SELECT COUNT(*) FROM class_attendance")
        count = cursor.fetchone()[0]
        
        if count == 0:
            try:
                print("Migrating data from class_attendance_records to class_attendance...")
                
                # Get all data from class_attendance_records
                cursor.execute("""
                SELECT student_name, class_date, subject, start_time, end_time, attended 
                FROM class_attendance_records
                """)
                records = cursor.fetchall()
                
                if records:
                    # Insert all records into class_attendance
                    cursor.executemany("""
                    INSERT OR IGNORE INTO class_attendance 
                    (student_name, class_date, subject, start_time, end_time, attended)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """, records)
                    
                    print(f"Successfully migrated {len(records)} records")
                else:
                    print("No records found in class_attendance_records")
            except sqlite3.Error as e:
                print(f"Error during migration: {e}")
    
    conn.commit()
    conn.close()

def check_database_tables():
    """Display all tables in the database"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    
    print("Tables in database:")
    for table in tables:
        print(f"- {table[0]}")
    
    conn.close()

def check_class_attendance_data():
    """Check if class_attendance table has data"""
    conn = sqlite3.connect(DATABASE_PATH)
    
    try:
        # Try to query the table
        df = pd.read_sql_query("SELECT COUNT(*) as count, COUNT(DISTINCT student_name) as students FROM class_attendance", conn)
        print(f"class_attendance table has {df['count'].iloc[0]} records for {df['students'].iloc[0]} students")
        
        # Get a sample of records
        sample = pd.read_sql_query("SELECT * FROM class_attendance LIMIT 5", conn)
        if not sample.empty:
            print("\nSample records:")
            print(sample)
    except Exception as e:
        print(f"Error checking class_attendance table: {e}")
    
    conn.close()

def main():
    st.title("Database Fix: Create class_attendance Table")
    st.write("This utility will create the missing class_attendance table in your database.")
    
    if st.button("Create Table", type="primary"):
        with st.spinner("Creating table..."):
            try:
                create_class_attendance_table()
                st.success("✅ class_attendance table created successfully!")
                
                # Check and display tables in the database
                conn = sqlite3.connect(DATABASE_PATH)
                cursor = conn.cursor()
                
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
                tables = [table[0] for table in cursor.fetchall()]
                
                # Check if class_attendance was created
                if 'class_attendance' in tables:
                    # Count records in the table
                    cursor.execute("SELECT COUNT(*) FROM class_attendance")
                    count = cursor.fetchone()[0]
                    
                    if count > 0:
                        st.success(f"✅ Table contains {count} records")
                        
                        # Show sample data
                        df = pd.read_sql_query("SELECT * FROM class_attendance LIMIT 5", conn)
                        st.write("Sample data:")
                        st.dataframe(df)
                    else:
                        st.warning("⚠️ Table created but contains no records")
                else:
                    st.error("❌ Table creation failed")
                
                conn.close()
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    st.divider()
    st.subheader("Manual SQL Execution")
    
    sql = st.text_area("Enter SQL to execute:", 
                      value="""CREATE TABLE IF NOT EXISTS class_attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_name TEXT NOT NULL, 
    class_date DATE NOT NULL,
    subject TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    attended BOOLEAN NOT NULL DEFAULT 0,
    UNIQUE(student_name, class_date, subject, start_time, end_time)
)""", height=200)
    
    if st.button("Execute SQL"):
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute(sql)
            conn.commit()
            conn.close()
            st.success("SQL executed successfully!")
        except Exception as e:
            st.error(f"Error executing SQL: {str(e)}")

if __name__ == "__main__":
    main()
