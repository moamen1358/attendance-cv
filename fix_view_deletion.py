"""
This script adds additional functionality to check if a table is actually a view 
before attempting to delete from it, and provides the user with a more helpful error message.
"""
import sqlite3

def is_view(conn, table_name):
    """Check if a table is actually a view"""
    cursor = conn.cursor()
    cursor.execute("SELECT type FROM sqlite_master WHERE name=?", (table_name,))
    result = cursor.fetchone()
    return result and result[0] == 'view'

def get_underlying_table(conn, view_name):
    """Get the underlying table for a view"""
    cursor = conn.cursor()
    cursor.execute("SELECT sql FROM sqlite_master WHERE name=?", (view_name,))
    result = cursor.fetchone()
    if result and result[0]:
        # This is a simple extraction that works for basic views
        # For complex views with joins, this won't work perfectly
        sql = result[0].lower()
        from_pos = sql.find(" from ")
        if from_pos > 0:
            remaining = sql[from_pos + 6:]  # Skip " from "
            # Find the first table name
            parts = remaining.split()
            if parts:
                return parts[0].strip()
    return None

def apply_view_check_to_explorer():
    """Instructions on how to modify the enhanced_db_explorer.py file"""
    modification_instructions = """
    To fix the issue with deleting from views, you need to modify the enhanced_db_explorer.py file:
    
    1. Add two new functions near the top of the file (after imports):
    
    ```python
    def is_view(table_name):
        """Check if a table is actually a view"""
        conn = None
        try:
            conn = sqlite3.connect('attendance_system.db')
            cursor = conn.cursor()
            cursor.execute("SELECT type FROM sqlite_master WHERE name=?", (table_name,))
            result = cursor.fetchone()
            return result and result[0] == 'view'
        except Exception as e:
            st.error(f"Error checking if table is a view: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def get_underlying_table(view_name):
        """Get the underlying table for a view"""
        conn = None
        try:
            conn = sqlite3.connect('attendance_system.db')
            cursor = conn.cursor()
            cursor.execute("SELECT sql FROM sqlite_master WHERE name=?", (view_name,))
            result = cursor.fetchone()
            if result and result[0]:
                # This is a simple extraction that works for basic views
                sql = result[0].lower()
                from_pos = sql.find(" from ")
                if from_pos > 0:
                    remaining = sql[from_pos + 6:]  # Skip " from "
                    # Find the first table name
                    parts = remaining.split()
                    if parts:
                        return parts[0].strip()
            return None
        except Exception as e:
            st.error(f"Error getting underlying table: {e}")
            return None
        finally:
            if conn:
                conn.close()
    ```
    
    2. Modify the delete section to check if the table is a view and provide helpful information:
    
    Before the "Check if record exists" comment, add this check:
    
    ```python
    # Check if table is a view (cannot delete directly from views)
    if is_view(table):
        underlying_table = get_underlying_table(table)
        error_msg = f"⚠️ Cannot delete from '{table}' because it is a view, not a table."
        if underlying_table:
            error_msg += f" Try deleting from the underlying table: '{underlying_table}'"
        st.error(error_msg)
        return
    ```
    
    This will help users understand why they can't delete from certain tables and guide them to the correct table.
    """
    
    print(modification_instructions)

if __name__ == "__main__":
    apply_view_check_to_explorer()
