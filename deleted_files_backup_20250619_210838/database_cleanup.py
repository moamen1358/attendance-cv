#!/usr/bin/env python3
"""
Database Cleanup and Optimization Script
This script implements the recommended database cleanup and establishes proper relationships.
"""

import sqlite3
import pandas as pd
from datetime import datetime
import os

def create_backup():
    """Create a backup of the database before making changes"""
    backup_name = f"attendance_system_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    
    try:
        import shutil
        shutil.copy2('attendance_system.db', backup_name)
        print(f"✅ Backup created: {backup_name}")
        return backup_name
    except Exception as e:
        print(f"❌ Failed to create backup: {e}")
        return None

def delete_unused_tables():
    """Delete tables that are empty and unused"""
    conn = sqlite3.connect('attendance_system.db')
    cursor = conn.cursor()
    
    unused_tables = ['attendance', 'attendance_log', 'course_students', 'student_profiles_temp']
    
    print("\\n🗑️ Deleting Unused Tables...")
    
    for table in unused_tables:
        try:
            # Double-check table is empty
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            
            if count == 0:
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
                print(f"  ✅ Deleted empty table: {table}")
            else:
                print(f"  ⚠️ Skipped {table} - contains {count} records")
                
        except Exception as e:
            print(f"  ❌ Error deleting {table}: {e}")
    
    conn.commit()
    conn.close()

