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
    Execute a query and return results as a pandas DataFrame
    with table name auto-correction
    
    Args:
        query (str): SQL query string
        params (tuple, optional): Parameters for the query
    
    Returns:
        pandas.DataFrame: DataFrame containing query results
    """
    # Fix table names in the query
    fixed_query = fix_query_tables(query)
    
    # If the query was modified, show info message
    if fixed_query != query:
        print(f"Query modified for compatibility: {fixed_query}")
    
    # Execute the query
    conn = get_db_connection()
    try:
        if params:
            df = pd.read_sql_query(fixed_query, conn, params=params)
        else:
            df = pd.read_sql_query(fixed_query, conn)
        return df
    finally:
        conn.close()
