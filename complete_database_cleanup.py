#!/usr/bin/env python3
"""
Complete Database Cleanup - Remove ALL Old Tables, Views, and Compatibility Layers

This script removes everything except the core enhanced tables you actually use.
"""

import sqlite3
from datetime import datetime
import shutil

DATABASE_PATH = 'attendance_system.db'

def create_backup():
    """Create a backup before cleanup"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"attendance_system_complete_cleanup_{timestamp}.db"
    shutil.copy2(DATABASE_PATH, backup_path)
    print(f"✅ Backup created: {backup_path}")
    return backup_path

def get_all_database_objects():
    """Get all tables, views, triggers, and indexes"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Get all database objects
    cursor.execute("""
        SELECT type, name 
        FROM sqlite_master 
        WHERE name NOT LIKE 'sqlite_%' 
        ORDER BY type, name
    """)
    
    objects = cursor.fetchall()
    conn.close()
    return objects

def complete_cleanup():
    """Remove everything except essential enhanced tables"""
    
    # ONLY keep these essential tables
    ESSENTIAL_TABLES = {
        'student_profiles_enhanced',
        'user_accounts_enhanced', 
        'subjects_enhanced',
        'attendance_records_enhanced',
        'class_schedules_enhanced',
        'departments',
        'academic_terms',
        'student_enrollments',
        'facial_embeddings',
        'login_logs',
        'professor_profiles'
    }
    
    # Get all database objects
    objects = get_all_database_objects()
    
    print("📋 Current Database Objects:")
    print("=" * 60)
    
    to_keep = []
    to_remove = []
    
    for obj_type, obj_name in objects:
        if obj_name in ESSENTIAL_TABLES:
            to_keep.append((obj_type, obj_name))
            print(f"✅ KEEP    {obj_type:8} {obj_name}")
        else:
            to_remove.append((obj_type, obj_name))
            print(f"🗑️ REMOVE  {obj_type:8} {obj_name}")
    
    print(f"\n📊 Summary:")
    print(f"✅ Objects to keep: {len(to_keep)}")
    print(f"🗑️ Objects to remove: {len(to_remove)}")
    
    if not to_remove:
        print("\nℹ️ No objects to remove!")
        return 0
    
    print(f"\n⚠️ This will remove {len(to_remove)} database objects:")
    for obj_type, obj_name in to_remove:
        print(f"   - {obj_type}: {obj_name}")
    
    response = input(f"\n❓ Remove these {len(to_remove)} objects? (y/N): ").lower().strip()
    
    if response != 'y':
        print("❌ Operation cancelled")
        return 0
    
    # Remove the objects
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    removed_count = 0
    
    # Remove in specific order: triggers, views, then tables
    object_types_order = ['trigger', 'view', 'table', 'index']
    
    for obj_type in object_types_order:
        for remove_type, remove_name in to_remove:
            if remove_type == obj_type:
                try:
                    if obj_type == 'table':
                        cursor.execute(f"DROP TABLE IF EXISTS {remove_name}")
                    elif obj_type == 'view':
                        cursor.execute(f"DROP VIEW IF EXISTS {remove_name}")
                    elif obj_type == 'trigger':
                        cursor.execute(f"DROP TRIGGER IF EXISTS {remove_name}")
                    elif obj_type == 'index':
                        cursor.execute(f"DROP INDEX IF EXISTS {remove_name}")
                    
                    print(f"✅ Removed {obj_type}: {remove_name}")
                    removed_count += 1
                except Exception as e:
                    print(f"❌ Failed to remove {obj_type} {remove_name}: {e}")
    
    conn.commit()
    conn.close()
    
    return removed_count

def verify_clean_database():
    """Verify the final clean database"""
    print("\n📊 Final Clean Database:")
    print("=" * 40)
    
    objects = get_all_database_objects()
    
    if not objects:
        print("❌ No objects found!")
        return
    
    # Count records in each table
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    total_records = 0
    
    for obj_type, obj_name in sorted(objects):
        if obj_type == 'table':
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {obj_name}")
                count = cursor.fetchone()[0]
                print(f"✅ {obj_name:35} {count:>6} rows")
                total_records += count
            except Exception as e:
                print(f"❌ {obj_name:35} Error: {e}")
        else:
            print(f"ℹ️ {obj_type:8} {obj_name}")
    
    conn.close()
    
    print(f"\n📈 Clean Database Summary:")
    print(f"✅ Total objects: {len(objects)}")
    print(f"✅ Total records: {total_records:,}")
    print("✅ Database is now completely clean!")

def main():
    """Main cleanup function"""
    print("🧹 Complete Database Cleanup")
    print("Remove ALL old tables, views, and compatibility layers")
    print("=" * 55)
    
    try:
        # Create backup
        backup_path = create_backup()
        
        # Complete cleanup
        removed_count = complete_cleanup()
        
        if removed_count > 0:
            # Verify final state
            verify_clean_database()
            
            print(f"\n🎉 Complete cleanup finished!")
            print(f"✅ Removed {removed_count} database objects")
            print(f"✅ Database is now completely clean")
            print(f"✅ Backup saved: {backup_path}")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
