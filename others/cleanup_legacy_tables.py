#!/usr/bin/env python3
"""
Final Legacy Table Cleanup

This script removes the remaining legacy tables that were missed in the previous cleanup.
"""

import sqlite3
from datetime import datetime

DATABASE_PATH = 'attendance_system.db'

def create_backup():
    """Create a backup before cleanup"""
    import shutil
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"attendance_system_backup_legacy_cleanup_{timestamp}.db"
    shutil.copy2(DATABASE_PATH, backup_path)
    print(f"✅ Backup created: {backup_path}")
    return backup_path

def remove_legacy_tables():
    """Remove remaining legacy tables"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Legacy tables to remove (these have enhanced versions)
    legacy_tables = [
        'student_profiles',  # -> student_profiles_enhanced
        'user_accounts',     # -> user_accounts_enhanced  
        'subjects',          # -> subjects_enhanced
        'professor_profiles', # Empty
        'professor_subject_assignments', # Empty
        'login_logs'         # Not needed
    ]
    
    removed_count = 0
    
    for table in legacy_tables:
        try:
            # Check if table exists and show its content
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if cursor.fetchone():
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                
                if count > 0:
                    print(f"⚠️ Removing {table} (had {count} rows)")
                else:
                    print(f"✅ Removing empty table {table}")
                
                cursor.execute(f"DROP TABLE {table}")
                removed_count += 1
            else:
                print(f"ℹ️ Table {table} doesn't exist")
                
        except Exception as e:
            print(f"❌ Failed to remove {table}: {e}")
    
    conn.commit()
    conn.close()
    
    return removed_count

def verify_database():
    """Verify the database is in good state after cleanup"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    print("\n📊 Final Database State:")
    print("========================")
    
    # Check essential tables
    essential_tables = [
        'student_profiles_enhanced',
        'user_accounts_enhanced',
        'subjects_enhanced',
        'attendance_records_enhanced',
        'departments',
        'academic_terms',
        'student_enrollments',
        'facial_embeddings'
    ]
    
    for table in essential_tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"✅ {table}: {count} rows")
    
    # Verify registration functionality
    print("\n🔍 Registration Verification:")
    print("=============================")
    
    # Check latest registered student
    cursor.execute("""
        SELECT sp.name, ua.username, ua.role 
        FROM student_profiles_enhanced sp
        JOIN user_accounts_enhanced ua ON sp.student_id = ua.student_id
        ORDER BY sp.created_at DESC LIMIT 1
    """)
    
    latest = cursor.fetchone()
    if latest:
        print(f"✅ Latest student: {latest[0]} (username: {latest[1]}, role: {latest[2]})")
    
    # Check profile-account consistency
    cursor.execute("SELECT COUNT(*) FROM student_profiles_enhanced")
    profile_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM user_accounts_enhanced WHERE role='student'")
    account_count = cursor.fetchone()[0]
    
    print(f"✅ Profile-Account consistency: {profile_count} profiles, {account_count} accounts")
    
    if profile_count == account_count:
        print("✅ Perfect consistency!")
    else:
        print("⚠️ Inconsistency detected!")
    
    conn.close()

def main():
    """Main cleanup function"""
    print("🧹 Final Legacy Table Cleanup")
    print("=============================")
    print("This will remove remaining legacy tables that have enhanced versions.")
    
    response = input("Proceed with cleanup? (y/N): ").lower().strip()
    if response != 'y':
        print("❌ Cleanup cancelled")
        return
    
    try:
        # Create backup
        backup_path = create_backup()
        
        # Remove legacy tables
        print("\n🗑️ Removing legacy tables...")
        removed_count = remove_legacy_tables()
        
        # Verify database
        verify_database()
        
        print(f"\n🎉 Cleanup completed!")
        print(f"✅ Removed {removed_count} legacy tables")
        print(f"✅ Backup saved: {backup_path}")
        print("✅ Database is now clean and consistent")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