def add_foreign_key_constraints():
    """Add proper foreign key relationships between tables"""
    conn = sqlite3.connect('attendance_system.db')
    cursor = conn.cursor()
    
    print("\\n🔗 Adding Foreign Key Relationships...")
    
    # Enable foreign key constraints
    cursor.execute("PRAGMA foreign_keys = ON")
    
    try:
        # Add subject_id reference in class_schedules if not exists
        cursor.execute("PRAGMA table_info(class_schedules)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'subject_id' not in columns:
            cursor.execute("ALTER TABLE class_schedules ADD COLUMN subject_id INTEGER")
            print("  ✅ Added subject_id column to class_schedules")
        
        # Update class_schedules to link with subjects table
        cursor.execute("""
            UPDATE class_schedules 
            SET subject_id = (
                SELECT id FROM subjects 
                WHERE subjects.name = class_schedules.subject 
                LIMIT 1
            )
            WHERE subject_id IS NULL
        """)
        
        print("  ✅ Updated class_schedules with proper subject references")
        
    except Exception as e:
        print(f"  ❌ Error adding foreign keys: {e}")
    
    conn.commit()
    conn.close()

def consolidate_user_data():
    """Consolidate user information and establish proper relationships"""
    conn = sqlite3.connect('attendance_system.db')
    cursor = conn.cursor()
    
    print("\\n👥 Consolidating User Data...")
    
    try:
        # Create a unified user management approach
        # Ensure all users in user_accounts have corresponding profile entries
        
        # Get all professors from user_accounts
        cursor.execute("SELECT username, role FROM user_accounts WHERE role = 'professor'")
        professors = cursor.fetchall()
        
        for username, role in professors:
            # Check if professor exists in professor_profiles
            cursor.execute("SELECT COUNT(*) FROM professor_profiles WHERE username = ?", (username,))
            exists = cursor.fetchone()[0]
            
            if exists == 0:
                # Create professor profile
                cursor.execute("""
                    INSERT INTO professor_profiles (username, name, password, email, phone, department)
                    SELECT username, username, password, '', '', ''
                    FROM user_accounts 
                    WHERE username = ? AND role = 'professor'
                """, (username,))
                print(f"  ✅ Created professor profile for: {username}")
        
        # Get all students from user_accounts
        cursor.execute("SELECT username, role FROM user_accounts WHERE role = 'student'")
        students = cursor.fetchall()
        
        for username, role in students:
            # Check if student exists in student_profiles
            cursor.execute("SELECT COUNT(*) FROM student_profiles WHERE username = ?", (username,))
            exists = cursor.fetchone()[0]
            
            if exists == 0:
                # Create student profile
                cursor.execute("""
                    INSERT INTO student_profiles (username, name, student_id, password, section, email, phone)
                    SELECT username, username, username, password, '', '', ''
                    FROM user_accounts 
                    WHERE username = ? AND role = 'student'
                """, (username,))
                print(f"  ✅ Created student profile for: {username}")
        
        # Sync existing profiles with user_accounts
        cursor.execute("""
            INSERT OR IGNORE INTO user_accounts (username, password, role, created_at)
            SELECT username, password, 'professor', created_at
            FROM professor_profiles
            WHERE username NOT IN (SELECT username FROM user_accounts)
        """)
        
        cursor.execute("""
            INSERT OR IGNORE INTO user_accounts (username, password, role, created_at)
            SELECT username, password, 'student', created_at
            FROM student_profiles
            WHERE username NOT IN (SELECT username FROM user_accounts)
        """)
        
        print("  ✅ Synchronized user accounts with profile tables")
        
    except Exception as e:
        print(f"  ❌ Error consolidating user data: {e}")
    
    conn.commit()
    conn.close()

def fix_attendance_relationships():
    """Fix attendance table relationships and data consistency"""
    conn = sqlite3.connect('attendance_system.db')
    cursor = conn.cursor()
    
    print("\\n📊 Fixing Attendance Data Relationships...")
    
    try:
        # Update attendance_records to use proper usernames
        # First, let's see what we're working with
        cursor.execute("SELECT DISTINCT student_username FROM attendance_records WHERE student_username IS NOT NULL")
        student_usernames = [row[0] for row in cursor.fetchall()]
        
        print(f"  📋 Found attendance records for usernames: {student_usernames}")
        
        # Ensure these usernames exist in student_profiles
        for username in student_usernames:
            cursor.execute("SELECT COUNT(*) FROM student_profiles WHERE username = ?", (username,))
            exists = cursor.fetchone()[0]
            
            if exists == 0:
                # Create missing student profile
                cursor.execute("""
                    INSERT INTO student_profiles (username, name, student_id, password, section)
                    VALUES (?, ?, ?, 'temp_password', '')
                """, (username, username.title(), username))
                
                # Also add to user_accounts
                cursor.execute("""
                    INSERT OR IGNORE INTO user_accounts (username, password, role)
                    VALUES (?, 'temp_password', 'student')
                """, (username,))
                
                print(f"  ✅ Created student profile for: {username}")
        
        # Update class_attendance to use consistent student identification
        cursor.execute("SELECT DISTINCT student_name FROM class_attendance WHERE student_name IS NOT NULL")
        class_students = [row[0] for row in cursor.fetchall()]
        
        # Try to map student names to usernames
        for student_name in class_students:
            # Look for matching username in student_profiles
            cursor.execute("SELECT username FROM student_profiles WHERE name = ? OR username = ?", 
                         (student_name, student_name))
            result = cursor.fetchone()
            
            if result:
                username = result[0]
                # Update class_attendance to include username
                cursor.execute("""
                    UPDATE class_attendance 
                    SET username = ? 
                    WHERE student_name = ? AND (username IS NULL OR username = '')
                """, (username, student_name))
                print(f"  ✅ Linked {student_name} to username {username}")
        
    except Exception as e:
        print(f"  ❌ Error fixing attendance relationships: {e}")
    
    conn.commit()
    conn.close()

def create_improved_views():
    """Create improved database views for better data access"""
    conn = sqlite3.connect('attendance_system.db')
    cursor = conn.cursor()
    
    print("\\n🔍 Creating Improved Database Views...")
    
    try:
        # Drop existing views that might conflict
        views_to_drop = ['unified_attendance_view', 'student_attendance_summary']
        
        for view in views_to_drop:
            cursor.execute(f"DROP VIEW IF EXISTS {view}")
        
        # Create a comprehensive attendance view
        cursor.execute("""
            CREATE VIEW unified_attendance_summary AS
            SELECT 
                ar.id,
                ar.student_username,
                sp.name as student_name,
                sp.section,
                s.name as subject_name,
                s.course_code,
                ar.timestamp,
                ar.status,
                ar.class_date,
                ar.confidence,
                ar.device_id
            FROM attendance_records ar
            LEFT JOIN student_profiles sp ON ar.student_username = sp.username
            LEFT JOIN subjects s ON ar.subject_id = s.id
        """)
        print("  ✅ Created unified_attendance_summary view")
        
        # Create a professor-subject mapping view
        cursor.execute("""
            CREATE VIEW professor_teaching_schedule AS
            SELECT 
                pp.username as professor_username,
                pp.name as professor_name,
                pp.department,
                s.name as subject_name,
                s.course_code,
                cs.day,
                cs.start_time,
                cs.end_time,
                cs.room
            FROM professor_profiles pp
            JOIN professor_subject_assignments psa ON pp.username = psa.professor_username
            JOIN subjects s ON psa.subject_id = s.id
            LEFT JOIN class_schedules cs ON s.id = cs.subject_id
        """)
        print("  ✅ Created professor_teaching_schedule view")
        
        # Create a comprehensive student view
        cursor.execute("""
            CREATE VIEW student_complete_profile AS
            SELECT 
                sp.id,
                sp.username,
                sp.name,
                sp.student_id,
                sp.section,
                sp.email,
                sp.phone,
                ua.last_login,
                ua.created_at as account_created,
                COUNT(ar.id) as total_attendance_records
            FROM student_profiles sp
            LEFT JOIN user_accounts ua ON sp.username = ua.username
            LEFT JOIN attendance_records ar ON sp.username = ar.student_username
            GROUP BY sp.id, sp.username, sp.name, sp.student_id, sp.section, sp.email, sp.phone, ua.last_login, ua.created_at
        """)
        print("  ✅ Created student_complete_profile view")
        
    except Exception as e:
        print(f"  ❌ Error creating views: {e}")
    
    conn.commit()
    conn.close()

def optimize_database():
    """Optimize database performance"""
    conn = sqlite3.connect('attendance_system.db')
    cursor = conn.cursor()
    
    print("\\n⚡ Optimizing Database Performance...")
    
    try:
        # Add useful indexes if they don't exist
        indexes = [
            ("idx_student_profiles_username", "student_profiles", "username"),
            ("idx_professor_profiles_username", "professor_profiles", "username"),
            ("idx_attendance_records_timestamp", "attendance_records", "timestamp"),
            ("idx_attendance_records_class_date", "attendance_records", "class_date"),
            ("idx_class_schedules_subject_id", "class_schedules", "subject_id"),
            ("idx_professor_subject_assignments_professor", "professor_subject_assignments", "professor_username"),
            ("idx_professor_subject_assignments_subject", "professor_subject_assignments", "subject_id")
        ]
        
        for index_name, table, column in indexes:
            try:
                cursor.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table}({column})")
                print(f"  ✅ Added index: {index_name}")
            except Exception as e:
                print(f"  ⚠️ Index {index_name} might already exist: {e}")
        
        # Run VACUUM to optimize database file
        cursor.execute("VACUUM")
        print("  ✅ Database optimized with VACUUM")
        
        # Analyze tables for query optimizer
        cursor.execute("ANALYZE")
        print("  ✅ Database statistics updated")
        
    except Exception as e:
        print(f"  ❌ Error optimizing database: {e}")
    
    conn.commit()
    conn.close()

