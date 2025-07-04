#!/usr/bin/env python3
"""
Simple fix for missing login_logs table - no database structure changes
"""

import sqlite3
import os

DATABASE_PATH = '../attendance_system.db'

def add_missing_login_logs_table():
    """Add only the missing login_logs table to prevent errors"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        print("🔧 Adding missing login_logs table...")
        
        # Check if login_logs table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='login_logs';")
        if cursor.fetchone():
            print("✅ login_logs table already exists")
        else:
            # Create login_logs table
            cursor.execute("""
                CREATE TABLE login_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    login_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    ip_address TEXT,
                    user_agent TEXT,
                    success BOOLEAN DEFAULT TRUE,
                    role TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("✅ login_logs table created successfully")
        
        conn.commit()
        conn.close()
        
        print("🎯 Database fix complete - no existing data modified")
        
    except Exception as e:
        print(f"❌ Error fixing database: {e}")

def main():
    print("🛠️ Simple Database Fix - Adding Missing Tables Only")
    print("=" * 60)
    add_missing_login_logs_table()

if __name__ == "__main__":
    main()
