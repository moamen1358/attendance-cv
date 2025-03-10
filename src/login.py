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
    cursor.execute("SELECT username, role FROM users WHERE username = ? AND password = ?", 
                  (username, hashed_password))
    result = cursor.fetchone()
    conn.close()
    
    return result

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
            
            # Store all login info in query params
            st.query_params["logged_in"] = "True"
            st.query_params["username"] = username
            st.query_params["role"] = role  # Add role to query params
            
            st.rerun()
        else:
            st.error("Invalid username or password")
    
    # Show test user information for development
    with st.expander("Test Users"):
        st.info("Use these test accounts:\n"
                "- Student: username='student', password='student123'\n"
                "- Professor: username='professor', password='professor123'\n"
                "- Admin: username='admin', password='admin123'")

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