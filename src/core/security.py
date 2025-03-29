"""
Security utilities for authentication and authorization.

This module provides security functions:
- Simple password verification (plain text)
- User authentication directly from user_accounts table
"""
import sqlite3
import logging
from datetime import datetime
from pathlib import Path

# Setup logging
logger = logging.getLogger(__name__)

# Database path
DATABASE_PATH = Path('attendance_system.db')

def verify_password(stored_password: str, provided_password: str) -> bool:
    """
    Direct password comparison - simple equality check
    
    Args:
        stored_password: The stored password
        provided_password: The password to verify
    
    Returns:
        True if password matches, False otherwise
    """
    return stored_password == provided_password

def password_strength(password: str) -> tuple:
    """
    Simplified password check - accepts all passwords
    
    Args:
        password: Password to check
    
    Returns:
        tuple: Always returns (5, "Password accepted")
    """
    return 5, "Password accepted"

def ensure_user_accounts_schema():
    """Ensure the user_accounts table has all required columns"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # First check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_accounts'")
        if not cursor.fetchone():
            # Create the table with all required columns
            cursor.execute("""
            CREATE TABLE user_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL,
                last_login TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            logger.info("Created user_accounts table")
            conn.commit()
            return True
            
        # Check if last_login column exists
        cursor.execute("PRAGMA table_info(user_accounts)")
        columns = [col[1].lower() for col in cursor.fetchall()]
        
        if 'last_login' not in columns:
            # Add the missing column
            cursor.execute("ALTER TABLE user_accounts ADD COLUMN last_login TIMESTAMP")
            logger.info("Added missing last_login column to user_accounts table")
            conn.commit()
            
        return True
    except Exception as e:
        logger.error(f"Error ensuring user_accounts schema: {e}")
        return False
    finally:
        conn.close()

def secure_verify_credentials(username: str, password: str) -> tuple:
    """
    Verify user credentials directly from user_accounts table
    
    Args:
        username: Username to verify
        password: Password to verify
    
    Returns:
        tuple: (success, role)
    """
    # First ensure the schema is correct
    ensure_user_accounts_schema()
    
    # Add debugging for troubleshooting
    logger.info(f"Attempting to verify credentials for username: {username}")
    
    # Special case for admin account (fallback)
    if username == "admin" and (password == "admin" or password == "123"):
        logger.info("Admin login with hardcoded credentials successful")
        return True, "admin"
    
    # Special case for professor account (fallback)
    if username == "professor" and (password == "professor" or password == "123"):
        logger.info("Professor login with hardcoded credentials successful")
        return True, "professor"
    
    # Special case for student account (fallback)
    if username == "student" and (password == "student" or password == "123"):
        logger.info("Student login with hardcoded credentials successful")
        return True, "student"
    
    # Check the user_accounts table directly
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # DEBUG: Directly check if user exists at all
        cursor.execute("SELECT username, password FROM user_accounts WHERE username = ?", (username,))
        user_data = cursor.fetchone()
        
        if user_data:
            stored_username, stored_password = user_data
            logger.info(f"Found user in database. Stored password length: {len(stored_password) if stored_password else 'None'}")
            
            # Compare passwords directly (plain text)
            if stored_password == password:
                # Get user role
                cursor.execute("SELECT id, role FROM user_accounts WHERE username = ?", (username,))
                user = cursor.fetchone()
                if user:
                    user_id, role = user
                    
                    # Check if last_login column exists before updating
                    try:
                        cursor.execute(
                            "UPDATE user_accounts SET last_login = ? WHERE id = ?",
                            (datetime.now().isoformat(), user_id)
                        )
                        conn.commit()
                    except sqlite3.OperationalError as e:
                        logger.warning(f"Could not update last_login: {e}")
                        # Continue anyway since login can still succeed
                    
                    logger.info(f"Successful login for user: {username}, role: {role}")
                    return True, role
        
        # Original query as fallback
        cursor.execute(
            "SELECT id, role FROM user_accounts WHERE username = ? AND password = ?",
            (username, password)
        )
        user = cursor.fetchone()
        
        if not user:
            logger.warning(f"User not found or password mismatch for: {username}")
            return False, ""
        
        user_id, role = user
        logger.info(f"User found in database with fallback query: {username}, role: {role}")
        
        # Try updating last_login with error handling
        try:
            cursor.execute(
                "UPDATE user_accounts SET last_login = ? WHERE id = ?",
                (datetime.now().isoformat(), user_id)
            )
            conn.commit()
        except sqlite3.OperationalError:
            # Ignore error if column doesn't exist
            pass
        
        return True, role
            
    except Exception as e:
        logger.error(f"Error verifying credentials: {e}")
        return False, ""
    finally:
        conn.close()
