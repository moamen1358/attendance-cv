"""
Database connection management.

This module provides functionality for managing database connections:
- Connection pooling
- Query execution utilities
- Connection context management
"""
import sqlite3
import logging
import pandas as pd
from contextlib import contextmanager
from typing import Optional, List, Dict, Any, Generator, Union
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database path with cross-platform compatibility
from src.constants import DATABASE_PATH

def get_connection():
    """Get a connection to the database"""
    return sqlite3.connect(DATABASE_PATH)

# For backward compatibility
get_db_connection = get_connection

def execute_query(query, params=None):
    """
    Execute a query with table name auto-correction
    
    Args:
        query (str): SQL query string
        params (tuple, optional): Parameters for the query
    
    Returns:
        sqlite3.Cursor: Cursor with query results
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        conn.commit()
        return cursor
    except Exception as e:
        conn.rollback()
        logger.error(f"Query error: {e}")
        logger.error(f"Query: {query}")
        logger.error(f"Params: {params}")
        raise
    finally:
        conn.close()

def execute_query_df(query, params=None):
    """
    Execute a SQL query and return results as a pandas DataFrame.
    
    Args:
        query (str): SQL query string
        params (tuple, optional): Parameters for the query
        
    Returns:
        pandas.DataFrame: Query results as DataFrame
    """
    conn = get_connection()
    
    try:
        if params:
            df = pd.read_sql_query(query, conn, params=params)
        else:
            df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        logger.error(f"DataFrame query error: {e}")
        logger.error(f"Query: {query}")
        logger.error(f"Params: {params}")
        # Return empty DataFrame on error
        return pd.DataFrame()
    finally:
        conn.close()

@contextmanager
def db_connection():
    """Context manager for database connections"""
    conn = None
    try:
        conn = get_connection()
        yield conn
    finally:
        if conn:
            conn.close()
