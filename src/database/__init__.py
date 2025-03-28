"""
Database package for the attendance system.

This package provides database functionality:
- Connection management (connection.py)
- Schema management (schema.py)
- Data models and ORM (models.py)
- Common queries (queries.py)
- Database maintenance (maintenance.py)
"""

# Import from connection.py instead of utils.py
from src.database.connection import get_connection, execute_query, execute_query_df
from src.database.maintenance import repair_attendance_tables, fix_duplicate_student_records
from src.database.schema import ensure_tables_exist, validate_schema

__all__ = [
    'get_connection',
    'execute_query',
    'execute_query_df',
    'repair_attendance_tables',
    'fix_duplicate_student_records',
    'ensure_tables_exist',
    'validate_schema'
]
