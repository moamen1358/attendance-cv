#!/usr/bin/env python3
"""
Professional Student Table Synchronization Script
This script demonstrates how the students table is synchronized with student_profiles 
and user_accounts to maintain proper relationships.
"""

import sqlite3
import pandas as pd

DATABASE_PATH = 'attendance_system.db'

def show_current_student_relationships():
    """Display current relationship status between tables"""
    print("=" * 80)
    print("CURRENT STUDENT TABLE RELATIONSHIPS")
    print("=" * 80)
    
    conn = sqlite3.connect(DATABASE_PATH)
    
    # Show student_profiles
    print("\n1. STUDENT_PROFILES TABLE:")
    print("-" * 40)
    profiles_df = pd.read_sql_query("""
        SELECT id, username, name, student_id, legacy_student_id
        FROM student_profiles 
        ORDER BY id
        LIMIT 10
    """, conn)
    print(f"Total student profiles: {pd.read_sql_query('SELECT COUNT(*) as count FROM student_profiles', conn).iloc[0]['count']}")
    print(profiles_df.to_string(index=False))
    
    # Show students (legacy)
    print("\n2. STUDENTS TABLE (Legacy):")
    print("-" * 40)
    students_df = pd.read_sql_query("""
        SELECT id, name, student_profile_id
        FROM students 
        ORDER BY id
    """, conn)
    print(f"Total legacy students: {len(students_df)}")
    print(students_df.to_string(index=False))
    
    # Show user_accounts with student role
    print("\n3. USER_ACCOUNTS (Role = 'student'):")
    print("-" * 40)
    users_df = pd.read_sql_query("""
        SELECT username, role, created_at
        FROM user_accounts 
        WHERE role = 'student'
        ORDER BY username
        LIMIT 10
    """, conn)
    print(f"Total student user accounts: {pd.read_sql_query('SELECT COUNT(*) FROM user_accounts WHERE role = \"student\"', conn).iloc[0]['count']}")
    print(users_df.to_string(index=False))
    
    # Show relationship status
    print("\n4. RELATIONSHIP STATUS:")
    print("-" * 40)
    try:
        # Connected students (have both profile and legacy)
        connected_df = pd.read_sql_query("""
            SELECT 
                sp.username,
                sp.name as profile_name,
                s.name as legacy_name,
                'Connected' as status
            FROM student_profiles sp
            JOIN students s ON sp.legacy_student_id = s.id
        """, conn)
        
        # Profile only students
        profile_only_df = pd.read_sql_query("""
            SELECT 
                sp.username,
                sp.name as profile_name,
                NULL as legacy_name,
                'Profile Only' as status
            FROM student_profiles sp
            LEFT JOIN students s ON sp.legacy_student_id = s.id
            WHERE s.id IS NULL
        """, conn)
        
        # Legacy only students
        legacy_only_df = pd.read_sql_query("""
            SELECT 
                NULL as username,
                s.name as profile_name,
                s.name as legacy_name,
                'Legacy Only' as status
            FROM students s
            LEFT JOIN student_profiles sp ON s.student_profile_id = sp.id
            WHERE sp.id IS NULL
        """, conn)
        
        print(f"Connected students: {len(connected_df)}")
        print(f"Profile only: {len(profile_only_df)}")
        print(f"Legacy only: {len(legacy_only_df)}")
        
        if len(connected_df) > 0:
            print("\nSample connected students:")
            print(connected_df.head().to_string(index=False))
            
    except Exception as e:
        print(f"Error checking relationships: {e}")
    
    conn.close()

def demonstrate_synchronization():
    """Demonstrate the synchronization process"""
    print("\n" + "=" * 80)
    print("SYNCHRONIZATION DEMONSTRATION")
    print("=" * 80)
    
    # Import the synchronization function
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
    
    try:
        from enhanced_db_explorer import synchronize_students_table, get_unified_student_list
        
        print("\n1. RUNNING SYNCHRONIZATION...")
        success, message = synchronize_students_table()
        print(f"Result: {message}")
        
        if success:
            print("\n2. UNIFIED STUDENT LIST AFTER SYNC:")
            print("-" * 40)
            unified_df = get_unified_student_list()
            print(f"Total unified students: {len(unified_df)}")
            if not unified_df.empty:
                print(unified_df[['username', 'name', 'status']].head(10).to_string(index=False))
        
    except ImportError as e:
        print(f"Could not import synchronization functions: {e}")
        print("Running basic synchronization check...")
        
        # Basic synchronization check
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        try:
            # Count students that need synchronization
            cursor.execute("""
                SELECT COUNT(*) 
                FROM student_profiles sp
                LEFT JOIN students s ON sp.legacy_student_id = s.id
                WHERE s.id IS NULL
            """)
            unsynced_count = cursor.fetchone()[0]
            
            print(f"Students needing synchronization: {unsynced_count}")
            
            if unsynced_count > 0:
                print("These student profiles need to be added to the students table:")
                cursor.execute("""
                    SELECT sp.username, sp.name
                    FROM student_profiles sp
                    LEFT JOIN students s ON sp.legacy_student_id = s.id
                    WHERE s.id IS NULL
                    LIMIT 5
                """)
                unsynced_students = cursor.fetchall()
                for username, name in unsynced_students:
                    print(f"  - {name} ({username})")
            
        except Exception as e:
            print(f"Error during synchronization check: {e}")
        
        conn.close()

def show_recommendations():
    """Show professional recommendations for managing student tables"""
    print("\n" + "=" * 80)
    print("PROFESSIONAL RECOMMENDATIONS")
    print("=" * 80)
    
    print("""
📋 STUDENT TABLE MANAGEMENT GUIDELINES:

1. PRIMARY TABLE: student_profiles
   ✅ Use for all new students
   ✅ Contains complete student information
   ✅ Primary source for authentication
   ✅ Links to user_accounts via username

2. LEGACY TABLE: students
   🔄 Automatically synchronized with student_profiles
   🔄 Maintains backward compatibility
   🔄 Used by legacy facial recognition systems
   🔄 Should contain ALL students from both sources

3. AUTHENTICATION: user_accounts
   🔐 Role-based access control
   🔐 Students have role = 'student'
   🔐 Links to student_profiles via username

📊 RELATIONSHIP STRUCTURE:

student_profiles (PRIMARY)
├── username → user_accounts.username
├── legacy_student_id → students.id
└── id ← students.student_profile_id

🔄 SYNCHRONIZATION PROCESS:

1. Automatically creates students records for all student_profiles
2. Links existing students to student_profiles via IDs
3. Handles user_accounts with role='student' but no profile
4. Maintains bidirectional relationships
5. Preserves data integrity

🎯 BEST PRACTICES:

• Always use student_profiles as primary source
• Run synchronization after bulk student imports
• Use unified_students view for comprehensive queries
• Maintain consistent username format across tables
• Regular synchronization ensures data consistency

🔧 MAINTENANCE:

• Synchronize after adding new students
• Check relationships after data imports
• Use get_unified_student_list() for reports
• Monitor for orphaned records
• Update legacy systems to use student_profiles
""")

def main():
    """Main function to demonstrate student table relationships"""
    show_current_student_relationships()
    demonstrate_synchronization()
    show_recommendations()

if __name__ == "__main__":
    main()
