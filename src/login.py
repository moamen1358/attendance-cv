import streamlit as st
import sqlite3
import app

def create_connection():
    conn = sqlite3.connect('attendance_system.db')
    return conn

def check_credentials(username, password):
    """Check credentials and return user info including role"""
    conn = create_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT username, role 
        FROM users 
        WHERE username = ? AND password = ?
    """, (username, password))
    
    result = cursor.fetchone()
    conn.close()
    return result

def show_login():
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user_info = check_credentials(username, password)
        if user_info:
            username, role = user_info
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.user_role = role  # Store user role in session state
            st.query_params["logged_in"] = "True"
            st.query_params["username"] = username
            st.query_params["role"] = role
            st.rerun()
        else:
            st.error("Invalid username or password")

def main():
    # Initialize session state
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user_role' not in st.session_state:
        st.session_state.user_role = None

    # Check query params
    if "logged_in" in st.query_params and st.query_params["logged_in"] == "True":
        st.session_state.logged_in = True
        if "username" in st.query_params:
            st.session_state.username = st.query_params["username"]
        if "role" in st.query_params:
            st.session_state.user_role = st.query_params["role"]

    if st.session_state.logged_in:
        app.show_app()
    else:
        show_login()

if __name__ == "__main__":
    main()