import sqlite3
import streamlit as st
from datetime import datetime

def setup_admin_tables():
    """Create essential tables for admin functionality"""
    conn = sqlite3.connect('attendance_system.db')
    cursor = conn.cursor()
    
    try:
        # Create user_accounts table if it doesn't exist
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_login DATETIME
        )
        """)
        
        # Create login_logs table if it doesn't exist
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS login_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            login_time DATETIME NOT NULL,
            ip_address TEXT,
            status TEXT,
            user_agent TEXT
        )
        """)
        
        # Ensure the admin user exists - with plain text password
        cursor.execute("SELECT COUNT(*) FROM user_accounts WHERE username = 'admin'")
        if cursor.fetchone()[0] == 0:
            # Admin doesn't exist yet, create it with plain text password
            cursor.execute(
                "INSERT INTO user_accounts (username, password, role) VALUES (?, ?, ?)",
                ("admin", "admin", "admin")  # Store password as plain text
            )
            print("Created admin user")
        
        # Ensure dev accounts exist for development - with plain text passwords
        cursor.execute("SELECT COUNT(*) FROM user_accounts")
        count = cursor.fetchone()[0]
        
        if count <= 1:  # Only admin exists
            # Add teacher and student dev accounts with plain text passwords
            cursor.execute(
                "INSERT INTO user_accounts (username, password, role) VALUES (?, ?, ?)",
                ("teacher", "teacher", "professor")  # Store password as plain text
            )
            cursor.execute(
                "INSERT INTO user_accounts (username, password, role) VALUES (?, ?, ?)",
                ("student", "student", "student")  # Store password as plain text
            )
            print("Created development accounts with plain text passwords")
        
        # Add a log of table creation
        cursor.execute(
            "INSERT INTO login_logs (username, login_time, status) VALUES (?, ?, ?)",
            ("system", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "tables_setup")
        )
            
        conn.commit()
        return True
        
    except Exception as e:
        print(f"Error setting up admin tables: {e}")
        conn.rollback()
        return False
    
    finally:
        conn.close()

if __name__ == "__main__":
    if setup_admin_tables():
        print("Admin tables setup successfully")
    else:
        print("Failed to setup admin tables")