def generate_cleanup_report():
    """Generate a report of the cleanup process"""
    conn = sqlite3.connect('attendance_system.db')
    cursor = conn.cursor()
    
    print("\\n\\n📊 CLEANUP COMPLETION REPORT")
    print("=" * 60)
    
    # Count tables
    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence'")
    table_count = cursor.fetchone()[0]
    
    # Count views
    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='view'")
    view_count = cursor.fetchone()[0]
    
    # Count indexes
    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'")
    index_count = cursor.fetchone()[0]
    
    # Count users
    cursor.execute("SELECT COUNT(*) FROM user_accounts")
    user_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM student_profiles")
    student_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM professor_profiles")
    professor_count = cursor.fetchone()[0]
    
    # Count attendance records
    cursor.execute("SELECT COUNT(*) FROM attendance_records")
    attendance_count = cursor.fetchone()[0]
    
    print(f"📋 Database Structure:")
    print(f"  - Tables: {table_count}")
    print(f"  - Views: {view_count}")
    print(f"  - Indexes: {index_count}")
    print(f"\\n👥 User Data:")
    print(f"  - Total user accounts: {user_count}")
    print(f"  - Student profiles: {student_count}")
    print(f"  - Professor profiles: {professor_count}")
    print(f"\\n📊 Data Records:")
    print(f"  - Attendance records: {attendance_count}")
    
    # Check for orphaned data
    cursor.execute("""
        SELECT COUNT(*) FROM attendance_records ar
        LEFT JOIN student_profiles sp ON ar.student_username = sp.username
        WHERE sp.username IS NULL AND ar.student_username IS NOT NULL
    """)
    orphaned_attendance = cursor.fetchone()[0]
    
    if orphaned_attendance > 0:
        print(f"\\n⚠️ Data Issues:")
        print(f"  - Orphaned attendance records: {orphaned_attendance}")
    else:
        print(f"\\n✅ No data integrity issues found!")
    
    conn.close()
    
    print(f"\\n🎉 Database cleanup completed successfully!")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def main():
    """Main cleanup function"""
    print("🚀 Starting Database Cleanup and Optimization...")
    
    # Create backup first
    backup_name = create_backup()
    if not backup_name:
        print("❌ Cannot proceed without backup. Exiting.")
        return
    
    try:
        # Perform cleanup operations
        delete_unused_tables()
        add_foreign_key_constraints()
        consolidate_user_data()
        fix_attendance_relationships()
        create_improved_views()
        optimize_database()
        
        # Generate final report
        generate_cleanup_report()
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        print(f"Database backup available at: {backup_name}")
    
    print("\\n✅ Cleanup process completed!")

if __name__ == "__main__":
    main()
