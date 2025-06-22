"""
Database Maintenance Module

This module provides functions to repair and maintain the database structure,
ensuring compatibility across different schema versions.
"""
import sqlite3
import os
import streamlit as st

DATABASE_PATH = 'attendance_system.db'

def repair_attendance_tables():
    """
    Repair the attendance tables to ensure they have the required structure.
    This function fixes common issues with the attendance_records table.
    
    Returns:
        bool: True if repairs were made, False otherwise
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    changes_made = False
    
    try:
        print("Starting attendance tables repair...")
        
        # Check if attendance_records table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='attendance_records'")
        if not cursor.fetchone():
            print("attendance_records table doesn't exist, using centralized initialization...")
            
            # LEGACY: Create attendance_records table (DISABLED - using centralized initialization)
            # Use centralized database initialization instead
            from db_init import initialize_database
            initialize_database()
            
            # cursor.execute("""
            # CREATE TABLE attendance_records (
            #     id INTEGER PRIMARY KEY AUTOINCREMENT,
            #     name TEXT,
            #     username TEXT,
            #     student_username TEXT,
            #     timestamp TIMESTAMP NOT NULL,
            #     confidence REAL DEFAULT 1.0,
            #     device_id TEXT,
            #     day_of_week TEXT
            # )
            # """)
            conn.commit()
            changes_made = True
            print("Used centralized initialization for attendance_records table")
        
        # Check columns in attendance_records
        cursor.execute("PRAGMA table_info(attendance_records)")
        columns = {col[1].lower() for col in cursor.fetchall()}
        
        # Add missing columns
        required_columns = {
            'name': 'TEXT', 
            'username': 'TEXT',
            'student_username': 'TEXT',
            'timestamp': 'TIMESTAMP',
            'confidence': 'REAL',
            'device_id': 'TEXT',
            'day_of_week': 'TEXT'
        }
        
        for col, col_type in required_columns.items():
            if col.lower() not in columns:
                print(f"Adding missing column '{col}' to attendance_records")
                try:
                    cursor.execute(f"ALTER TABLE attendance_records ADD COLUMN {col} {col_type}")
                    changes_made = True
                except sqlite3.OperationalError as e:
                    print(f"Error adding column {col}: {e}")
        
        # Create indexes for better query performance
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_attendance_name ON attendance_records(name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_attendance_username ON attendance_records(username)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_attendance_student_username ON attendance_records(student_username)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_attendance_timestamp ON attendance_records(timestamp)")
            conn.commit()
        except sqlite3.OperationalError as e:
            print(f"Error creating indexes: {e}")
        
        # Create views for compatibility with different naming schemes
        try:
            cursor.execute("""
            CREATE VIEW IF NOT EXISTS attendance_with_names AS
            SELECT 
                ar.*,
                COALESCE(ar.name, ar.username, ar.student_username) AS student_name
            FROM attendance_records ar
            """)
            conn.commit()
            print("Created attendance_with_names view")
        except sqlite3.OperationalError as e:
            print(f"Error creating view: {e}")
        
        return changes_made
    
    except Exception as e:
        print(f"Error repairing attendance tables: {e}")
        return False
    finally:
        conn.close()

def ensure_table_exists(table_name, schema):
    """
    Create a table with the given schema if it doesn't exist.
    LEGACY FUNCTION: Use centralized db_init.py when possible.
    This function is kept for maintenance purposes only.
    
    Args:
        table_name (str): The name of the table
        schema (str): The schema definition
        
    Returns:
        bool: True if the table needed to be created, False otherwise
    """
    # Try to use centralized initialization first
    try:
        from db_init import initialize_database
        print(f"Using centralized initialization instead of creating {table_name} directly")
        success = initialize_database()
        if success:
            return True
    except ImportError:
        print("Centralized initialization not available, falling back to direct table creation")
    
    # Fallback to direct table creation for maintenance purposes
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    created = False
    
    try:
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        if not cursor.fetchone():
            print(f"MAINTENANCE: Creating table {table_name} with legacy method")
            cursor.execute(f"CREATE TABLE {table_name} ({schema})")
            conn.commit()
            created = True
            print(f"MAINTENANCE: Created table {table_name}")
    except Exception as e:
        print(f"Error ensuring table {table_name} exists: {e}")
    finally:
        conn.close()
        
    return created

def auto_repair_database():
    """Run a full suite of database repair operations"""
    print("Starting auto repair with centralized initialization...")
    
    # Use centralized database initialization first
    try:
        from db_init import initialize_database, check_database_integrity
        print("Using centralized database initialization...")
        success = initialize_database()
        if success:
            check_database_integrity()
            print("Centralized initialization completed successfully")
        else:
            print("Centralized initialization failed, using legacy repair methods")
    except ImportError:
        print("Centralized initialization not available, using legacy repair methods")
    
    # Repair attendance tables
    repair_attendance_tables()
    
    # LEGACY: Ensure essential tables exist (fallback for maintenance)
    print("Running legacy table checks as fallback...")
    ensure_table_exists("user_accounts", 
                       """id INTEGER PRIMARY KEY AUTOINCREMENT,
                          username TEXT UNIQUE,
                          password TEXT,
                          role TEXT,
                          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP""")
    
    ensure_table_exists("student_profiles", 
                       """id INTEGER PRIMARY KEY AUTOINCREMENT,
                          username TEXT UNIQUE NOT NULL,
                          name TEXT NOT NULL,
                          student_id TEXT UNIQUE,
                          password TEXT NOT NULL,
                          section TEXT,
                          email TEXT,
                          phone TEXT,
                          last_login TIMESTAMP,
                          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP""")
    
    ensure_table_exists("professor_profiles", 
                       """id INTEGER PRIMARY KEY AUTOINCREMENT,
                          username TEXT UNIQUE,
                          name TEXT,
                          password TEXT,
                          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP""")
    
    # Create views for easier queries
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # Create unified user view
        cursor.execute("""
        CREATE VIEW IF NOT EXISTS all_users_view AS
        SELECT 
            ua.username, 
            ua.role,
            CASE 
                WHEN ua.role = 'student' THEN sp.name
                WHEN ua.role = 'professor' THEN pp.name
                ELSE ua.username
            END as display_name,
            CASE 
                WHEN ua.role = 'student' THEN sp.section
                ELSE NULL
            END as section
        FROM user_accounts ua
        LEFT JOIN student_profiles sp ON ua.username = sp.username AND ua.role = 'student'
        LEFT JOIN professor_profiles pp ON ua.username = pp.username AND ua.role = 'professor'
        """)
        conn.commit()
    except Exception as e:
        print(f"Error creating views: {e}")
    finally:
        conn.close()
    
    return True
