import sqlite3
import streamlit as st
from datetime import datetime

def fix_admin_users():
    """Fix any admin users with incorrect roles in the database"""
    conn = sqlite3.connect('attendance_system.db')
    cursor = conn.cursor()
    
    try:
        # Find users with "admin" in their username but without admin role
        cursor.execute("""
        SELECT username, role FROM user_accounts 
        WHERE (username LIKE '%admin%' OR username = 'admin') 
        AND LOWER(role) != 'admin'
        """)
        
        incorrect_users = cursor.fetchall()
        fixed_count = 0
        
        # Fix each user
        for username, current_role in incorrect_users:
            cursor.execute(
                "UPDATE user_accounts SET role = 'admin' WHERE username = ?",
                (username,)
            )
            
            # Remove any student profiles for this admin user
            cursor.execute("DELETE FROM student_profiles WHERE name = ? OR username = ?", (username, username))
            
            # Log the fix
            cursor.execute(
                "INSERT INTO login_logs (username, login_time, status) VALUES (?, ?, ?)",
                ('system', datetime.now().strftime("%Y-%m-%d %H:%M:%S"), f"admin_role_fixed_{username}")
            )
            
            fixed_count += 1
        
        conn.commit()
        return fixed_count, incorrect_users
    
    except Exception as e:
        conn.rollback()
        return -1, str(e)
    
    finally:
        conn.close()

if __name__ == "__main__":
    st.set_page_config(page_title="Fix Admin Users", page_icon="🛠️")
    st.title("Fix Admin User Roles")
    
    if st.button("Find and Fix Admin Users", use_container_width=True, type="primary"):
        fixed_count, details = fix_admin_users()
        
        if fixed_count >= 0:
            if fixed_count > 0:
                st.success(f"Fixed {fixed_count} admin users with incorrect roles:")
                for username, old_role in details:
                    st.write(f"- {username}: {old_role} → admin")
            else:
                st.success("All admin users already have correct roles!")
        else:
            st.error(f"Error fixing admin roles: {details}")
    
    # Add a manual fix option
    st.subheader("Manual Fix")
    
    with st.form("manual_fix"):
        username = st.text_input("Username to fix")
        
        if st.form_submit_button("Set as Admin"):
            conn = sqlite3.connect('attendance_system.db')
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE user_accounts SET role = 'admin' WHERE username = ?",
                    (username,)
                )
                
                if cursor.rowcount > 0:
                    st.success(f"User '{username}' updated to admin role")
                else:
                    st.warning(f"User '{username}' not found")
                    
                conn.commit()
            except Exception as e:
                st.error(f"Error: {e}")
            finally:
                conn.close()
