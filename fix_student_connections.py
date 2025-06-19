#!/usr/bin/env python3
"""
Fix Student Table Relationships
This script properly connects the students table with student_profiles table
"""

import sqlite3
from datetime import datetime

def analyze_student_tables():
    """Analyze the current state of student tables"""
    conn = sqlite3.connect('attendance_system.db')
    cursor = conn.cursor()
    
    print("🔍 Analyzing Student Table Relationships")
    print("=" * 50)
    
    # Get data from students table
    cursor.execute("SELECT id, name FROM students")
    students_data = cursor.fetchall()
    
    # Get data from student_profiles table
    cursor.execute("SELECT id, username, name, student_id FROM student_profiles")
    profiles_data = cursor.fetchall()
    
    print(f"📊 Current Data:")
    print(f"  - students table: {len(students_data)} records")
    print(f"  - student_profiles table: {len(profiles_data)} records")
    
    print(f"\n📋 Students table data:")
    for student_id, name in students_data:
        print(f"  ID: {student_id}, Name: '{name}'")
    
    print(f"\n📋 Student_profiles table data:")
    for prof_id, username, name, student_id in profiles_data:
        print(f"  ID: {prof_id}, Username: '{username}', Name: '{name}', Student_ID: '{student_id}'")
    
    # Check for potential matches by name
    print(f"\n🔗 Potential Name Matches:")
    for student_id, student_name in students_data:
        for prof_id, username, prof_name, student_sid in profiles_data:
            if student_name.lower() in prof_name.lower() or prof_name.lower() in student_name.lower():
                print(f"  - '{student_name}' (students) ≈ '{prof_name}' (profiles)")
    
    conn.close()
    return students_data, profiles_data

def create_student_table_connection():
    """Create proper connection between student tables"""
    conn = sqlite3.connect('attendance_system.db')
    cursor = conn.cursor()
    
    print(f"\n🔗 Creating Student Table Connections")
    print("-" * 40)
    
    try:
        # Option 1: Add student_profile_id to students table
        cursor.execute("PRAGMA table_info(students)")
        students_columns = [col[1] for col in cursor.fetchall()]
        
        if 'student_profile_id' not in students_columns:
            cursor.execute("ALTER TABLE students ADD COLUMN student_profile_id INTEGER")
            print("  ✅ Added student_profile_id column to students table")
        
        # Option 2: Add legacy_student_id to student_profiles table  
        cursor.execute("PRAGMA table_info(student_profiles)")
        profiles_columns = [col[1] for col in cursor.fetchall()]
        
        if 'legacy_student_id' not in profiles_columns:
            cursor.execute("ALTER TABLE student_profiles ADD COLUMN legacy_student_id INTEGER")
            print("  ✅ Added legacy_student_id column to student_profiles table")
        
        # Try to create connections based on name matching
        cursor.execute("SELECT id, name FROM students")
        students_data = cursor.fetchall()
        
        connections_made = 0
        
        for student_id, student_name in students_data:
            # Try to find matching profile by name
            cursor.execute("""
                SELECT id, username, name FROM student_profiles 
                WHERE LOWER(name) LIKE LOWER(?) OR LOWER(username) LIKE LOWER(?)
            """, (f"%{student_name}%", f"%{student_name}%"))
            
            matching_profiles = cursor.fetchall()
            
            if matching_profiles:
                # Take the first match
                profile_id, username, profile_name = matching_profiles[0]
                
                # Update students table with profile reference
                cursor.execute("""
                    UPDATE students 
                    SET student_profile_id = ? 
                    WHERE id = ?
                """, (profile_id, student_id))
                
                # Update student_profiles table with legacy reference
                cursor.execute("""
                    UPDATE student_profiles 
                    SET legacy_student_id = ? 
                    WHERE id = ?
                """, (student_id, profile_id))
                
                print(f"  ✅ Connected '{student_name}' (ID:{student_id}) ↔ '{profile_name}' (ID:{profile_id})")
                connections_made += 1
            else:
                # Create new student profile for unmatched students
                username = student_name.lower().replace(' ', '_')
                
                cursor.execute("""
                    INSERT INTO student_profiles (username, name, student_id, password, section)
                    VALUES (?, ?, ?, 'temp_password', 'unassigned')
                """, (username, student_name, f"LEG_{student_id}"))
                
                new_profile_id = cursor.lastrowid
                
                # Update students table
                cursor.execute("""
                    UPDATE students 
                    SET student_profile_id = ? 
                    WHERE id = ?
                """, (new_profile_id, student_id))
                
                # Update student_profiles table
                cursor.execute("""
                    UPDATE student_profiles 
                    SET legacy_student_id = ? 
                    WHERE id = ?
                """, (student_id, new_profile_id))
                
                # Also add to user_accounts
                cursor.execute("""
                    INSERT OR IGNORE INTO user_accounts (username, password, role)
                    VALUES (?, 'temp_password', 'student')
                """, (username,))
                
                print(f"  ✅ Created new profile for '{student_name}' (ID:{student_id}) → '{username}'")
                connections_made += 1
        
        print(f"\n📊 Connection Summary: {connections_made} connections established")
        
    except Exception as e:
        print(f"  ❌ Error creating connections: {e}")
    
    conn.commit()
    conn.close()

