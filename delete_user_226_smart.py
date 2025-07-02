"""
Script to delete user ID 226 directly using SQL
This script bypasses the view issue by determining the actual underlying table
"""
import sqlite3

def delete_user_by_id_smart(user_id):
    try:
        # Connect to the database
        conn = sqlite3.connect('attendance_system.db')
        cursor = conn.cursor()
        
        # First, let's find out if user_accounts_enhanced is a view
        cursor.execute("SELECT type FROM sqlite_master WHERE name='user_accounts_enhanced'")
        result = cursor.fetchone()
        is_view = result and result[0] == 'view'
        
        # If it's a view, find the underlying table
        if is_view:
            cursor.execute("SELECT sql FROM sqlite_master WHERE name='user_accounts_enhanced'")
            view_sql = cursor.fetchone()[0]
            # Simple parsing to extract the main table name
            from_pos = view_sql.lower().find(" from ")
            if from_pos > 0:
                remaining = view_sql[from_pos + 6:].lower()
                parts = remaining.split()
                if parts:
                    table_name = parts[0].strip()
                    print(f"Found underlying table: {table_name}")
                else:
                    print("Could not parse the view SQL to find underlying table")
                    return False
            else:
                print("Could not find FROM clause in view SQL")
                return False
        else:
            table_name = "user_accounts_enhanced"
            
        # Now check if user exists in this table
        cursor.execute(f"SELECT * FROM {table_name} WHERE id=?", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            print(f"Error: User with ID {user_id} not found in {table_name}.")
            return False
            
        # Delete the user from the underlying table
        cursor.execute(f"DELETE FROM {table_name} WHERE id=?", (user_id,))
        conn.commit()
        
        # Verify deletion
        cursor.execute(f"SELECT * FROM {table_name} WHERE id=?", (user_id,))
        check = cursor.fetchone()
        
        if check:
            print(f"Error: Failed to delete user with ID {user_id}. User still exists.")
            return False
        else:
            print(f"Success: User with ID {user_id} has been deleted from {table_name}.")
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
    delete_user_by_id_smart(226)
