import sqlite3
import hashlib

# Constants
DATABASE_PATH = 'attendance_system.db'

def generate_section_password(username, section):
    """Generate a password based on name and section"""
    # Format: {name}_{section_abbreviated}
    # Example: "moamen" in "Section 1" → "moamen_sec1"
    
    # Get section number (default to "0" if not available)
    section_num = "0"
    if section and "Section" in section:
        try:
            section_num = section.split()[-1]  # Extract number from "Section X"
        except:
            pass
    
    # Create password
    password = f"{username}_sec{section_num}"
    return password

def update_all_passwords():
    """Update all student passwords to follow the name_secX format"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Get all student_profiles with their sections
    cursor.execute("""
        SELECT s.name, s.section
        FROM student_profiles s
        JOIN user_accounts u ON s.name = u.username
        WHERE u.role = 'student'
    """)
    
    students = cursor.fetchall()
    
    updated_count = 0
    for name, section in students:
        # Generate new password
        password = generate_section_password(name, section)
        hashed_password = hashlib.md5(password.encode()).hexdigest()
        
        # Update password in database
        cursor.execute("""
            UPDATE user_accounts 
            SET password = ?
            WHERE username = ?
        """, (hashed_password, name))
        
        updated_count += 1
        print(f"Updated {name} (Section: {section or 'Unassigned'}) → Password: {password}")
    
    # Commit changes
    conn.commit()
    conn.close()
    
    print(f"\nUpdated passwords for {updated_count} student_profiles to name_secX format.")
    print("All student_profiles can now login with: username / username_sec#")

if __name__ == "__main__":
    print("Updating all student passwords to name_secX format...")
    update_all_passwords()
