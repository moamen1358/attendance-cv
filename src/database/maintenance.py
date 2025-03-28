"""
Database maintenance and repair functions.

This module provides tools to fix common database issues:
- Duplicate student records
- Schema inconsistencies
- Table relationships
- Missing indexes
"""
import sqlite3
import logging
import pandas as pd
from typing import Dict, List, Tuple, Optional
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database path
DATABASE_PATH = Path('attendance_system.db')

def get_db_connection() -> sqlite3.Connection:
    """Get a connection to the SQLite database"""
    return sqlite3.connect(DATABASE_PATH)

def fix_duplicate_student_records():
    """
    Find and fix duplicate student records
    
    Returns:
        int: Number of duplicates fixed
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Look for duplicate student names in user_accounts
        cursor.execute("""
        SELECT username, COUNT(*) as count
        FROM user_accounts
        WHERE role = 'student'
        GROUP BY username
        HAVING COUNT(*) > 1
        """)
        
        duplicates = cursor.fetchall()
        
        if not duplicates:
            logger.info("No duplicate student records found")
            return 0
        
        fixed_count = 0
        for username, count in duplicates:
            # Keep the most recently used account
            cursor.execute("""
            SELECT id FROM user_accounts
            WHERE username = ? AND role = 'student'
            ORDER BY last_login DESC NULLS LAST
            LIMIT 1
            """, (username,))
            
            keep_id = cursor.fetchone()
            
            if keep_id:
                # Delete all other duplicates
                cursor.execute("""
                DELETE FROM user_accounts
                WHERE username = ? AND role = 'student' AND id != ?
                """, (username, keep_id[0]))
                
                fixed_count += cursor.rowcount
        
        conn.commit()
        logger.info(f"Fixed {fixed_count} duplicate student records")
        return fixed_count
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error fixing duplicate student records: {e}")
        return 0
    finally:
        conn.close()

def repair_attendance_tables():
    """
    Comprehensive repair of attendance-related tables
    
    Returns:
        Dict: Status of each repair action
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    results = {
        "tables_created": 0,
        "records_fixed": 0,
        "schema_fixed": 0,
        "indexes_added": 0
    }
    
    try:
        # Create attendance tables if they don't exist
        attendance_tables = [
            ("attendance_records", """
                CREATE TABLE attendance_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    name TEXT,
                    timestamp TIMESTAMP NOT NULL,
                    confidence REAL DEFAULT 1.0,
                    device_id TEXT,
                    day_of_week TEXT
                )
            """),
            ("class_attendance", """
                CREATE TABLE class_attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_name TEXT NOT NULL,
                    class_date TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    start_time TEXT,
                    end_time TEXT,
                    attended INTEGER DEFAULT 0
                )
            """),
            ("attendance_log", """
                CREATE VIEW IF NOT EXISTS attendance_log AS
                SELECT * FROM attendance_records
            """)
        ]
        
        # Create missing tables
        for table_name, create_sql in attendance_tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type IN ('table', 'view') AND name='{table_name}'")
            if not cursor.fetchone():
                cursor.execute(create_sql)
                results["tables_created"] += 1
                logger.info(f"Created {table_name}")
        
        # Fix schema issues - add missing columns
        schema_fixes = [
            ("attendance_records", "username", "TEXT", "name"),
            ("attendance_records", "name", "TEXT", "username"),
            ("attendance_records", "confidence", "REAL DEFAULT 1.0", None),
            ("attendance_records", "device_id", "TEXT", None),
            ("class_attendance", "subject", "TEXT", None),
            ("class_attendance", "attended", "INTEGER DEFAULT 0", None)
        ]
        
        for table, column, data_type, default_source in schema_fixes:
            try:
                # Check if table exists
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                if not cursor.fetchone():
                    continue
                
                # Check if column exists
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [col[1] for col in cursor.fetchall()]
                
                if column not in columns:
                    # Add missing column
                    cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {data_type}")
                    results["schema_fixed"] += 1
                    logger.info(f"Added column {column} to {table}")
                    
                    # Populate from default source if specified
                    if default_source and default_source in columns:
                        cursor.execute(f"UPDATE {table} SET {column} = {default_source}")
                        results["records_fixed"] += cursor.rowcount
                        logger.info(f"Populated {column} from {default_source} in {table}")
            except Exception as e:
                logger.error(f"Error fixing schema for {table}.{column}: {e}")
        
        # Add missing indexes for performance
        indexes = [
            ("idx_attendance_username", "attendance_records", "username"),
            ("idx_attendance_timestamp", "attendance_records", "timestamp"),
            ("idx_class_attendance_student", "class_attendance", "student_name"),
            ("idx_class_attendance_subject", "class_attendance", "subject"),
            ("idx_class_attendance_date", "class_attendance", "class_date")
        ]
        
        for index_name, table, column in indexes:
            try:
                # Check if table exists
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                if not cursor.fetchone():
                    continue
                
                # Check if index exists
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='index' AND name='{index_name}'")
                if not cursor.fetchone():
                    cursor.execute(f"CREATE INDEX {index_name} ON {table}({column})")
                    results["indexes_added"] += 1
                    logger.info(f"Created index {index_name} on {table}({column})")
            except Exception as e:
                logger.error(f"Error creating index {index_name}: {e}")
        
        # Fix view if needed
        try:
            cursor.execute("DROP VIEW IF EXISTS attendance_log")
            cursor.execute("CREATE VIEW attendance_log AS SELECT * FROM attendance_records")
            logger.info("Recreated attendance_log view")
        except Exception as e:
            logger.error(f"Error fixing attendance_log view: {e}")
        
        conn.commit()
        return results
    
    except Exception as e:
        conn.rollback()
        logger.error(f"Error repairing attendance tables: {e}")
        return results
    finally:
        conn.close()

