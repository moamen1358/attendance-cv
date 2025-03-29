"""
Database check utility to troubleshoot login issues.
Run this script separately to diagnose database problems.
"""
import sqlite3
import os
from pathlib import Path
import sys
import pandas as pd

# Database path
DATABASE_PATH = Path('attendance_system.db')

def print_table_info(table_name):
    """Print table schema and sample data"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    print(f"\n===== {table_name} TABLE =====")
    
    try:
        # Check if table exists
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        if not cursor.fetchone():
            print(f"Table '{table_name}' does not exist.")
            return
        
        # Get schema
        print("\nSCHEMA:")
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col[1]} ({col[2]}){' PRIMARY KEY' if col[5] else ''}")
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        print(f"\nROW COUNT: {row_count}")
        
        # Get sample data (first 5 rows)
        if row_count > 0:
            print("\nSAMPLE DATA:")
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
            rows = cursor.fetchall()
            
            # Get column names for readability
            column_names = [col[0] for col in cursor.description]
            
            for row in rows:
                print("  ---")
                for i, value in enumerate(row):
                    print(f"  {column_names[i]}: {value}")
        
    except Exception as e:
        print(f"Error accessing table: {e}")
    finally:
        conn.close()

def list_all_tables():
    """List all tables in the database"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT name, type FROM sqlite_master WHERE type='table' OR type='view' ORDER BY type, name")
        objects = cursor.fetchall()
        
        print("\n===== DATABASE OBJECTS =====")
        for obj in objects:
            name, obj_type = obj
            print(f"  {name} ({obj_type})")
        
    except Exception as e:
        print(f"Error listing tables: {e}")
    finally:
        conn.close()

def check_user_credentials():
    """Check specifically for user login credentials"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if user_accounts table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_accounts'")
        if not cursor.fetchone():
            print("\nERROR: user_accounts table does not exist!")
            print("Run reset_users.py to create default users")
            return
        
        print("\n===== USER LOGIN CREDENTIALS =====")
        cursor.execute("SELECT username, password, role FROM user_accounts")
        users = cursor.fetchall()
        
        if not users:
            print("No users found in the database!")
        else:
            print(f"Found {len(users)} users:")
            for user in users:
                username, password, role = user
                print(f"  Username: {username}, Password: {password}, Role: {role}")
        
        # Check if default users exist
        print("\nCHECKING DEFAULT USERS:")
        for default_user in [('admin', 'admin'), ('professor', 'professor'), ('student', 'student')]:
            username, expected_password = default_user
            cursor.execute("SELECT password, role FROM user_accounts WHERE username = ?", (username,))
            result = cursor.fetchone()
            
            if result:
                actual_password, role = result
                if actual_password == expected_password:
                    print(f"  ✅ {username}: correct password and role ({role})")
                else:
                    print(f"  ❌ {username}: WRONG PASSWORD! Expected '{expected_password}', got '{actual_password}'")
            else:
                print(f"  ❌ {username}: NOT FOUND in database!")
        
    except Exception as e:
        print(f"Error checking user credentials: {e}")
    finally:
        conn.close()

def main():
    """Main diagnostic function"""
    print(f"Database path: {DATABASE_PATH.absolute()}")
    
    if not DATABASE_PATH.exists():
        print("ERROR: Database file does not exist!")
        return
    
    print(f"Database size: {DATABASE_PATH.stat().st_size / 1024:.2f} KB")
    
    # List all tables
    list_all_tables()
    
    # Check tables required for login
    print_table_info("user_accounts")
    check_user_credentials()
    
    # Print profile tables
    print_table_info("student_profiles")
    print_table_info("professor_profiles")
    
    print("\nDiagnostic complete. If login issues persist, run reset_users.py to recreate default users.")

if __name__ == "__main__":
    main()
