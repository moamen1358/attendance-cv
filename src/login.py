import streamlit as st
import sqlite3
import hashlib
import app

def create_connection():
    conn = sqlite3.connect('attendance_system.db')
    return conn

def check_credentials(username, password):
    conn = create_connection()
    cursor = conn.cursor()
    
    # Hash the password using MD5 to match stored hash
    hashed_password = hashlib.md5(password.encode()).hexdigest()
    
    # Get user with role
    cursor.execute("SELECT username, role FROM user_accounts WHERE username = ? AND password = ?", 
                  (username, hashed_password))
    result = cursor.fetchone()
    conn.close()
    
    return result

def get_available_users():
    """
    Get a list of available users from the database
    Returns a list of tuples (username, role)
    """
    conn = create_connection()
    cursor = conn.cursor()
    
    try:
        # Check if we're using the old table name or the new one
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND (name='users' OR name='user_accounts')")
        result = cursor.fetchone()
        
        if result:
            table_name = result[0]
            # Update to fetch both username and role
            cursor.execute(f"SELECT username, role FROM {table_name}")
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
    
    cursor.execute("SELECT section FROM student_profiles WHERE name = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    
    return result[0] if result and result[0] else "Unassigned"

def show_login():
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        result = check_credentials(username, password)
        if result:
            username, role = result
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.user_role = role
            
            # If student, get section
            if role == "student":
                section = get_user_section(username)
                st.session_state.section = section
            
            # Store all login info in query params
            st.query_params["logged_in"] = "True"
            st.query_params["username"] = username
            st.query_params["role"] = role  # Add role to query params
            
            st.rerun()
        else:
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
        show_login()

if __name__ == "__main__":
    main()