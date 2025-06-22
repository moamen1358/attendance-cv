#!/usr/bin/env python3
"""
Remove Old Tables That Have Enhanced Versions

This script identifies tables that have enhanced versions and removes the old ones.
"""

import sqlite3
from datetime import datetime
import shutil

DATABASE_PATH = 'attendance_system.db'

def create_backup():
    """Create a backup before cleanup"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"attendance_system_backup_remove_old_{timestamp}.db"
    shutil.copy2(DATABASE_PATH, backup_path)
    print(f"✅ Backup created: {backup_path}")
    return backup_path

def get_all_tables():
    """Get list of all tables in the database"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    return tables

def find_tables_to_remove():
    """Find tables that have enhanced versions"""
    all_tables = get_all_tables()
    
    # Find enhanced tables
    enhanced_tables = [table for table in all_tables if table.endswith('_enhanced')]
    
    # Find corresponding old tables
    tables_to_remove = []
    
    for enhanced_table in enhanced_tables:
        # Get the base name (without _enhanced)
        base_name = enhanced_table.replace('_enhanced', '')
        
        # Check if the old table exists
        if base_name in all_tables:
            # Get row counts
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            cursor.execute(f"SELECT COUNT(*) FROM {base_name}")
            old_count = cursor.fetchone()[0]
            
            cursor.execute(f"SELECT COUNT(*) FROM {enhanced_table}")
            enhanced_count = cursor.fetchone()[0]
            
            conn.close()
            
            tables_to_remove.append({
                'old_table': base_name,
                'enhanced_table': enhanced_table,
                'old_count': old_count,
                'enhanced_count': enhanced_count
            })
    
    return tables_to_remove

def remove_old_tables():
    """Remove old tables that have enhanced versions"""
    tables_to_remove = find_tables_to_remove()
    
    if not tables_to_remove:
        print("ℹ️ No old tables with enhanced versions found")
        return 0
    
    print("📋 Tables to be removed:")
    print("=" * 50)
    for item in tables_to_remove:
        print(f"🗑️ {item['old_table']} ({item['old_count']} rows) -> keeping {item['enhanced_table']} ({item['enhanced_count']} rows)")
    
    print("\n" + "=" * 50)
    response = input("❓ Proceed with removing these old tables? (y/N): ").lower().strip()
    
    if response != 'y':
        print("❌ Operation cancelled")
        return 0
    
    # Remove the tables
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    removed_count = 0
    
    for item in tables_to_remove:
        old_table = item['old_table']
        try:
            cursor.execute(f"DROP TABLE IF EXISTS {old_table}")
            print(f"✅ Removed table: {old_table}")
            removed_count += 1
        except Exception as e:
            print(f"❌ Failed to remove {old_table}: {e}")
    
    conn.commit()
    conn.close()
    
    return removed_count

def verify_database():
    """Verify the database state after cleanup"""
    print("\n📊 Remaining Tables After Cleanup:")
    print("=" * 40)
    
    all_tables = get_all_tables()
    enhanced_tables = []
    other_tables = []
    
    for table in all_tables:
        if table.endswith('_enhanced'):
            enhanced_tables.append(table)
        elif not table.startswith('sqlite_'):
            other_tables.append(table)
    
    print("✅ Enhanced Tables:")
    for table in sorted(enhanced_tables):
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        conn.close()
        print(f"   📊 {table}: {count} rows")
    
    print("\n✅ Other System Tables:")
    for table in sorted(other_tables):
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        conn.close()
        print(f"   📊 {table}: {count} rows")

def main():
    """Main function"""
    print("🧹 Remove Old Tables With Enhanced Versions")
    print("=" * 45)
    
    try:
        # Create backup
        backup_path = create_backup()
        
        # Remove old tables
        print("\n🔍 Scanning for old tables with enhanced versions...")
        removed_count = remove_old_tables()
        
        if removed_count > 0:
            # Verify database
            verify_database()
            
            print(f"\n🎉 Cleanup completed!")
            print(f"✅ Removed {removed_count} old tables")
            print(f"✅ Backup saved: {backup_path}")
            print("✅ Database now uses only enhanced tables")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
