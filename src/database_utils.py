import sqlite3
import streamlit as st
import pandas as pd

# Constants
DATABASE_PATH = 'attendance_system.db'

def get_db_connection():
    """Get a connection to the database"""
    return sqlite3.connect(DATABASE_PATH)

def get_table_names():
    """Get all table names in the database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tables

def fix_query_tables(query):
    """
    Fix table names in SQL queries to match what exists in the database
    Handles common mapping issues like class_attendance_records → class_attendance
    """
    tables = get_table_names()
    
    # Define mappings for incorrect table names to correct ones
    common_mappings = {
        'class_attendance_records': 'class_attendance',
        'attendance_log': 'attendance_records',
        'students': 'student_profiles',
        'professors': 'user_accounts',
        'user_accounts': 'user_accounts'  # This one is correct, included for completeness
    }
    
    # For each mapping, check if the table exists and replace if needed
    for wrong_name, correct_name in common_mappings.items():
        if wrong_name in query and wrong_name not in tables and correct_name in tables:
            # Replace all occurrences in the query, preserving case and whitespace
            query = query.replace(f" {wrong_name} ", f" {correct_name} ")
            query = query.replace(f" {wrong_name}\n", f" {correct_name}\n")
            query = query.replace(f" {wrong_name},", f" {correct_name},")
            query = query.replace(f"({wrong_name})", f"({correct_name})")
            query = query.replace(f"({wrong_name} ", f"({correct_name} ")
            
            # Handle beginning and end of query
            if query.startswith(f"{wrong_name} "):
                query = f"{correct_name} " + query[len(wrong_name)+1:]
            if query.endswith(f" {wrong_name}"):
                query = query[:-len(wrong_name)-1] + f" {correct_name}"
    
    return query

def execute_query(query, params=None):
    """
    Execute a query with table name auto-correction
    
    Args:
        query (str): SQL query string
        params (tuple, optional): Parameters for the query
    
    Returns:
        list: List of rows returned by the query
    """
    # Fix table names in the query
    fixed_query = fix_query_tables(query)
    
    # If the query was modified, show info message
    if fixed_query != query:
        print(f"Query modified for compatibility: {fixed_query}")
    
    # Execute the query
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if params:
            cursor.execute(fixed_query, params)
        else:
            cursor.execute(fixed_query)
        
        results = cursor.fetchall()
        return cursor  # Return cursor instead of results for flexibility
    except Exception as e:
        conn.close()
        raise e

def execute_query_df(query, params=None):
    """
    Execute a SQL query and return the result as a pandas DataFrame.
    """
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        fixed_query = query.strip()
        print(f"Executing query: {fixed_query}")  # Added debug log
        df = pd.read_sql_query(fixed_query, conn, params=params)
        print(f"Query result columns: {df.columns.tolist()}")  # Log the columns of the result
        return df
    except Exception as e:
        print(f"Error executing query: {query}, Error: {e}")
        raise
    finally:
        conn.close()

def get_professors_list():
    """
    Get a list of professors with their usernames and names.
    Handles the case when professor_profiles table doesn't exist.
    
    Returns:
        DataFrame with 'username' and 'name' columns
    """
    conn = sqlite3.connect(DATABASE_PATH)
    try:
        # Check if professor_profiles table exists
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='professor_profiles'")
        has_profiles_table = cursor.fetchone() is not None
        
        if has_profiles_table:
            # Join user_accounts and professor_profiles
            query = """
                SELECT u.username, COALESCE(p.name, u.username) as name
                FROM user_accounts u
                LEFT JOIN professor_profiles p ON u.username = p.username
                WHERE u.role = 'professor'
                ORDER BY name
            """
        else:
            # Just get usernames and use them as names
            query = """
                SELECT username, username as name
                FROM user_accounts
                WHERE role = 'professor'
                ORDER BY username
            """
        
        df = pd.read_sql_query(query, conn)
        print(f"Found {len(df)} professors")
        return df
    except Exception as e:
        print(f"Error getting professors list: {e}")
        # Return empty DataFrame with expected columns
        return pd.DataFrame(columns=['username', 'name'])
    finally:
        conn.close()

def get_subjects_list(with_id=True):
    """
    Get a list of subjects with schema detection for different column names
    
    Args:
        with_id (bool): If True, include ID column in results
    
    Returns:
        DataFrame with subject information
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if subjects table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='subjects'")
        if not cursor.fetchone():
            print("Subjects table does not exist")
            return pd.DataFrame()
        
        # Get schema information
        cursor.execute("PRAGMA table_info(subjects)")
        columns = {col[1]: col[0] for col in cursor.fetchall()}
        
        # Determine column names to use
        id_col = 'subject_id' if 'subject_id' in columns else 'id' if 'id' in columns else None
        name_col = 'subject_name' if 'subject_name' in columns else 'name' if 'name' in columns else None
        
        if not name_col:
            print("Could not find name column in subjects table")
            return pd.DataFrame()
        
        # Create query based on available columns
        if with_id and id_col:
            query = f"SELECT {id_col} AS subject_id, {name_col} AS subject_name FROM subjects ORDER BY {name_col}"
        else:
            query = f"SELECT {name_col} AS subject_name FROM subjects ORDER BY {name_col}"
        
        df = pd.read_sql_query(query, conn)
        print(f"Found {len(df)} subjects")
        return df
    
    except Exception as e:
        print(f"Error getting subjects list: {e}")
        return pd.DataFrame()
    finally:
        conn.close()
