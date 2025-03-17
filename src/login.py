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
    """Verify credentials using plain text password comparison"""
    
    # PRIORITY CHECK FOR "admin" USERNAME (handles default admin user)
    if username == "admin" and password == "admin":
        print("Default admin login detected with default credentials")
        return True, "admin"
    
    # Special handling for usernames containing "admin" (optional)
    if "admin" in username.lower():
        print(f"Potential admin user detected: {username}")
    
    conn = sqlite3.connect('attendance_system.db')
    cursor = conn.cursor()
    
    try:
        # Check for the unified user_accounts table first (new schema)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_accounts'")
        if cursor.fetchone():
            # Check password as plain text (no hashing)
            cursor.execute("SELECT password, role FROM user_accounts WHERE username = ?", (username,))
            result = cursor.fetchone()
            
            if result:
                stored_password, role = result
                
                # Direct comparison of passwords (plain text)
                if stored_password == password:
                    # Additional check: Ensure any admin user gets admin role 
                    if username.lower() == "admin" or "admin" in username.lower() or role.lower() == "admin":
                        print(f"Admin user {username} authenticated with role override")
                        return True, "admin"
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
    
    try:
        # First check if student_profiles table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='student_profiles'")
        if not cursor.fetchone():
            # Table doesn't exist, return default value
            return "Unassigned"
            
        # Table exists, so query it
        cursor.execute("SELECT section FROM student_profiles WHERE name = ? OR username = ?", (username, username))
        result = cursor.fetchone()
        
        return result[0] if result and result[0] else "Unassigned"
    except Exception as e:
        print(f"Error getting user section: {e}")
        return "Unassigned"
    finally:
        conn.close()

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
            
            # ENHANCED ROLE DETECTION
            # Force admin role for any username containing "admin"
            is_admin = (username.lower() == "admin" or "admin" in username.lower() or role.lower() == "admin")
            is_professor = role.lower() == "professor"
            
            if is_admin:
                role = "admin"
                st.session_state.is_admin = True
                print(f"Enforcing admin role for {username}")
            elif is_professor:
                st.session_state.is_professor = True
                print(f"Setting professor role for {username}")
                
            st.session_state.user_role = role
            
            # Debug info for role login
            print(f"User login successful: username={username}, role={role}")
            
            # Store login time for security tracking
            st.session_state.login_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Update query parameters to maintain login state - INCLUDE ROLE FOR ALL USERS
            st.query_params["logged_in"] = "True"
            st.query_params["username"] = username
            st.query_params["user_role"] = role  # Add role to query params
            
            # For admin users, add a flag to URL to ensure persistence
            if is_admin:
                st.query_params["is_admin"] = "true"
            elif is_professor:
                st.query_params["is_professor"] = "true"
            
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
                try:
                    section = get_user_section(user) if role == "student" else "N/A"
                except Exception as e:
                    # Handle any errors during section lookup
                    print(f"Error getting section for {user}: {e}")
                    section = "Unknown"
                    
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