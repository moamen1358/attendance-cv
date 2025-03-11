import sqlite3
import random

# Constants
DATABASE_PATH = 'attendance_system.db'
SECTIONS = ["Section 1", "Section 2"]  # Available sections

def update_database_schema():
    """Update student_profiles table to include section column"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    print("Checking student_profiles table schema...")
    
    # Check if section column exists
    cursor.execute("PRAGMA table_info(students)")
    columns = [col[1] for col in cursor.fetchall()]
    
    schema_updated = False
    
    if 'section' not in columns:
        print("Adding section column to student_profiles table")
        cursor.execute("ALTER TABLE student_profiles ADD COLUMN section TEXT")
        schema_updated = True
    
    if schema_updated:
        conn.commit()
        print("Schema updated successfully.")
    else:
        print("Schema already contains required columns.")
    
    conn.close()

def assign_sections():
    """Assign sections to all students"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Get all student_profiles
    cursor.execute("SELECT id, name, section FROM student_profiles")
    students = cursor.fetchall()
    
    updated_count = 0
    
    for student in students:
        student_id = student[0]
        name = student[1]
        current_section = student[2]
        
        # Assign section if not present
        if not current_section:
            # Deterministic section assignment to ensure even distribution
            # Uses the sum of character codes in name to determine section
            section_index = sum(ord(c) for c in name) % len(SECTIONS)
            section = SECTIONS[section_index]
            cursor.execute(
                "UPDATE student_profiles SET section = ? WHERE id = ?",
                (section, student_id)
            )
            updated_count += 1
            print(f"Assigned {section} to {name}")
    
    # Special handling for test user_accounts
    test_user_accounts = ['student', 'moamen', 'admin', 'professor']
    for i, user in enumerate(test_users):
        cursor.execute("SELECT section FROM student_profiles WHERE name = ?", (user,))
        result = cursor.fetchone()
        
        if result:
            section = result[0]
            new_section = SECTIONS[i % len(SECTIONS)]
            
            cursor.execute("UPDATE student_profiles SET section = ? WHERE name = ?", 
                         (new_section, user))
            print(f"Updated test user: {user} - Section: {new_section}")
    
    conn.commit()
    conn.close()
    
    print(f"Updated {updated_count} student records.")

def display_student_info():
    """Display all student_profiles with their sections"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name, section FROM student_profiles ORDER BY section, name")
    students = cursor.fetchall()
    
    conn.close()
    
    print("\nStudent Information:")
    print("-" * 40)
    print(f"{'Name':<20} {'Section':<15}")
    print("-" * 40)
    
    current_section = None
    for name, section in students:
        if section != current_section:
            if current_section is not None:
                print()
            current_section = section
        
        print(f"{name:<20} {section:<15}")
    
    print("-" * 40)
    print(f"Total students: {len(students)}")

def main():
    print("Updating student_profiles database with sections...")
    update_database_schema()
    assign_sections()
    display_student_info()
    print("\nDatabase update complete! Application now supports student sections.")

if __name__ == "__main__":
    main()