def create_unified_student_view():
    """Create a unified view that combines both student tables"""
    conn = sqlite3.connect('attendance_system.db')
    cursor = conn.cursor()
    
    print(f"\n🔍 Creating Unified Student View")
    print("-" * 35)
    
    try:
        # Drop existing view if it exists
        cursor.execute("DROP VIEW IF EXISTS unified_students")
        
        # Create comprehensive student view
        cursor.execute("""
            CREATE VIEW unified_students AS
            SELECT 
                sp.id as profile_id,
                sp.username,
                sp.name,
                sp.student_id as official_student_id,
                sp.section,
                sp.email,
                sp.phone,
                sp.last_login,
                sp.created_at,
                s.id as legacy_id,
                s.name as legacy_name,
                ua.role,
                ua.last_login as account_last_login,
                CASE 
                    WHEN s.id IS NOT NULL THEN 'Connected to Legacy'
                    ELSE 'Profile Only'
                END as connection_status
            FROM student_profiles sp
            LEFT JOIN students s ON sp.legacy_student_id = s.id
            LEFT JOIN user_accounts ua ON sp.username = ua.username
            
            UNION ALL
            
            SELECT 
                NULL as profile_id,
                s.name as username,
                s.name,
                'LEG_' || s.id as official_student_id,
                'unknown' as section,
                NULL as email,
                NULL as phone,
                NULL as last_login,
                NULL as created_at,
                s.id as legacy_id,
                s.name as legacy_name,
                'student' as role,
                NULL as account_last_login,
                'Legacy Only' as connection_status
            FROM students s
            WHERE s.student_profile_id IS NULL
        """)
        
        print("  ✅ Created unified_students view")
        
        # Create a simplified current students view
        cursor.execute("DROP VIEW IF EXISTS current_students")
        cursor.execute("""
            CREATE VIEW current_students AS
            SELECT 
                sp.username,
                sp.name,
                sp.student_id,
                sp.section,
                sp.email,
                CASE 
                    WHEN sp.legacy_student_id IS NOT NULL THEN 'Migrated from Legacy'
                    ELSE 'New Student'
                END as student_type,
                ua.last_login,
                COUNT(ar.id) as attendance_count
            FROM student_profiles sp
            LEFT JOIN user_accounts ua ON sp.username = ua.username
            LEFT JOIN attendance_records ar ON sp.username = ar.student_username
            GROUP BY sp.username, sp.name, sp.student_id, sp.section, sp.email, ua.last_login
        """)
        
        print("  ✅ Created current_students view")
        
    except Exception as e:
        print(f"  ❌ Error creating views: {e}")
    
    conn.commit()
    conn.close()

