import sqlite3
import hashlib

# Constants
DATABASE_PATH = 'attendance_system.db'

def generate_section_password(username, section):
    """Generate a password based on name and section"""
    # Format: {name}_{section_abbreviated}
    # Example: "moamen" in "Section 1" → "moamen_sec1"
    
    # Get section number (default to "0" if not available)
    section_num = "1"  # Default to Section 1 for moamen
    if section and "Section" in section:
        try:
            section_num = section.split()[-1]  # Extract number from "Section X"
        except:
            pass
    
    # Create password
    password = f"{username}_sec{section_num}"
    return password

def fix_moamen_user():
    """Fix the password for user 'moamen' by setting it to name_secX format"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    username = "moamen"
    
    # Get section for user if exists
    cursor.execute("SELECT section FROM student_profiles WHERE name = ?", (username,))
    section_result = cursor.fetchone()
    section = section_result[0] if section_result and section_result[0] else "Section 1"
    
    # Generate the new password format
    password = generate_section_password(username, section)
    
    # Check if user exists
    cursor.execute("SELECT username, password, role FROM user_accounts WHERE username = ?", (username,))
    user_data = cursor.fetchone()
    
    if user_data:
        print(f"User '{username}' found in database")
        
        # Hash the new password
        hashed_password = hashlib.md5(password.encode()).hexdigest()
        
        # Update the password
        print(f"Updating password for '{username}' to new format")
        cursor.execute(
            "UPDATE user_accounts SET password = ? WHERE username = ?",
            (hashed_password, username)
        )
        conn.commit()
        print(f"Password updated successfully")
    else:
        print(f"User '{username}' not found, creating user...")
        
        # Hash the password
        hashed_password = hashlib.md5(password.encode()).hexdigest()
        
        # Create user with hashed password
        cursor.execute(
            "INSERT INTO user_accounts (username, password, role) VALUES (?, ?, ?)",
            (username, hashed_password, "student")
        )
        
        # Add to student_profiles table
        cursor.execute("SELECT name FROM student_profiles WHERE name = ?", (username,))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO student_profiles (name, section) VALUES (?, ?)", (username, section))
            print(f"Added '{username}' to student_profiles table with section '{section}'")
        
        conn.commit()
        print(f"User '{username}' created with role 'student'")
    
    # Show all user_accounts for verification
    cursor.execute("SELECT username, role FROM user_accounts")
    print("\nUsers in database:")
    for user, role in cursor.fetchall():
        print(f"  {user} ({role})")
    
    conn.close()
    print("\nYou can now log in with:")
    print(f"Username: {username}")
    print(f"Password: {password}")

if __name__ == "__main__":
    fix_moamen_user()
