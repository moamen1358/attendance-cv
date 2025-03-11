import sqlite3
import os
import shutil
import sys

# Constants
DATABASE_PATH = 'attendance_system.db'
CHROMADB_PATH = './store'

def get_db_connection():
    """Get a connection to the SQLite database"""
    return sqlite3.connect(DATABASE_PATH)

def count_records():
    """Count records in relevant tables"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM user_accounts")
    user_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM facial_recognition_data")
    embedding_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM student_profiles")
    student_count = cursor.fetchone()[0]
    
    conn.close()
    
    return user_count, embedding_count, student_count

def show_warning():
    """Display warning and get confirmation"""
    user_count, embedding_count, student_count = count_records()
    
    print("=" * 80)
    print("WARNING: This script will delete data from your system!")
    print("=" * 80)
    print(f"\nCurrent data in database:")
    print(f"- Users: {user_count}")
    print(f"- Facial embeddings: {embedding_count}")
    print(f"- Students: {student_count}")
    print("\nThis operation will:")
    print("1. Delete ALL user accounts (including admin, professor, student accounts)")
    print("2. Delete ALL facial recognition data")
    print("3. Optionally delete student records")
    print("4. Clear ChromaDB collection (if it exists)")
    
    print("\nYou will need to re-create essential user_accounts after this operation.")
    
    confirmation = input("\nAre you sure you want to proceed? (type 'yes' to confirm): ")
    
    if confirmation.lower() != 'yes':
        print("Operation cancelled.")
        return False
    
    return True

def reset_users():
    """Remove all user accounts"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM user_accounts")
    deleted_count = cursor.connection.total_changes
    
    conn.commit()
    conn.close()
    
    return deleted_count

def reset_facial_features():
    """Remove all facial recognition data"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM facial_recognition_data")
    deleted_count = cursor.connection.total_changes
    
    conn.commit()
    conn.close()
    
    return deleted_count

def reset_chromadb():
    """Remove ChromaDB data"""
    if os.path.exists(CHROMADB_PATH):
        try:
            shutil.rmtree(CHROMADB_PATH)
            print(f"Removed ChromaDB directory: {CHROMADB_PATH}")
            return True
        except Exception as e:
            print(f"Error removing ChromaDB directory: {e}")
            return False
    else:
        print(f"ChromaDB directory not found: {CHROMADB_PATH}")
        return False

def reset_students(should_delete=False):
    """Reset or delete student records"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if should_delete:
        # Delete all student records
        cursor.execute("DELETE FROM student_profiles")
        deleted_count = cursor.connection.total_changes
        print(f"Deleted {deleted_count} student records")
    else:
        # Keep student records but reset section
        cursor.execute("UPDATE student_profiles SET section = NULL")
        updated_count = cursor.connection.total_changes
        print(f"Reset section for {updated_count} student records")
    
    conn.commit()
    conn.close()

def create_essential_users():
    """Re-create essential user_accounts for the system"""
    import hashlib
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create basic test user_accounts
    test_user_accounts = [
        ('admin', 'admin123', 'admin'),
        ('professor', 'professor123', 'professor'),
        ('student', 'student_sec1', 'student')
    ]
    
    for username, password, role in test_users:
        # Hash the password
        hashed_password = hashlib.md5(password.encode()).hexdigest()
        
        # Create user
        cursor.execute(
            "INSERT INTO user_accounts (username, password, role) VALUES (?, ?, ?)",
            (username, hashed_password, role)
        )
        
        # Add to student_profiles table if student role
        if role == 'student':
            cursor.execute("SELECT name FROM student_profiles WHERE name = ?", (username,))
            if not cursor.fetchone():
                cursor.execute("INSERT INTO student_profiles (name, section) VALUES (?, 'Section 1')", 
                              (username,))
    
    conn.commit()
    conn.close()
    
    print("\nCreated essential users:")
    print("- admin (admin123) - Admin role")
    print("- professor (professor123) - Professor role")
    print("- student (student_sec1) - Student role")

def main():
    print(">>> User and Facial Recognition Data Reset Tool <<<\n")
    
    if not show_warning():
        sys.exit(0)
    
    # Handle student records
    delete_students = input("\nAlso delete student records? (yes/no, default=no): ").lower() == 'yes'
    
    # Perform deletion
    print("\nPerforming reset operations...")
    
    users_deleted = reset_users()
    print(f"Deleted {users_deleted} user accounts")
    
    embeddings_deleted = reset_facial_features()
    print(f"Deleted {embeddings_deleted} facial embeddings")
    
    reset_students(delete_students)
    reset_chromadb()
    
    # Create essential user_accounts
    recreate_defaults = input("\nRecreate default users (admin/professor/student)? (yes/no, default=yes): ")
    if recreate_defaults.lower() != 'no':
        create_essential_users()
    
    print("\nReset operation completed successfully!")

if __name__ == "__main__":
    main()
