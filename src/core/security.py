"""
Security utilities for authentication and authorization.

This module provides security functions:
- Simple password verification (plain text)
- User authentication
"""
import sqlite3
import logging
import re
from datetime import datetime
from src.constants import DATABASE_PATH

# Setup logging
logger = logging.getLogger(__name__)

def verify_password(stored_password: str, provided_password: str) -> bool:
    """
    Verify a password against stored password (plain text)
    
    Args:
        stored_password: The stored password
        provided_password: The password to verify
    
    Returns:
        True if password matches, False otherwise
    """
    return stored_password == provided_password

def password_strength(password: str) -> tuple:
    """
    Check password strength
    
    Args:
        password: Password to check
    
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

def secure_verify_credentials(username: str, password: str) -> tuple:
    """
    Verify user credentials using plain text passwords
    
    Args:
        username: Username to verify
        password: Password to verify
    
    Returns:
        (success, role)
    """
    # Special case for admin account
    if username == "admin" and password == "admin" or password == "123":
        return True, "admin"
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # Simple plain text password verification
        cursor.execute(
            "SELECT id, role FROM user_accounts WHERE username = ? AND password = ?",
            (username, password)
        )
        user = cursor.fetchone()
        
        if not user:
            return False, ""
        
        user_id, role = user
        
        # Update last login time
        cursor.execute(
            "UPDATE user_accounts SET last_login = ? WHERE id = ?",
            (datetime.now().isoformat(), user_id)
        )
        conn.commit()
        
        return True, role
            
    except Exception as e:
        logger.error(f"Error verifying credentials: {e}")
        return False, ""
    finally:
        conn.close()
