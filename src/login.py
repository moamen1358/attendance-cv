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
        # Check for tables that might contain user credentials
        execute_query("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('user_accounts', 'student_profiles', 'professor_profiles')")
        tables = [row[0] for row in cursor.fetchall()]
        
        # Check in user_accounts table if it exists
        if 'user_accounts' in tables:
            execute_query("PRAGMA table_info(user_accounts)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'username' in columns and ('password' in columns or 'hashed_password' in columns):
                pwd_column = 'hashed_password' if 'hashed_password' in columns else 'password'
                role_column = 'role' if 'role' in columns else None
                
                query = f"SELECT username, {role_column or '\"student\" as role'}, {pwd_column} FROM user_accounts WHERE username = ?"
                execute_query(query, (username,))
                user = cursor.fetchone()
                
                if user:
                    stored_hash = user[2]
                    
                    # If using bcrypt hashed passwords
                    if stored_hash and (stored_hash.startswith('$2b$') or stored_hash.startswith('$2a$')):
                        try:
                            import bcrypt
                            if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
                                return True, user[1]
                        except ImportError:
                            # Bcrypt not available, try direct comparison as fallback
                            if stored_hash == password:
                                return True, user[1]
                    # For plain text passwords (not recommended for production)
                    elif stored_hash == password:
                        return True, user[1]
        
        # Check for student records
        if 'student_profiles' in tables:
            # Check columns
            execute_query("PRAGMA table_info(student_profiles)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'password' in columns:
                # Check if we can query by name or username
                where_clause = ""
                if 'name' in columns and 'username' in columns:
                    where_clause = "WHERE name = ? OR username = ?"
                    params = (username, username)
                elif 'name' in columns:
                    where_clause = "WHERE name = ?"
                    params = (username,)
                elif 'username' in columns:
                    where_clause = "WHERE username = ?"
                    params = (username,)
                
                if where_clause:
                    query = f"SELECT name, password FROM student_profiles {where_clause}"
                    execute_query(query, params)
                    student = cursor.fetchone()
                    
                    if student and student[1] == password:
                        return True, "student"
            
        # Check for professor records
        if 'professor_profiles' in tables:
            # Check columns
            execute_query("PRAGMA table_info(professor_profiles)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'username' in columns and 'password' in columns:
                query = "SELECT username, password FROM professor_profiles WHERE username = ?"
                execute_query(query, (username,))
                professor = cursor.fetchone()
                
                if professor and professor[1] == password:
                    return True, "professor"
        
        # Default credentials for development if no tables or users found
        if len(tables) == 0 or execute_query("SELECT COUNT(*) FROM user_accounts").fetchone()[0] == 0:
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
        # Check if we're using the old table name or the new one
        execute_query("SELECT name FROM sqlite_master WHERE type='table' AND (name='users' OR name='user_accounts')")
        result = cursor.fetchone()
        
        if result:
            table_name = result[0]
            # Update to fetch both username and role
            execute_query(f"SELECT username, role FROM {table_name}")
            user_accounts = cursor.fetchall()  # This will return [(username1, role1), (username2, role2), ...]
        else:
            # If no table exists yet
            user_accounts = []
            
        return user_accounts
    
    except sqlite3.Error as e:
        st.error(f"Database error: {e}")
        return []
    
    finally:
        conn.close()

def get_user_section(username):
    """Get the section for a student user (if available)"""
    conn = create_connection()
    cursor = conn.cursor()
    
    execute_query("SELECT section FROM student_profiles WHERE name = ?", (username,))
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