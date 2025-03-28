"""
Database schema management.

This module provides functionality for managing the database schema:
- Schema initialization
- Schema migrations
- Schema validation and repair
"""
import sqlite3
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database path
DATABASE_PATH = Path('attendance_system.db')

# Migrations directory
MIGRATIONS_DIR = Path('migrations')

def ensure_tables_exist() -> bool:
    """Ensure all required tables exist in the database"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # Define essential tables
        essential_tables = {
            'user_accounts': '''
                CREATE TABLE user_accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    role TEXT NOT NULL,
                    last_login TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''',
            'student_profiles': '''
                CREATE TABLE student_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    student_id TEXT UNIQUE,
                    section TEXT,
                    email TEXT,
                    phone TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (username) REFERENCES user_accounts(username)
                )
            ''',
            'professor_profiles': '''
                CREATE TABLE professor_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL, 
                    department TEXT,
                    email TEXT,
                    phone TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (username) REFERENCES user_accounts(username)
                )
            ''',
            'subjects': '''
                CREATE TABLE subjects (
                    subject_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subject_name TEXT NOT NULL,
                    course_code TEXT,
                    credit_hours INTEGER DEFAULT 3,
                    description TEXT
                )
            ''',
            'attendance_records': '''
                CREATE TABLE attendance_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    name TEXT,
                    timestamp TIMESTAMP NOT NULL,
                    confidence REAL DEFAULT 1.0,
                    device_id TEXT,
                    day_of_week TEXT,
                    FOREIGN KEY (username) REFERENCES user_accounts(username)
                )
            '''
        }
        
        # Check existing tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = {row[0] for row in cursor.fetchall()}
        
        # Create missing tables
        tables_created = 0
        for table, create_sql in essential_tables.items():
            if table not in existing_tables:
                cursor.execute(create_sql)
                tables_created += 1
                logger.info(f"Created table: {table}")
        
        conn.commit()
        return True
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error ensuring tables: {e}")
        return False
    finally:
        conn.close()

def validate_schema() -> bool:
    """Validate database schema and fix inconsistencies"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # First ensure all required tables exist
        ensure_tables_exist()
        
        # Fix common column issues
        fixes = [
            # Add missing columns to user_accounts if needed
            "SELECT 1 FROM pragma_table_info('user_accounts') WHERE name='password_hash'",
            "ALTER TABLE user_accounts ADD COLUMN password_hash TEXT",
            
            "SELECT 1 FROM pragma_table_info('user_accounts') WHERE name='salt'",
            "ALTER TABLE user_accounts ADD COLUMN salt TEXT",
            
            # Add indexes for performance
            "CREATE INDEX IF NOT EXISTS idx_attendance_username ON attendance_records(username)",
            "CREATE INDEX IF NOT EXISTS idx_attendance_timestamp ON attendance_records(timestamp)",
        ]
        
        # Execute fixes in pairs (check, fix if needed)
        for i in range(0, len(fixes), 2):
            check_sql = fixes[i]
            fix_sql = fixes[i+1]
            
            # Check if fix is needed
            try:
                cursor.execute(check_sql)
                if not cursor.fetchone():
                    try:
                        cursor.execute(fix_sql)
                        logger.info(f"Applied schema fix: {fix_sql}")
                    except sqlite3.OperationalError:
                        logger.warning(f"Could not apply fix (already exists?): {fix_sql}")
            except sqlite3.OperationalError:
                logger.warning(f"Could not check if fix is needed: {check_sql}")
        
        conn.commit()
        return True
    
    except Exception as e:
        conn.rollback()
        logger.error(f"Error validating schema: {e}")
        return False
    finally:
        conn.close()
