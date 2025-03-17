# ...existing code...

def show_admin_dashboard():
    """
    Display the admin dashboard with key management functions
    """
    # Debug statement to confirm we reached the admin dashboard
    print("Admin dashboard function called")
    
    # No need to check if user is admin - this is handled in app.py
    
    # Ensure consistent padding
    ensure_consistent_padding()
    
    st.title("Admin Dashboard")
    
    # Add Quick Access Panel at the top
    st.subheader("Quick Access")
    quick_col1, quick_col2, quick_col3, quick_col4 = st.columns(4)
    
    with quick_col1:
        if st.button("📝 Create User", use_container_width=True):
            # Change to registration page instead of showing a form here
            st.session_state.current_page = "Registration"
            st.rerun()
    
    with quick_col2:
        if st.button("🏫 Manage Classes", use_container_width=True):
            # Set session state to change to Subject Management page
            st.session_state.current_page = "Subject Management"
            st.rerun()
            
    with quick_col3:
        if st.button("👁️ Recognition", use_container_width=True):
            st.session_state.current_page = "Real-Time Recognition"
            st.rerun()
    
    with quick_col4:
        if st.button("🔍 Database Explorer", use_container_width=True):
            st.session_state.current_page = "Database Explorer"
            st.rerun()
    
    # Rest of the original admin dashboard code
    # ...existing code...
