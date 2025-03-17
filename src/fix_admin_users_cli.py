import sqlite3
from datetime import datetime
import sys

def ensure_tables_exist():
    """Ensure all necessary tables exist"""
    conn = sqlite3.connect('attendance_system.db')
    cursor = conn.cursor()
    
    try:
        # Create user_accounts table if needed
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
        
        # Create login_logs table if needed
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
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error ensuring tables exist: {e}")
        return False
    finally:
        conn.close()

def fix_admin_users():
    """Fix any admin users with incorrect roles in the database"""
    # Ensure tables exist first
    ensure_tables_exist()
    
    conn = sqlite3.connect('attendance_system.db')
    cursor = conn.cursor()
    
    try:
        print("Looking for admin users with incorrect roles...")
        # Find users with "admin" in their username but without admin role
        cursor.execute("""
        SELECT username, role FROM user_accounts 
        WHERE (username LIKE '%admin%' OR username = 'admin') 
        AND LOWER(role) != 'admin'
        """)
        
        incorrect_users = cursor.fetchall()
        fixed_count = 0
        
        # Fix each user
        for username, current_role in incorrect_users:
            print(f"Fixing user '{username}' - changing role from '{current_role}' to 'admin'")
            cursor.execute(
                "UPDATE user_accounts SET role = 'admin' WHERE username = ?",
                (username,)
            )
            
            # Remove any student profiles for this admin user
            try:
                cursor.execute("DELETE FROM student_profiles WHERE name = ? OR username = ?", (username, username))
            except sqlite3.OperationalError:
                print("Note: student_profiles table does not exist or has different structure")
            
            # Log the fix
            try:
                cursor.execute(
                    "INSERT INTO login_logs (username, login_time, status) VALUES (?, ?, ?)",
                    ('system', datetime.now().strftime("%Y-%m-%d %H:%M:%S"), f"admin_role_fixed_{username}")
                )
            except sqlite3.OperationalError:
                print("Warning: Could not log action (login_logs table issue)")
            
            fixed_count += 1
        
        conn.commit()
        
        if fixed_count > 0:
            print(f"\n✅ Fixed {fixed_count} admin users with incorrect roles:")
            for username, old_role in incorrect_users:
                print(f"  - {username}: {old_role} → admin")
        else:
            print("\n✅ All admin users already have correct roles!")
            
        return True
    
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error fixing admin roles: {e}")
        return False
    
    finally:
        conn.close()

def manual_fix(username):
    """Manually set a specific user to admin role"""
    # Ensure tables exist first
    ensure_tables_exist()
    
    conn = sqlite3.connect('attendance_system.db')
    try:
        print(f"Setting user '{username}' to admin role...")
        cursor = conn.cursor()
        cursor.execute("SELECT username, role FROM user_accounts WHERE username = ?", (username,))
        user = cursor.fetchone()
        
        if user:
            old_role = user[1]
            cursor.execute(
                "UPDATE user_accounts SET role = 'admin' WHERE username = ?",
                (username,)
            )
            
            # Remove any student profiles for this admin user
            try:
                cursor.execute("DELETE FROM student_profiles WHERE name = ? OR username = ?", (username, username))
            except sqlite3.OperationalError:
                print("Note: student_profiles table does not exist or has different structure")
            
            # Log the change
            try:
                cursor.execute(
                    "INSERT INTO login_logs (username, login_time, status) VALUES (?, ?, ?)",
                    ('system', datetime.now().strftime("%Y-%m-%d %H:%M:%S"), f"admin_role_manual_fix_{username}")
                )
            except sqlite3.OperationalError:
                print("Warning: Could not log action (login_logs table issue)")
            
            conn.commit()
            print(f"✅ Successfully updated '{username}' from '{old_role}' to 'admin' role")
            return True
        else:
            print(f"❌ User '{username}' not found in database")
            return False
    except Exception as e:
        conn.rollback()
        print(f"❌ Error updating user: {e}")
        return False
    finally:
        conn.close()

def create_admin(username, password):
    """Create a new admin user or update an existing one"""
    # Ensure tables exist first
    ensure_tables_exist()
    
    conn = sqlite3.connect('attendance_system.db')
    try:
        print(f"Creating/updating admin user: {username}")
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT username FROM user_accounts WHERE username = ?", (username,))
        if cursor.fetchone():
            # Update existing user
            cursor.execute(
                "UPDATE user_accounts SET password = ?, role = 'admin' WHERE username = ?",
                (password, username)
            )
            conn.commit()
            print(f"✅ Updated existing user '{username}' to admin role with new password")
        else:
            # Create new user
            cursor.execute(
                "INSERT INTO user_accounts (username, password, role) VALUES (?, ?, 'admin')",
                (username, password)
            )
            conn.commit()
            print(f"✅ Created new admin user '{username}'")
        
        return True
    except Exception as e:
        conn.rollback()
        print(f"❌ Error creating/updating admin user: {e}")
        return False
    finally:
        conn.close()

def list_users():
    """List all users in the system"""
    conn = sqlite3.connect('attendance_system.db')
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT username, role FROM user_accounts ORDER BY role, username")
        users = cursor.fetchall()
        
        if users:
            print("\nCurrent users in the system:")
            print("===========================")
            for username, role in users:
                print(f"  👤 {username} - Role: {role}")
        else:
            print("No users found in the database")
    except Exception as e:
        print(f"Error listing users: {e}")
    finally:
        conn.close()

def show_help():
    print("""
Fix Admin Users CLI Tool
========================

Usage:
  python fix_admin_users_cli.py [command] [options]

Commands:
  fix               Fix all admin users with incorrect roles
  manual USERNAME   Manually set a specific user to admin role
  create USERNAME PASSWORD  Create a new admin user
  list              List all users in the system
  help              Show this help message

Examples:
  python fix_admin_users_cli.py fix
  python fix_admin_users_cli.py manual myAdmin
  python fix_admin_users_cli.py create newadmin password123
  python fix_admin_users_cli.py list
    """)

if __name__ == "__main__":
    # Process command-line arguments
    if len(sys.argv) < 2 or sys.argv[1] == 'help':
        show_help()
    
    elif sys.argv[1] == 'fix':
        fix_admin_users()
    
    elif sys.argv[1] == 'manual' and len(sys.argv) >= 3:
        manual_fix(sys.argv[2])
    
    elif sys.argv[1] == 'create' and len(sys.argv) >= 4:
        create_admin(sys.argv[2], sys.argv[3])
    
    elif sys.argv[1] == 'list':
        list_users()
    
    else:
        print("Invalid command or missing arguments")
        show_help()
