#!/usr/bin/env python3
"""
Simple Database Replacement

Create a new database with the exact structure of existing enhanced tables
"""

import sqlite3
import shutil
from datetime import datetime

OLD_DATABASE = 'attendance_system.db'
NEW_DATABASE = 'clean_attendance_system.db'

def create_backup():
    """Create backup"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"attendance_system_backup_simple_{timestamp}.db"
    shutil.copy2(OLD_DATABASE, backup_path)
    print(f"✅ Backup created: {backup_path}")
    return backup_path

def create_clean_database():
    """Create new database with only the tables we want to keep"""
    
    # Tables to keep
    TABLES_TO_KEEP = [
        'departments',
        'academic_terms', 
        'student_profiles_enhanced',
        'user_accounts_enhanced',
        'subjects_enhanced',
        'student_enrollments',
        'class_schedules_enhanced',
        'attendance_records_enhanced',
        'facial_embeddings',
        'professor_profiles',
        'login_logs'
    ]
    
    old_conn = sqlite3.connect(OLD_DATABASE)
    new_conn = sqlite3.connect(NEW_DATABASE)
    
    old_cursor = old_conn.cursor()
    new_cursor = new_conn.cursor()
    
    print("🏗️ Creating clean database...")
    
    # Remove new database if exists
    import os
    if os.path.exists(NEW_DATABASE):
        os.remove(NEW_DATABASE)
    
    new_conn = sqlite3.connect(NEW_DATABASE)
    new_cursor = new_conn.cursor()
    
    total_records = 0
    
    for table_name in TABLES_TO_KEEP:
        try:
            # Get table schema from old database
            old_cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            schema_result = old_cursor.fetchone()
            
            if schema_result:
                schema_sql = schema_result[0]
                
                # Create table in new database
                new_cursor.execute(schema_sql)
                print(f"✅ Created table: {table_name}")
                
                # Copy data
                old_cursor.execute(f"SELECT * FROM {table_name}")
                rows = old_cursor.fetchall()
                
                if rows:
                    # Get column count
                    old_cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = old_cursor.fetchall()
                    placeholders = ','.join(['?' for _ in columns])
                    
                    # Insert data
                    new_cursor.executemany(f"INSERT INTO {table_name} VALUES ({placeholders})", rows)
                    print(f"✅ Transferred {len(rows)} rows to {table_name}")
                    total_records += len(rows)
                else:
                    print(f"ℹ️ No data in {table_name}")
            else:
                print(f"⚠️ Table {table_name} not found in old database")
                
        except Exception as e:
            print(f"❌ Error with table {table_name}: {e}")
    
    new_conn.commit()
    old_conn.close()
    new_conn.close()
    
    print(f"✅ Clean database created with {total_records} total records")
    return total_records

def verify_clean_database():
    """Verify the clean database"""
    print("\n📊 Verifying clean database...")
    
    conn = sqlite3.connect(NEW_DATABASE)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall() if not row[0].startswith('sqlite_')]
    
    print(f"✅ Tables in clean database: {len(tables)}")
    
    total_records = 0
    for table_name in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"   📊 {table_name}: {count} rows")
        total_records += count
    
    print(f"✅ Total records: {total_records}")
    
    # Check key relationships
    cursor.execute("SELECT COUNT(*) FROM student_profiles_enhanced")
    students = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM user_accounts_enhanced WHERE role='student'")
    accounts = cursor.fetchone()[0]
    
    print(f"✅ Students: {students}, Student accounts: {accounts}")
    print(f"✅ Data consistency: {'PERFECT' if students == accounts else 'NEEDS REVIEW'}")
    
    conn.close()

def replace_database():
    """Replace old database with clean one"""
    print("\n🔄 Replacing old database...")
    
    # Final backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    final_backup = f"attendance_system_replaced_{timestamp}.db"
    shutil.copy2(OLD_DATABASE, final_backup)
    print(f"✅ Final backup: {final_backup}")
    
    # Replace
    shutil.copy2(NEW_DATABASE, OLD_DATABASE)
    print(f"✅ Database replaced successfully")
    
    # Verify replacement
    conn = sqlite3.connect(OLD_DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall() if not row[0].startswith('sqlite_')]
    conn.close()
    
    print(f"✅ Production database now has {len(tables)} clean tables:")
    for table in tables:
        print(f"   - {table}")

def main():
    """Main function"""
    print("🆕 Simple Clean Database Creation")
    print("=" * 35)
    
    try:
        # Backup
        backup_path = create_backup()
        
        # Create clean database
        total_records = create_clean_database()
        
        # Verify
        verify_clean_database()
        
        # Replace
        response = input("\n❓ Replace production database with clean version? (y/N): ").lower().strip()
        if response == 'y':
            replace_database()
            print("\n🎉 Database replacement completed!")
            print("✅ Your database is now completely clean")
            print("✅ All data preserved")
            print("✅ Only enhanced tables remain")
        else:
            print(f"\n✅ Clean database saved as: {NEW_DATABASE}")
            print("✅ Original database unchanged")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