def validate_student_connections():
    """Validate the student table connections"""
    conn = sqlite3.connect('attendance_system.db')
    cursor = conn.cursor()
    
    print(f"\n✅ Validating Student Connections")
    print("-" * 35)
    
    try:
        # Check connection statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_students,
                COUNT(student_profile_id) as connected_students,
                COUNT(*) - COUNT(student_profile_id) as unconnected_students
            FROM students
        """)
        
        total, connected, unconnected = cursor.fetchone()
        print(f"  📊 Students table: {total} total, {connected} connected, {unconnected} unconnected")
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_profiles,
                COUNT(legacy_student_id) as connected_profiles,
                COUNT(*) - COUNT(legacy_student_id) as new_profiles
            FROM student_profiles
        """)
        
        total_prof, connected_prof, new_prof = cursor.fetchone()
        print(f"  📊 Student_profiles: {total_prof} total, {connected_prof} connected, {new_prof} new")
        
        # Check for orphaned attendance records
        cursor.execute("""
            SELECT COUNT(*) FROM attendance_records ar
            LEFT JOIN student_profiles sp ON ar.student_username = sp.username
            WHERE sp.username IS NULL AND ar.student_username IS NOT NULL
        """)
        
        orphaned_attendance = cursor.fetchone()[0]
        print(f"  📊 Orphaned attendance records: {orphaned_attendance}")
        
        # Show sample connections
        cursor.execute("""
            SELECT s.id, s.name, sp.username, sp.name 
            FROM students s
            JOIN student_profiles sp ON s.student_profile_id = sp.id
            LIMIT 5
        """)
        
        connections = cursor.fetchall()
        if connections:
            print(f"\n  🔗 Sample Connections:")
            for s_id, s_name, sp_username, sp_name in connections:
                print(f"    students[{s_id}]:'{s_name}' ↔ profiles[{sp_username}]:'{sp_name}'")
        
        # Test the unified view
        cursor.execute("SELECT COUNT(*) FROM unified_students")
        unified_count = cursor.fetchone()[0]
        print(f"\n  📋 Unified view contains: {unified_count} student records")
        
    except Exception as e:
        print(f"  ❌ Error during validation: {e}")
    
    conn.close()

def generate_student_connection_report():
    """Generate a report on student table connections"""
    conn = sqlite3.connect('attendance_system.db')
    cursor = conn.cursor()
    
    print(f"\n\n📊 STUDENT CONNECTION REPORT")
    print("=" * 60)
    
    try:
        # Get comprehensive statistics
        cursor.execute("SELECT COUNT(*) FROM students")
        students_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM student_profiles") 
        profiles_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM students WHERE student_profile_id IS NOT NULL")
        connected_students = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM student_profiles WHERE legacy_student_id IS NOT NULL")
        connected_profiles = cursor.fetchone()[0]
        
        print(f"📈 Connection Statistics:")
        print(f"  • Legacy students table: {students_count} records")
        print(f"  • Modern student_profiles: {profiles_count} records")
        print(f"  • Students connected to profiles: {connected_students}/{students_count}")
        print(f"  • Profiles connected to legacy: {connected_profiles}/{profiles_count}")
        
        # Show connection efficiency
        if students_count > 0:
            connection_rate = (connected_students / students_count) * 100
            print(f"  • Connection rate: {connection_rate:.1f}%")
        
        # Show unified view data
        cursor.execute("""
            SELECT connection_status, COUNT(*) 
            FROM unified_students 
            GROUP BY connection_status
        """)
        
        status_counts = cursor.fetchall()
        print(f"\n🔗 Connection Status:")
        for status, count in status_counts:
            print(f"  • {status}: {count} students")
        
        print(f"\n✅ Student tables are now properly connected!")
        print(f"📋 Use 'unified_students' view for complete student data")
        print(f"📋 Use 'current_students' view for active student information")
        
    except Exception as e:
        print(f"❌ Error generating report: {e}")
    
    conn.close()

def main():
    """Main function to fix student table relationships"""
    print("🔧 Fixing Student Table Relationships")
    print("Timestamp:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print()
    
    try:
        # Analyze current state
        students_data, profiles_data = analyze_student_tables()
        
        # Create connections
        create_student_table_connection()
        
        # Create unified views
        create_unified_student_view()
        
        # Validate connections
        validate_student_connections()
        
        # Generate report
        generate_student_connection_report()
        
    except Exception as e:
        print(f"❌ Error during student table fix: {e}")

if __name__ == "__main__":
    main()
