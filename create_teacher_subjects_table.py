import sqlite3
import os
import pandas as pd
from tabulate import tabulate

# Constants
DATABASE_PATH = 'attendance_system.db'

def get_db_connection():
    """Create a connection to the database"""
    return sqlite3.connect(DATABASE_PATH)

def create_teacher_subjects_table():
    """Create the teacher_subjects table if it doesn't exist"""
    print("\n🔄 Creating teacher_subjects table...")
    
    if not os.path.exists(DATABASE_PATH):
        print(f"❌ Error: Database file '{DATABASE_PATH}' not found.")
        return False
    
    conn = get_db_connection()
    cursor = conn.cursor()
    


    try:
        # Check if table already exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='teacher_subjects'")
        if cursor.fetchone():
            print("✅ teacher_subjects table already exists")
            return True
        
        # Create the teacher_subjects table
        cursor.execute("""
        CREATE TABLE teacher_subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_username TEXT NOT NULL,
            subject TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(teacher_username, subject)
        )
        """)
        
        # Add index for faster lookups
        cursor.execute("CREATE INDEX idx_teacher_subjects_username ON teacher_subjects(teacher_username)")
        
        print("✅ Created teacher_subjects table")
        
        # Return success
        return True
        
    except Exception as e:
        print(f"❌ Error creating teacher_subjects table: {e}")
        return False
        
    finally:
        conn.close()

def extract_teachers_from_schedule():
    """Extract teacher-subject relationships from class_schedules table"""
    conn = get_db_connection()
    
    try:
        # Check if class_schedules table exists
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='class_schedules'")
        if not cursor.fetchone():
            print("❌ class_schedules table not found")
            return []
        
        # Get list of teachers and their subjects
        query = """
        SELECT DISTINCT teacher, subject 
        FROM class_schedules 
        WHERE teacher IS NOT NULL AND teacher != ''
        ORDER BY teacher, subject
        """
        
        df = pd.read_sql(query, conn)
        
        if df.empty:
            print("❌ No teacher-subject data found in class schedules")
            return []
        
        # Get the list of users to verify teachers exist
        user_query = """
        SELECT username 
        FROM user_accounts 
        WHERE role = 'professor' OR role = 'admin'
        """
        
        try:
            users_df = pd.read_sql(user_query, conn)
            teachers = users_df['username'].tolist()
        except:
            print("⚠️ Could not get list of professors from user_accounts")
            teachers = []
        
        # Create a list of (teacher_username, subject) tuples
        teacher_subjects = []
        
        # Map full teacher names to usernames where possible
        for _, row in df.iterrows():
            teacher_name = row['teacher']
            subject = row['subject']
            
            # Try to find a matching username - use part of the teacher's name
            # This is a heuristic and might need adjustment
            username_found = False
            name_parts = teacher_name.lower().replace("dr.", "").replace("prof.", "").strip().split()
            
            if name_parts:
                for teacher in teachers:
                    # Check if teacher username contains part of the full name
                    # (e.g. "williams" in "Dr. Rebecca Williams")
                    for part in name_parts:
                        if part and len(part) > 3 and part in teacher.lower():
                            teacher_subjects.append((teacher, subject))
                            username_found = True
                            break
                    if username_found:
                        break
            
            # If we couldn't match to a username, use the full name
            # (this will need manual correction later)
            if not username_found:
                # Create a username from teacher name (simple approach)
                # Remove prefixes, take first part of name to be username
                username = name_parts[0] if name_parts else "unknown"
                teacher_subjects.append((username, subject))
        
        print(f"✅ Found {len(teacher_subjects)} teacher-subject relationships")
        return teacher_subjects
        
    except Exception as e:
        print(f"❌ Error extracting teacher data: {e}")
        return []
        
    finally:
        conn.close()

def populate_teacher_subjects():
    """Populate the teacher_subjects table with data"""
    print("\n🔄 Populating teacher_subjects table...")
    
    # Get teacher-subject relationships
    teacher_subjects = extract_teachers_from_schedule()
    
    if not teacher_subjects:
        print("⚠️ No teacher-subject relationships found to add")
        
        # Add default mapping as a fallback
        teacher_subjects = [
            ('smith', 'Advanced Mathematics'),
            ('williams', 'Computer Science'), 
            ('brown', 'Physics'),
            ('martin', 'Engineering'),
            ('taylor', 'Statistics')
        ]
        print(f"➕ Adding {len(teacher_subjects)} default teacher-subject mappings")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Start transaction
        cursor.execute("BEGIN TRANSACTION")
        
        # Insert teacher-subject relationships
        for username, subject in teacher_subjects:
            cursor.execute(
                "INSERT OR IGNORE INTO teacher_subjects (teacher_username, subject) VALUES (?, ?)",
                (username, subject)
            )
        
        # Add admin-to-all-subjects mapping
        # Get list of distinct subjects
        cursor.execute("SELECT DISTINCT subject FROM class_schedules WHERE subject != ''")
        subjects = [row[0] for row in cursor.fetchall()]
        
        # Check if there are any admin users
        cursor.execute("SELECT username FROM user_accounts WHERE role = 'admin'")
        admin_users = [row[0] for row in cursor.fetchall()]
        
        # If no admins found, add a default admin-all subjects mapping
        if not admin_users:
            admin_users = ['admin']
        
        # Add each subject to each admin user
        for admin in admin_users:
            for subject in subjects:
                cursor.execute(
                    "INSERT OR IGNORE INTO teacher_subjects (teacher_username, subject) VALUES (?, ?)",
                    (admin, subject)
                )
            print(f"✅ Added all subjects to admin user: {admin}")
        
        # Commit changes
        cursor.execute("COMMIT")
        
        # Show the data
        cursor.execute("SELECT teacher_username, subject FROM teacher_subjects ORDER BY teacher_username")
        rows = cursor.fetchall()
        
        if rows:
            print("\n=== Teacher-Subject Assignments ===")
            df = pd.DataFrame(rows, columns=['Teacher Username', 'Subject'])
            print(tabulate(df, headers='keys', tablefmt='pretty', showindex=False))
            
            # Get count per teacher
            print("\n=== Subjects per Teacher ===")
            cursor.execute("""
                SELECT teacher_username, COUNT(subject) as subject_count 
                FROM teacher_subjects 
                GROUP BY teacher_username
                ORDER BY subject_count DESC
            """)
            count_rows = cursor.fetchall()
            count_df = pd.DataFrame(count_rows, columns=['Teacher', 'Subject Count'])
            print(tabulate(count_df, headers='keys', tablefmt='pretty', showindex=False))
        
        print(f"✅ Successfully added {len(rows)} teacher-subject relationships")
        return True
        
    except Exception as e:
        print(f"❌ Error populating teacher_subjects table: {e}")
        cursor.execute("ROLLBACK")
        return False
        
    finally:
        conn.close()

def main():
    """Main function"""
    print("🔧 Teacher-Subjects Table Creation Utility")
    print("This will create the missing teacher_subjects table needed for the application")
    
    # Create table
    if create_teacher_subjects_table():
        # Populate table
        populate_teacher_subjects()
        print("\n✅ Table created and populated successfully!")
        print("\nYou can now run subject_management.py without errors.")
    else:
        print("\n❌ Failed to create teacher_subjects table")

if __name__ == "__main__":
    main()
