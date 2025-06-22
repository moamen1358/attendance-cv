#!/usr/bin/env python3
"""
Final Database Cleanup - Remove ALL Old Tables and Keep Only What's Used

This script will:
1. Remove all old tables that have enhanced versions
2. Remove empty/unused tables
3. Keep only the tables you actually use
"""

import sqlite3
from datetime import datetime
import shutil

DATABASE_PATH = 'attendance_system.db'

def create_backup():
    """Create a backup before cleanup"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"attendance_system_final_cleanup_{timestamp}.db"
    shutil.copy2(DATABASE_PATH, backup_path)
    print(f"✅ Backup created: {backup_path}")
    return backup_path

def get_all_tables_with_counts():
    """Get all tables with their row counts"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row[0] for row in cursor.fetchall()]
    
    table_info = []
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            table_info.append({'name': table, 'count': count})
        except Exception as e:
            table_info.append({'name': table, 'count': f'Error: {e}'})
    
    conn.close()
    return table_info

def remove_old_and_unused_tables():
    """Remove old tables and unused tables"""
    
    # Tables to KEEP (the ones you actually use)
    TABLES_TO_KEEP = [
        # Enhanced tables (main data)
        'student_profiles_enhanced',
        'user_accounts_enhanced', 
        'subjects_enhanced',
        'attendance_records_enhanced',
        'class_schedules_enhanced',
        
        # Core system tables
        'departments',
        'academic_terms',
        'student_enrollments',
        'facial_embeddings',
        
        # Operational tables
        'login_logs',
        'professor_profiles',
    ]
    
    # Get all current tables
    table_info = get_all_tables_with_counts()
    
    print("📋 Current Database Tables:")
    print("=" * 60)
    
    tables_to_remove = []
    tables_to_keep = []
    
    for table in table_info:
        name = table['name']
        count = table['count']
        
        if name in TABLES_TO_KEEP:
            tables_to_keep.append(table)
            print(f"✅ KEEP    {name:35} ({count} rows)")
        else:
            tables_to_remove.append(table)
            print(f"🗑️ REMOVE  {name:35} ({count} rows)")
    
    print(f"\n📊 Summary:")
    print(f"✅ Tables to keep: {len(tables_to_keep)}")
    print(f"🗑️ Tables to remove: {len(tables_to_remove)}")
    
    if not tables_to_remove:
        print("\nℹ️ No tables to remove!")
        return 0
    
    print(f"\n⚠️ This will remove {len(tables_to_remove)} tables:")
    for table in tables_to_remove:
        print(f"   - {table['name']} ({table['count']} rows)")
    
    response = input(f"\n❓ Are you sure you want to remove these {len(tables_to_remove)} tables? (y/N): ").lower().strip()
    
    if response != 'y':
        print("❌ Operation cancelled")
        return 0
    
    # Remove the tables
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    removed_count = 0
    
    for table in tables_to_remove:
        table_name = table['name']
        try:
            cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            print(f"✅ Removed: {table_name}")
            removed_count += 1
        except Exception as e:
            print(f"❌ Failed to remove {table_name}: {e}")
    
    conn.commit()
    conn.close()
    
    return removed_count

def verify_final_database():
    """Verify the final database state"""
    print("\n📊 Final Database State:")
    print("=" * 40)
    
    table_info = get_all_tables_with_counts()
    
    if not table_info:
        print("❌ No tables found!")
        return
    
    total_records = 0
    for table in sorted(table_info, key=lambda x: x['name']):
        name = table['name']
        count = table['count']
        print(f"✅ {name:35} {count:>6} rows")
        if isinstance(count, int):
            total_records += count
    
    print(f"\n📈 Database Summary:")
    print(f"✅ Total tables: {len(table_info)}")
    print(f"✅ Total records: {total_records:,}")
    
    # Check for key functionality
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # Check student registration capability
        cursor.execute("SELECT COUNT(*) FROM student_profiles_enhanced")
        students = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM user_accounts_enhanced WHERE role='student'")
        accounts = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM subjects_enhanced")
        subjects = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM facial_embeddings")
        embeddings = cursor.fetchone()[0]
        
        print(f"\n🎯 System Health Check:")
        print(f"✅ Students: {students}")
        print(f"✅ Login accounts: {accounts}")
        print(f"✅ Subjects: {subjects}")
        print(f"✅ Face embeddings: {embeddings}")
        
        if students == accounts:
            print("✅ Student-Account consistency: PERFECT")
        else:
            print("⚠️ Student-Account consistency: MISMATCH")
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")
    finally:
        conn.close()

def main():
    """Main cleanup function"""
    print("🧹 Final Database Cleanup")
    print("Remove old tables and keep only what you use")
    print("=" * 50)
    
    try:
        # Create backup
        backup_path = create_backup()
        
        # Remove old and unused tables
        removed_count = remove_old_and_unused_tables()
        
        if removed_count > 0:
            # Verify final state
            verify_final_database()
            
            print(f"\n🎉 Final cleanup completed!")
            print(f"✅ Removed {removed_count} tables")
            print(f"✅ Database is now clean and optimized")
            print(f"✅ Backup saved: {backup_path}")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
