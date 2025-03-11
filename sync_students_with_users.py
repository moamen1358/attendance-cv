import sqlite3
import hashlib
import random
import string

# Constants
DATABASE_PATH = 'attendance_system.db'

def get_db_connection():
    """Get a connection to the SQLite database"""
    return sqlite3.connect(DATABASE_PATH)

def generate_default_password(name, section):
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
    password = f"{name}_sec{section_num}"
    return password

def sync_students_to_users():
    """Ensure every student has a corresponding user account"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("Checking for student_profiles without user accounts...")
    
    # Get all student_profiles
    cursor.execute("SELECT name, section FROM student_profiles ORDER BY name")
    students = cursor.fetchall()
    
    # Track statistics
    total_students = len(students)
    created_users = 0
    already_had_users = 0
    
    # Process each student
    for student_name, section in students:
        # Check if user already exists
        cursor.execute("SELECT username FROM user_accounts WHERE username = ?", (student_name,))
        user = cursor.fetchone()
        
        if not user:
            # Generate default password based on name and section
            default_password = generate_default_password(student_name, section)
            
            # Hash the password
            hashed_password = hashlib.md5(default_password.encode()).hexdigest()
            
            # Create user for this student
            cursor.execute("""
                INSERT INTO user_accounts (username, password, role) 
                VALUES (?, ?, 'student')
            """, (student_name, hashed_password))
            
            print(f"Created user for student: {student_name} (Section: {section or 'Unassigned'})")
            print(f"  - Default password: {default_password}")
            created_users += 1
        else:
            # Update existing user_accounts to use the new password format
            default_password = generate_default_password(student_name, section)
            hashed_password = hashlib.md5(default_password.encode()).hexdigest()
            
            # Update password
            cursor.execute("""
                UPDATE user_accounts SET password = ? WHERE username = ?
            """, (hashed_password, student_name))
            
            print(f"Updated password for: {student_name} (Section: {section or 'Unassigned'})")
            print(f"  - New password: {default_password}")
            already_had_users += 1
    
    # Save changes
    conn.commit()
    
    # Print summary
    print("\nSync completed:")
    print(f"Total students: {total_students}")
    print(f"Users created: {created_users}")
    print(f"Users updated: {already_had_users}")
    
    # Show all student user_accounts for verification
    print("\nList of all student users:")
    cursor.execute("""
        SELECT u.username, s.section
        FROM user_accounts u
        JOIN student_profiles s ON u.username = s.name
        WHERE u.role = 'student'
        ORDER BY s.section, u.username
    """)
    
    student_users = cursor.fetchall()
    
    print(f"{'Username':<20} {'Section':<15} {'Password':<15}")
    print("-" * 50)
    
    current_section = None
    for username, section in student_users:
        if section != current_section:
            if current_section is not None:
                print()
            current_section = section
            print(f"--- {section or 'Unassigned'} ---")
        
        password = generate_default_password(username, section)
        print(f"{username:<20} {section or 'Unassigned':<15} {password:<15}")
    
    conn.close()

if __name__ == "__main__":
    sync_students_to_users()
    print("\nAll student_profiles now have user accounts with name_secX passwords!")
