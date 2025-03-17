"""
Import utilities to ensure consistent database access across the application
This module should be imported in all files that access the database to ensure table names
are corrected consistently.
"""

import sqlite3
import os
from database_utils import execute_query, execute_query_df, get_db_connection, fix_query_tables

# Constants
DATABASE_PATH = 'attendance_system.db'

# Create a single wrapper for the sqlite3 module that automatically fixes table names
class DatabaseWrapper:
    @staticmethod
    def connect(database_path=DATABASE_PATH):
        """Get a connection to the database, prioritizing the wrapped version"""
        return get_db_connection()
    
    @staticmethod
    def execute_query(query, params=None):
        """Execute a query with table name correction"""
        return execute_query(query, params)
    
    @staticmethod
    def execute_query_df(query, params=None):
        """Execute a query and return as DataFrame with table name correction"""
        return execute_query_df(query, params)

# Replace standard sqlite3 functionality with our wrapped version
def patch_sqlite3():
    """
    Patch the sqlite3 module to use our wrapper functions
    
    Call this at the top of any file that uses sqlite3 directly to ensure table names are corrected
    """
    # Store original connect function
    original_connect = sqlite3.connect
    
    # Replace with our wrapper
    def wrapped_connect(database=DATABASE_PATH, *args, **kwargs):
        # Only wrap connections to our specific database
        if database == DATABASE_PATH or os.path.basename(database) == os.path.basename(DATABASE_PATH):
            conn = original_connect(database, *args, **kwargs)
            
            # Replace the execute method with a wrapped version
            original_execute = conn.execute
            def wrapped_execute(query, parameters=None):
                fixed_query = fix_query_tables(query)
                if fixed_query != query:
                    print(f"Fixed query: {query} -> {fixed_query}")
                return original_execute(fixed_query, parameters)
            
            # Replace the cursor's execute method
            original_cursor = conn.cursor
            def wrapped_cursor():
                cursor = original_cursor()
                cursor_execute = cursor.execute
                def wrapped_cursor_execute(query, parameters=None):
                    fixed_query = fix_query_tables(query)
                    if fixed_query != query:
                        print(f"Fixed cursor query: {query} -> {fixed_query}")
                    return cursor_execute(fixed_query, parameters)
                cursor.execute = wrapped_cursor_execute
                return cursor
            
            # Apply wrapped methods
            conn.execute = wrapped_execute
            conn.cursor = wrapped_cursor
            return conn
        return original_connect(database, *args, **kwargs)
    
    # Replace the connect function
    sqlite3.connect = wrapped_connect

# Apply patches when importing
patch_sqlite3()

# Provide simplified imports for all database access
__all__ = ['execute_query', 'execute_query_df', 'get_db_connection', 'DatabaseWrapper']
