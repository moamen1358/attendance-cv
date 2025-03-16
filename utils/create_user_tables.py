import sqlite3
import os
import streamlit as st
import pandas as pd

DATABASE_PATH = '../attendance_system.db'

def create_user_tables():
    """Create all necessary user tables for the system"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Create user_accounts table (main table for authentication)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        hashed_password TEXT NOT NULL,
        role TEXT NOT NULL,
        email TEXT,
        full_name TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create professor_profiles table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS professor_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        name TEXT NOT NULL,
        email TEXT,
        department TEXT,
        office TEXT,
        phone TEXT,
        profile_image BLOB
    )
    ''')
    
    # Check if student_profiles table exists, if not create it
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='student_profiles'")
    if not cursor.fetchone():
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS student_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT UNIQUE,
            name TEXT NOT NULL,
            username TEXT UNIQUE,
            password TEXT,
            section TEXT,
            email TEXT,
            phone TEXT,
            address TEXT,
            profile_image BLOB
        )
        ''')
    
    # Create index for faster lookups
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_username ON user_accounts(username)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_student_name ON student_profiles(name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_professor_username ON professor_profiles(username)')
    
    # Create default admin user if no users exist
    cursor.execute("SELECT COUNT(*) FROM user_accounts")
    if cursor.fetchone()[0] == 0:
        # Plain text 'admin' for simplicity in development (not for production)
        cursor.execute('''
        INSERT INTO user_accounts (username, hashed_password, role, full_name)
        VALUES (?, ?, ?, ?)
        ''', ('admin', 'admin', 'admin', 'System Administrator'))
        
        # Add a demo professor
        cursor.execute('''
        INSERT INTO professor_profiles (username, password, name, department)
        VALUES (?, ?, ?, ?)
        ''', ('teacher', 'teacher', 'Demo Teacher', 'Computer Science'))
        
        # Add a demo student
        try:
            cursor.execute('''
            INSERT INTO student_profiles (student_id, name, username, password, section)
            VALUES (?, ?, ?, ?, ?)
            ''', ('S12345', 'Demo Student', 'student', 'student', 'A'))
        except sqlite3.IntegrityError:
            pass # Student might already exist
    
    conn.commit()
    conn.close()
    
    print("User tables created and populated with default users")

def show_create_tables_ui():
    st.title("Database Setup: Create User Tables")
    st.write("This utility will create the necessary user tables in your database.")
    
    if st.button("Create Tables", type="primary"):
        with st.spinner("Creating tables..."):
            try:
                create_user_tables()
                st.success("✅ User tables created successfully!")
                
                # Show database status
                conn = sqlite3.connect(DATABASE_PATH)
                
                tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn)
                st.write("### Current Database Tables:")
                st.dataframe(tables)
                
                st.write("### Default Users:")
                users = pd.read_sql("SELECT username, role FROM user_accounts", conn)
                st.dataframe(users)
                
                conn.close()
                
            except Exception as e:
                st.error(f"Error: {str(e)}")

if __name__ == "__main__":
    show_create_tables_ui()
