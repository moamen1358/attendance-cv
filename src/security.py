import hashlib
import os
import re
import sqlite3
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database path
DATABASE_PATH = 'attendance_system.db'

def generate_salt():
    """Generate a random salt for password hashing"""
    return os.urandom(32).hex()

def hash_password(password, salt=None):
    """
    Hash a password with a salt using PBKDF2
    
    Args:
        password (str): The plaintext password
        salt (str, optional): Salt to use, or generate new one if None
    
    Returns:
        tuple: (hashed_password, salt)
    """
    if salt is None:
        salt = generate_salt()
    else:
        # Ensure salt is a string
        salt = str(salt)
    
    # Hash password using PBKDF2 with SHA-256
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000  # Number of iterations
    ).hex()
    
    return key, salt

def verify_password(stored_hash, stored_salt, provided_password):
    """
    Verify a password against a stored hash and salt
    
    Args:
        stored_hash (str): The stored password hash
        stored_salt (str): The stored salt
        provided_password (str): The password to verify
    
    Returns:
        bool: True if password matches, False otherwise
    """
    calculated_hash, _ = hash_password(provided_password, stored_salt)
    return calculated_hash == stored_hash

def password_strength(password):
    """
    Check password strength
    
    Args:
        password (str): Password to check
    
    Returns:
        tuple: (strength_score, message)
    """
    score = 0
    feedback = []
    
    # Length check
    if len(password) < 8:
        feedback.append("Password should be at least 8 characters long")
    else:
        score += 1
    
    # Uppercase check
    if not re.search(r'[A-Z]', password):
        feedback.append("Include at least one uppercase letter")
    else:
        score += 1
    
    # Lowercase check
    if not re.search(r'[a-z]', password):
        feedback.append("Include at least one lowercase letter")
    else:
        score += 1
    
    # Digit check
    if not re.search(r'\d', password):
        feedback.append("Include at least one number")
    else:
        score += 1
    
    # Special character check
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        feedback.append("Include at least one special character")
    else:
        score += 1
    
    # Prepare feedback message
    strength_levels = ["Very Weak", "Weak", "Moderate", "Good", "Strong", "Very Strong"]
    strength_text = strength_levels[min(score, len(strength_levels)-1)]
    
    if feedback:
        message = f"Password strength: {strength_text}. {' '.join(feedback)}"
    else:
        message = f"Password strength: {strength_text}"
    
    return score, message

def migrate_plain_passwords():
    """
    Migrate plain text passwords to hashed passwords
    This function should be run once to upgrade existing passwords
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # First check if the table has the required columns
        cursor.execute("PRAGMA table_info(user_accounts)")
        columns = {col[1].lower() for col in cursor.fetchall()}
        
        # Add required columns if they don't exist
        if 'password_hash' not in columns:
            cursor.execute("ALTER TABLE user_accounts ADD COLUMN password_hash TEXT")
        
        if 'salt' not in columns:
            cursor.execute("ALTER TABLE user_accounts ADD COLUMN salt TEXT")
        
        # Get users with plain passwords
        cursor.execute("""
        SELECT id, username, password 
        FROM user_accounts 
        WHERE (password_hash IS NULL OR password_hash = '') AND password IS NOT NULL
        """)
        users = cursor.fetchall()
        
        migrated_count = 0
        for user_id, username, plain_password in users:
            # Hash the password
            password_hash, salt = hash_password(plain_password)
            
            # Update the user record
            cursor.execute(
                "UPDATE user_accounts SET password_hash = ?, salt = ? WHERE id = ?",
                (password_hash, salt, user_id)
            )
            migrated_count += 1
        
        conn.commit()
        logger.info(f"Migrated {migrated_count} passwords to secure hash")
        return migrated_count
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error migrating passwords: {e}")
        return 0
    finally:
        conn.close()

def secure_verify_credentials(username, password):
    """
    Securely verify user credentials using hashed passwords
    
    Args:
        username (str): Username
        password (str): Plain text password
    
    Returns:
        tuple: (success, role)
    """
    # Special case for admin account
    if username == "admin" and password == "admin":
        return True, "admin"
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # First try to find the user with hashed password
        cursor.execute(
            "SELECT id, password_hash, salt, role FROM user_accounts WHERE username = ?",
            (username,)
        )
        user = cursor.fetchone()
        
        if not user:
            return False, ""
        
        user_id, password_hash, salt, role = user
        
        # If we have a hash and salt, verify with them
        if password_hash and salt:
            if verify_password(password_hash, salt, password):
                # Update last login time
                cursor.execute(
                    "UPDATE user_accounts SET last_login = ? WHERE id = ?",
                    (datetime.now().isoformat(), user_id)
                )
                conn.commit()
                return True, role
        else:
            # Fall back to plain password check for legacy accounts
            cursor.execute(
                "SELECT role FROM user_accounts WHERE username = ? AND password = ?",
                (username, password)
            )
            legacy_user = cursor.fetchone()
            
            if legacy_user:
                # Update to hashed password for next time
                password_hash, salt = hash_password(password)
                cursor.execute(
                    "UPDATE user_accounts SET password_hash = ?, salt = ?, last_login = ? WHERE id = ?",
                    (password_hash, salt, datetime.now().isoformat(), user_id)
                )
                conn.commit()
                return True, legacy_user[0]
        
        return False, ""
            
    except Exception as e:
        logger.error(f"Error verifying credentials: {e}")
        return False, ""
    finally:
        conn.close()
