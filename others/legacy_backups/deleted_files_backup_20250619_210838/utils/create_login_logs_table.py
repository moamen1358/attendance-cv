
import sqlite3
import datetime

DATABASE_PATH = '../attendance_system.db'

def create_login_logs_table():
    """Create a table to track login activity"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Create login logs table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS login_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        login_time DATETIME NOT NULL,
        ip_address TEXT,
        status TEXT,
        user_agent TEXT
    )
    ''')
    
    # Create index for faster lookups
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_login_username ON login_logs(username)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_login_time ON login_logs(login_time)')
    
    conn.commit()
    conn.close()
    
    print("Login logs table created successfully")

if __name__ == "__main__":
    create_login_logs_table()
