import sqlite3
import hashlib

# Constants
DATABASE_PATH = 'attendance_system.db'

def update_database_schema():
    """Update database to support three distinct user roles"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    print("Checking existing users table...")
    cursor.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cursor.fetchall()]

    if 'role' in columns:
        print("Role column already exists in users table")
    else:
        print("Adding role column to users table")
        cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'student'")
        conn.commit()
    
    # Add sample users with proper password hashing
    test_users = [
        ('student', 'student123', 'student'),
        ('professor', 'professor123', 'professor'),
        ('admin', 'admin123', 'admin')
    ]
    
    for username, password, role in test_users:
        # Hash the password
        hashed_password = hashlib.md5(password.encode()).hexdigest()
        
        # Check if user exists
        cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            print(f"Updating user '{username}' with role '{role}'")
            cursor.execute(
                "UPDATE users SET password = ?, role = ? WHERE username = ?",
                (hashed_password, role, username)
            )
        else:
            print(f"Creating user '{username}' with role '{role}'")
            cursor.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                (username, hashed_password, role)
            )
            
            # Add to students table if student role
            if role == 'student':
                cursor.execute("SELECT name FROM students WHERE name = ?", (username,))
                if not cursor.fetchone():
                    cursor.execute("INSERT INTO students (name) VALUES (?)", (username,))
                    print(f"Added '{username}' to students table")

    # Commit changes
    conn.commit()
    
    # Verify user roles
    cursor.execute("SELECT username, role FROM users")
    print("\nUser roles in database:")
    for user, role in cursor.fetchall():
        print(f"  {user}: {role}")
    
    conn.close()
    print("\nDatabase schema update complete!")

if __name__ == "__main__":
    update_database_schema()