def fix_attendance_names():
    """
    Fix inconsistent naming in attendance records
    
    Returns:
        int: Number of records fixed
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='attendance_records'")
        if not cursor.fetchone():
            logger.error("attendance_records table doesn't exist")
            return 0
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_accounts'")
        if not cursor.fetchone():
            logger.error("user_accounts table doesn't exist")
            return 0
        
        # Find records where name doesn't match username
        cursor.execute("""
        UPDATE attendance_records SET name = username
        WHERE name != username OR name IS NULL
        """)
        name_count = cursor.rowcount
        
        # Synchronize attendance_records with user_accounts
        cursor.execute("""
        UPDATE attendance_records 
        SET username = (SELECT username FROM user_accounts WHERE user_accounts.username = attendance_records.name)
        WHERE EXISTS (SELECT 1 FROM user_accounts WHERE user_accounts.username = attendance_records.name)
        AND (username != name OR username IS NULL)
        """)
        username_count = cursor.rowcount
        
        conn.commit()
        return name_count + username_count
    
    except Exception as e:
        conn.rollback()
        logger.error(f"Error fixing attendance names: {e}")
        return 0
    finally:
        conn.close()

def repair_subjects_schema():
    """
    Fix issues with subjects table schema
    
    Returns:
        bool: Success status
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if subjects table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='subjects'")
        if not cursor.fetchone():
            # Create subjects table
            cursor.execute("""
            CREATE TABLE subjects (
                subject_id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_name TEXT NOT NULL,
                course_code TEXT,
                credit_hours INTEGER DEFAULT 3,
                description TEXT
            )
            """)
            logger.info("Created subjects table")
        
        # Check the existing columns
        cursor.execute("PRAGMA table_info(subjects)")
        columns = {col[1].lower(): col[1] for col in cursor.fetchall()}
        
        # Add missing columns
        if 'subject_id' not in columns and 'id' not in columns:
            cursor.execute("ALTER TABLE subjects ADD COLUMN subject_id INTEGER")
            logger.info("Added subject_id column to subjects table")
        
        if 'subject_name' not in columns and 'name' not in columns:
            cursor.execute("ALTER TABLE subjects ADD COLUMN subject_name TEXT")
            logger.info("Added subject_name column to subjects table")
        
        if 'course_code' not in columns:
            cursor.execute("ALTER TABLE subjects ADD COLUMN course_code TEXT")
            logger.info("Added course_code column to subjects table")
        
        if 'credit_hours' not in columns:
            cursor.execute("ALTER TABLE subjects ADD COLUMN credit_hours INTEGER DEFAULT 3")
            logger.info("Added credit_hours column to subjects table")
        
        if 'description' not in columns:
            cursor.execute("ALTER TABLE subjects ADD COLUMN description TEXT")
            logger.info("Added description column to subjects table")
        
        # Create compatibility views
        cursor.execute("DROP VIEW IF EXISTS subjects_view")
        
        # Create view with both column naming conventions
        id_col = 'subject_id' if 'subject_id' in columns else 'id'
        name_col = 'subject_name' if 'subject_name' in columns else 'name'
        
        cursor.execute(f"""
        CREATE VIEW subjects_view AS
        SELECT 
            {id_col} as subject_id,
            {id_col} as id,
            {name_col} as subject_name,
            {name_col} as name,
            * 
        FROM subjects
        """)
        logger.info("Created subjects_view with both naming conventions")
        
        conn.commit()
        return True
    
    except Exception as e:
        conn.rollback()
        logger.error(f"Error repairing subjects schema: {e}")
        return False
    finally:
        conn.close()
