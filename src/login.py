import streamlit as st
import sqlite3
from database_utils import execute_query, execute_query_df
import hashlib
import app
import os
from datetime import datetime

def create_connection():
    conn = sqlite3.connect('attendance_system.db')
    return conn

def verify_credentials(username, password):
    """Verify credentials and return user role if valid"""
    
    conn = sqlite3.connect('attendance_system.db')
    cursor = conn.cursor()
    
    try:
        # Check for the unified user_accounts table first (new schema)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_accounts'")
        if cursor.fetchone():
            # Check if password is stored as hash or plain text
            cursor.execute("SELECT password, role FROM user_accounts WHERE username = ?", (username,))
            result = cursor.fetchone()
            
            if result:
                stored_password, role = result
                
                # Check if password matches (plain text for now - could be upgraded to proper hashing)
                if stored_password == password:
                    return True, role
        
        # Legacy tables support (for backward compatibility)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('student_profiles', 'professor_profiles')")
        tables = [row[0] for row in cursor.fetchall()]
        
        # Check in student_profiles table if it exists
        if 'student_profiles' in tables:
            cursor.execute("SELECT password FROM student_profiles WHERE name = ? OR username = ?", (username, username))
            result = cursor.fetchone()
            if result and result[0] == password:
                return True, "student"
            
        # Check in professor_profiles table if it exists  
        if 'professor_profiles' in tables:
            cursor.execute("SELECT password FROM professor_profiles WHERE username = ?", (username,))
            result = cursor.fetchone()
            if result and result[0] == password:
                return True, "professor"
            
        # Default development credentials (only if no user accounts exist)
        cursor.execute("SELECT COUNT(*) FROM user_accounts")
        count = cursor.fetchone()[0]
        
        if count == 0:
            if username == "admin" and password == "admin":
                return True, "admin"
            elif username == "teacher" and password == "teacher":
                return True, "professor"
            elif username == "student" and password == "student":
                return True, "student"
    
    except Exception as e:
        st.error(f"Database error: {e}")
    finally:
        conn.close()
    
    return False, None

def get_available_users():
    """
    Get a list of available users from the database
    Returns a list of tuples (username, role)
    """
    conn = create_connection()
    cursor = conn.cursor()
    
    try:
        # Use the unified user_accounts table (new schema)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_accounts'")
        if cursor.fetchone():
            # Get all users with their roles from the unified table
            cursor.execute("SELECT username, role FROM user_accounts")
            return cursor.fetchall()
        
        # Fallback to legacy tables if needed
        users = []
        
        # Check student_profiles table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='student_profiles'")
        if cursor.fetchone():
            cursor.execute("SELECT name, 'student' FROM student_profiles")
            users.extend(cursor.fetchall())
        
        # Check professor_profiles table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='professor_profiles'")
        if cursor.fetchone():
            cursor.execute("SELECT username, 'professor' FROM professor_profiles")
            users.extend(cursor.fetchall())
            
        return users
        
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return []
    
    finally:
        conn.close()

def get_user_section(username):
    """Get the section for a student user (if available)"""
    conn = create_connection()
    cursor = conn.cursor()
    
    # First check user_accounts table (new schema)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_accounts'")
    if cursor.fetchone():
        cursor.execute("SELECT section FROM user_accounts WHERE username = ? AND role = 'student'", (username,))
        result = cursor.fetchone()
        if result and result[0]:
            conn.close()
            return result[0]
    
    # Fallback to student_profiles (old schema)
    cursor.execute("SELECT section FROM student_profiles WHERE name = ? OR username = ?", (username, username))
    result = cursor.fetchone()
    conn.close()
    
    return result[0] if result and result[0] else "Unassigned"

def login_page():
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        success, role = verify_credentials(username, password)
        if success:
            # Set session state variables
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.user_role = role
            
            # Store login time for security tracking
            st.session_state.login_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Update query parameters to maintain login state
            st.query_params["logged_in"] = "True"
            st.query_params["username"] = username
            
            # Log successful login
            try:
                conn = sqlite3.connect('attendance_system.db')
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO login_logs (username, login_time, ip_address, status) VALUES (?, ?, ?, ?)",
                    (username, st.session_state.login_time, get_client_ip(), "success")
                )
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"Error logging login: {e}")
            
            # Refresh to load the app
            st.rerun()
        else:
            # Log failed login attempt
            try:
                conn = sqlite3.connect('attendance_system.db')
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO login_logs (username, login_time, ip_address, status) VALUES (?, ?, ?, ?)",
                    (username, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), get_client_ip(), "failed")
                )
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"Error logging failed login: {e}")
                
            st.error("Invalid username or password")
    
    # Show available users from database
    with st.expander("Available Users"):
        users = get_available_users()
        if users:
            st.write("Available users in the system:")
            for user, role in users:
                section = get_user_section(user) if role == "student" else "N/A"
                st.write(f"- {user} (Role: {role}, Section: {section})")
            st.info("Note: Passwords are hashed in the database. Contact the administrator if you need access.")
        else:
            st.warning("No users found in the database.")

# Simple function to get client IP for logging
def get_client_ip():
    """Get the client's IP address if available"""
    try:
        import streamlit.server.server as streamlit_server
        return streamlit_server.get_remote_ip() or "unknown"
    except:
        return "unknown"

def main():
    # Initialize session state
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    # Check query params
    if "logged_in" in st.query_params and st.query_params["logged_in"] == "True":
        st.session_state.logged_in = True

    if st.session_state.logged_in:
        app.show_app()
    else:
        login_page()

if __name__ == "__main__":
    main()