import sqlite3

# Constants
DATABASE_PATH = 'attendance_system.db'

def explain_registration_process():
    """Explain where student data goes when registering"""
    print("When registering a new student, data is stored in 3 main places:\n")
    
    print("1. STUDENTS TABLE:")
    print("   - Stores basic student information (name and section)")
    print("   - Used for attendance tracking and reports")
    
    print("\n2. USERS TABLE:")
    print("   - Creates login credentials for the student")
    print("   - Username = Student name")
    print("   - Password = name_sec# format (e.g., 'moamen_sec1')")
    print("   - Role is set to 'student'")
    
    print("\n3. PRESIDENTS_EMBEDS TABLE:")
    print("   - Stores facial recognition data (facial features/embeddings)")
    print("   - Used for identifying student_profiles in real-time recognition")
    
    # Show table schemas
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    print("\n=== Database Table Schemas ===")
    
    # Students table
    cursor.execute("PRAGMA table_info(students)")
    columns = cursor.fetchall()
    print("\nSTUDENTS TABLE COLUMNS:")
    for col in columns:
        print(f"   - {col[1]} ({col[2]})")
    
    # Users table
    cursor.execute("PRAGMA table_info(users)")
    columns = cursor.fetchall()
    print("\nUSERS TABLE COLUMNS:")
    for col in columns:
        print(f"   - {col[1]} ({col[2]})")
    
    # Presidents_embeds table
    cursor.execute("PRAGMA table_info(presidents_embeds)")
    columns = cursor.fetchall()
    print("\nPRESIDENTS_EMBEDS TABLE COLUMNS:")
    for col in columns:
        print(f"   - {col[1]} ({col[2]})")
    
    conn.close()
    
    print("\n=== Registration Process in Code ===")
    print("The process is handled primarily by:")
    print("1. register_face_from_image() function - Extracts facial features and stores them")
    print("2. register_student() function - Creates user account and updates student_profiles table")
    print("3. Later, these embeddings are used by real_time_prediction.py for identification")

if __name__ == "__main__":
    explain_registration_process()
