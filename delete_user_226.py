"""
Script to delete user ID 226 from users_enhanced table
"""
import sqlite3
import sys

def delete_user_by_id(user_id):
    try:
        # Connect to the database
        conn = sqlite3.connect('attendance_system.db')
        cursor = conn.cursor()
        
        # Check if the user exists
        cursor.execute("SELECT * FROM users_enhanced WHERE id=?", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            print(f"Error: User with ID {user_id} not found in users_enhanced table.")
            return False
        
        # Store user info for confirmation
        user_info = f"ID: {user[0]}, Username: {user[1]}, Full Name: {user[3] if len(user) > 3 else 'N/A'}"
        
        # Delete the user
        cursor.execute("DELETE FROM users_enhanced WHERE id=?", (user_id,))
        conn.commit()
        
        # Verify deletion
        cursor.execute("SELECT * FROM users_enhanced WHERE id=?", (user_id,))
        check = cursor.fetchone()
        
        if check:
            print(f"Error: Failed to delete user with ID {user_id}. User still exists.")
            return False
        else:
            print(f"Success: User {user_info} has been deleted.")
            return True
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    # Delete user with ID 226
    delete_user_by_id(226)
