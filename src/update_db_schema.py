import sqlite3
import streamlit as st

def update_user_table():
    """Ensure the users table has the required structure"""
    try:
        conn = sqlite3.connect('attendance_system.db')
        cursor = conn.cursor()
        
        # Check if users table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='users'
        """)
        table_exists = cursor.fetchone() is not None
        
        if not table_exists:
            # Create users table if it doesn't exist
            cursor.execute("""
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'student'
                )
            """)
            print("Created users table")
        else:
            # Check if role column exists
            cursor.execute("PRAGMA table_info(users)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'role' not in columns:
                # Add role column if it doesn't exist
                cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'student'")
                print("Added role column to users table")
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating database schema: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    # Run this script directly to update the database schema
    success = update_user_table()
    if success:
        st.success("Database schema updated successfully!")
    else:
        st.error("Failed to update database schema")
