import sqlite3
from datetime import datetime

# ...existing code...

def create_admin_user(username, password):
    """Create an admin user in the database"""
    try:
        # Connect to the database
        conn = sqlite3.connect('attendance_system.db')
        cursor = conn.cursor()
        
        # First, make sure the user_accounts table exists
        cursor.execute('''CREATE TABLE IF NOT EXISTS user_accounts (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username TEXT NOT NULL UNIQUE,
                            password TEXT NOT NULL,
                            role TEXT NOT NULL)''')
        
        # Check if user already exists
        cursor.execute("SELECT username, role FROM user_accounts WHERE username = ?", (username,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            existing_username, existing_role = existing_user
            # Update existing user to admin role AND fix role if it's not correctly set
            cursor.execute(
                "UPDATE user_accounts SET password = ?, role = 'admin' WHERE username = ?",
                (password, username)
            )
            
            # Also remove any student or professor records for this user to avoid confusion
            cursor.execute("DELETE FROM student_profiles WHERE name = ? OR username = ?", (username, username))
            conn.commit()
            
            # Log the update with note about role change if needed
            role_changed = existing_role.lower() != 'admin'
            status_msg = f"admin_update_role_fixed_{username}" if role_changed else f"admin_update_{username}"
            
            cursor.execute(
                "INSERT INTO login_logs (username, login_time, status) VALUES (?, ?, ?)",
                ('system', datetime.now().strftime("%Y-%m-%d %H:%M:%S"), status_msg)
            )
            conn.commit()
            
            return f"Updated user '{username}' to admin with new password" + (" (fixed incorrect role)" if role_changed else "")
        else:
            # Create new admin user
            cursor.execute(
                "INSERT INTO user_accounts (username, password, role) VALUES (?, ?, 'admin')",
                (username, password)
            )
            conn.commit()
            
            # Log the creation of the new admin user
            cursor.execute(
                "INSERT INTO login_logs (username, login_time, status) VALUES (?, ?, ?)",
                ('system', datetime.now().strftime("%Y-%m-%d %H:%M:%S"), f"admin_created_{username}")
            )
            conn.commit()
            
            return f"Created new admin user '{username}'"
    except sqlite3.Error as e:
        return f"An error occurred: {e}"
    finally:
        if conn:
            conn.close()
