import sqlite3
import sys
import os
# Remove hashlib import as we're not hashing passwords

def create_admin_user(username="admin", password="admin"):
    """
    Create an admin user in the user_accounts table with plain text password
    
    Args:
        username: Admin username (default: admin)
        password: Admin password (default: admin)
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        print(f"Creating admin user: {username}")
        
        # Connect to the database
        conn = sqlite3.connect('attendance_system.db')
        cursor = conn.cursor()
        
        # First, make sure the user_accounts table exists
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
        conn.commit()
        
        # Check if the admin user already exists
        cursor.execute("SELECT username FROM user_accounts WHERE username = ?", (username,))
        if cursor.fetchone():
            print(f"Admin user '{username}' already exists.")
            
            # Option to update the password
            update = input(f"Do you want to update the password for '{username}'? (y/n): ")
            if update.lower() == 'y':
                # Update with plain text password
                cursor.execute(
                    "UPDATE user_accounts SET password = ? WHERE username = ?",
                    (password, username)  # Store password as plain text
                )
                conn.commit()
                print(f"Password updated for admin user '{username}'")
                return True
            else:
                print("No changes made.")
                return False
        
        # Create the admin user with plain text password
        cursor.execute(
            "INSERT INTO user_accounts (username, password, role) VALUES (?, ?, ?)",
            (username, password, "admin")  # Store password as plain text
        )
        conn.commit()
        
        print(f"Admin user '{username}' created successfully!")
        return True
        
    except Exception as e:
        print(f"Error creating admin user: {e}")
        return False
    
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    # Get username and password from command line args or use defaults
    if len(sys.argv) > 2:
        username = sys.argv[1]
        password = sys.argv[2]
        create_admin_user(username, password)
    elif len(sys.argv) > 1:
        username = sys.argv[1]
        password = input(f"Enter password for admin user '{username}': ")
        create_admin_user(username, password)
    else:
        # Interactive mode
        print("Creating new admin user")
        username = input("Enter admin username (default: admin): ")
        if not username:
            username = "admin"
        password = input(f"Enter password for {username} (default: admin): ")
        if not password:
            password = "admin"
        create_admin_user(username, password)