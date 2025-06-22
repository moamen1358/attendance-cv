"""
Database Sync Module

This module handles synchronization between different database tables
to ensure data consistency across the application.
"""
import sqlite3
import os

def sync_user_tables():
    """
    Synchronize user data between user_accounts and profile tables.
    
    Returns:
        int: Number of changes made during synchronization
    """
    conn = sqlite3.connect('attendance_system.db')
    cursor = conn.cursor()
    changes = 0
    
    try:
        # 1. Ensure all students in student_profiles have corresponding user_accounts entries
        cursor.execute("""
        INSERT OR IGNORE INTO user_accounts (username, password, role)
        SELECT username, password, 'student'
        FROM student_profiles
        WHERE username IS NOT NULL
        """)
        changes += cursor.rowcount
        
        # 2. Ensure all professors in professor_profiles have corresponding user_accounts entries
        cursor.execute("""
        INSERT OR IGNORE INTO user_accounts (username, password, role)
        SELECT username, password, 'professor'
        FROM professor_profiles
        WHERE username IS NOT NULL
        """)
        changes += cursor.rowcount
        
        # 3. Ensure students in user_accounts have student_profiles entries
        cursor.execute("""
        INSERT OR IGNORE INTO student_profiles_enhanced (username, name, password)
        SELECT ua.username, ua.username, ua.password
        FROM user_accounts_enhanced ua
        WHERE ua.role = 'student' AND ua.username NOT IN (SELECT username FROM student_profiles_enhanced)
        """)
        changes += cursor.rowcount
        
        # 4. Ensure professors in user_accounts have professor_profiles entries
        cursor.execute("""
        INSERT OR IGNORE INTO professor_profiles (username, name, password)
        SELECT ua.username, ua.username, ua.password
        FROM user_accounts_enhanced ua
        WHERE ua.role = 'professor' AND ua.username NOT IN (SELECT username FROM professor_profiles)
        """)
        changes += cursor.rowcount
        
        # Commit all changes
        conn.commit()
        
    except Exception as e:
        print(f"Error syncing user tables: {e}")
        conn.rollback()
    finally:
        conn.close()
    
    return changes

def register_user(username, password, role, profile_data=None):
    """
    Register a new user in all relevant tables.
    
    Args:
        username (str): Username for the new user
        password (str): Password for the new user
        role (str): User role (admin, professor, student)
        profile_data (dict, optional): Additional profile data
    
    Returns:
        bool: True if registration was successful, False otherwise
    """
    conn = sqlite3.connect('attendance_system.db')
    cursor = conn.cursor()
    success = False
    
    try:
        # 1. Add to user_accounts table
        cursor.execute("""
        INSERT OR IGNORE INTO user_accounts (username, password, role)
        VALUES (?, ?, ?)
        """, (username, password, role))
        
        # 2. Add to specific profile table based on role
        if role.lower() == 'student':
            # Extract profile data or use defaults
            name = profile_data.get('name', username) if profile_data else username
            student_id = profile_data.get('student_id', username) if profile_data else username
            section = profile_data.get('section', 'Default') if profile_data else 'Default'
            
            cursor.execute("""
            INSERT OR IGNORE INTO student_profiles (username, name, student_id, password, section)
            VALUES (?, ?, ?, ?, ?)
            """, (username, name, student_id, password, section))
            
        elif role.lower() == 'professor':
            # Extract profile data or use defaults
            name = profile_data.get('name', username) if profile_data else username
            department = profile_data.get('department', 'General') if profile_data else 'General'
            
            cursor.execute("""
            INSERT OR IGNORE INTO professor_profiles (username, name, password)
            VALUES (?, ?, ?)
            """, (username, name, password))
        
        # Commit changes
        conn.commit()
        success = True
        
    except Exception as e:
        print(f"Error registering user: {e}")
        conn.rollback()
    finally:
        conn.close()
    
    return success
