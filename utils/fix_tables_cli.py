import sqlite3
import os

def completely_fix_teacher_tables():
    """
    Complete fix for teacher-subject relationships - Command line version
    """
    print("🔄 Starting complete teacher-subject relationship fix...")
    
    conn = sqlite3.connect('attendance_system.db')
    cursor = conn.cursor()
    
    try:
        # 1. Drop both tables to start fresh
        print("Dropping existing tables...")
        cursor.execute("DROP TABLE IF EXISTS teacher_subjects")
        cursor.execute("DROP TABLE IF EXISTS professor_subject_assignments")
        
        # 2. Create professor_subject_assignments table with correct structure
        print("Creating professor_subject_assignments table...")
        cursor.execute("""
        CREATE TABLE professor_subject_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            professor_username TEXT,
            subject_id INTEGER,
            assigned_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(professor_username, subject_id)
        )
        """)
        
        # 3. Create teacher_subjects table with correct structure
        print("Creating teacher_subjects table...")
        cursor.execute("""
        CREATE TABLE teacher_subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER,
            teacher_name TEXT,
            UNIQUE(subject_id, teacher_name)
        )
        """)
        
        # 4. Get professors and subjects to create some initial assignments
        cursor.execute("SELECT username FROM user_accounts WHERE role='professor'")
        professors = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT subject_id FROM subjects")
        subjects = [row[0] for row in cursor.fetchall()]
        
        if professors and subjects:
            # Create some sample assignments to demonstrate it working
            sample_count = min(len(professors) * len(subjects), 10)
            assignments_made = 0
            
            print(f"Found {len(professors)} professors and {len(subjects)} subjects")
            print("Creating sample assignments...")
            
            for prof in professors:
                for subj in subjects:
                    if assignments_made >= sample_count:
                        break
                        
                    try:
                        # Add to professor_subject_assignments
                        cursor.execute(
                            "INSERT INTO professor_subject_assignments (professor_username, subject_id) VALUES (?, ?)",
                            (prof, subj)
                        )
                        
                        # Add to teacher_subjects with same data
                        cursor.execute(
                            "INSERT INTO teacher_subjects (subject_id, teacher_name) VALUES (?, ?)",
                            (subj, prof)
                        )
                        
                        assignments_made += 1
                    except sqlite3.IntegrityError:
                        # Skip duplicates
                        continue
                        
                if assignments_made >= sample_count:
                    break
                    
            print(f"✅ Created {assignments_made} sample assignments")
            
        conn.commit()
        
        # 5. Verify the tables
        cursor.execute("SELECT COUNT(*) FROM professor_subject_assignments")
        prof_assignments_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM teacher_subjects")
        teacher_subjects_count = cursor.fetchone()[0]
        
        print(f"📊 Professor assignments count: {prof_assignments_count}")
        print(f"📊 Teacher subjects count: {teacher_subjects_count}")
        
        # 7. Final verification query - check if we can join subjects to professors
        cursor.execute("""
        SELECT COUNT(*)
        FROM user_accounts ua
        JOIN professor_subject_assignments psa ON ua.username = psa.professor_username
        JOIN subjects s ON psa.subject_id = s.subject_id
        WHERE ua.role = 'professor'
        """)
        verification_count = cursor.fetchone()[0]
        
        if verification_count > 0:
            print(f"✅ Verification successful! Found {verification_count} valid relationships.")
            return True
        else:
            print("❌ Verification failed. No relationships could be found.")
            return False
            
    except Exception as e:
        conn.rollback()
        print(f"❌ Error during fix: {str(e)}")
        return False
    finally:
        conn.close()
        print("🏁 Database connection closed")

def check_database_file():
    """Check if the database file exists and is accessible"""
    db_path = 'attendance_system.db'
    exists = os.path.isfile(db_path)
    readable = os.access(db_path, os.R_OK) if exists else False
    writable = os.access(db_path, os.W_OK) if exists else False
    
    print(f"Database file check:")
    print(f"- File exists: {'✅' if exists else '❌'}")
    print(f"- File readable: {'✅' if readable else '❌'}")
    print(f"- File writable: {'✅' if writable else '❌'}")
    
    if exists:
        # Check file size
        size_mb = os.path.getsize(db_path) / (1024 * 1024)
        print(f"- File size: {size_mb:.2f} MB")
        
        # Try opening the database
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            integrity = cursor.fetchone()[0]
            print(f"- Database integrity: {'✅ OK' if integrity == 'ok' else '❌ ' + integrity}")
            
            # List all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            print(f"- Tables found: {len(tables)}")
            print(f"  {', '.join(tables)}")
            
            conn.close()
            return True
        except Exception as e:
            print(f"Error accessing database: {str(e)}")
            return False
    else:
        print("Database file not found!")
        return False

if __name__ == "__main__":
    print("=======================================")
    print("🔧 Teacher-Subject Relationship Fix CLI")
    print("=======================================")
    
    db_ok = check_database_file()
    
    if db_ok:
        print("\nReady to fix tables. This will:")
        print(" - Drop existing teacher_subjects table")
        print(" - Drop existing professor_subject_assignments table") 
        print(" - Recreate both tables with proper structure")
        print(" - Create sample assignments if professors and subjects exist")
        
        confirm = input("\nProceed with fix? (y/n): ").strip().lower()
        
        if confirm == 'y':
            print("\nRunning fix...")
            if completely_fix_teacher_tables():
                print("\n✅ Success! Tables have been fixed successfully.")
                print("Now when you assign subjects to professors, they will appear correctly on the professor's dashboard.")
                print("\nNext steps:")
                print("1. Open the application in your browser")
                print("2. Go to Subject Management and use the Professor Assignments tab")
                print("3. Assign subjects to professors")
                print("4. Log in as a professor to see the assignments")
            else:
                print("\n❌ Fix was not fully successful. Please check the errors above.")
        else:
            print("Operation canceled.")
    else:
        print("\n❌ Database check failed. Please fix the database issues before continuing.")
