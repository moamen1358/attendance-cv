"""
Database utilities for executing queries and managing connections.

This module provides core database functionality including:
- Query execution
- DataFrame conversion
- Schema detection
- Table compatibility management
"""
import sqlite3
import pandas as pd
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database path - use pathlib for cross-platform compatibility
DATABASE_PATH = Path('attendance_system.db')

def get_db_connection():
    """Get a connection to the database"""
    return sqlite3.connect(DATABASE_PATH)

# Import functions from database_utils.py
# Copy the core functions from database_utils.py:
# - execute_query
# - execute_query_df
# - fix_query_tables
# - get_table_names
# - ensure_student_profiles_compatibility
# - get_attendance_records_schema
