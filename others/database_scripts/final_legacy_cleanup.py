#!/usr/bin/env python3
"""
Final cleanup to remove ALL legacy tables and ensure only enhanced tables remain
"""

import sqlite3
import os

def main():
    db_path = "attendance_system.db"
    
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found!")
        return
    
    # Create backup first
    backup_path = f"attendance_system_backup_before_final_cleanup.db"
    os.system(f"cp {db_path} {backup_path}")
    print(f"Created backup: {backup_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all current tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    all_tables = [row[0] for row in cursor.fetchall()]
    print(f"Current tables: {all_tables}")
    
    # Define legacy tables to remove
    legacy_tables = [
        'student_profiles',          # Legacy, keep only student_profiles_enhanced
        'user_accounts',             # Legacy, keep only user_accounts_enhanced
        'subjects',                  # Legacy, keep only subjects_enhanced
        'attendance_records',        # Legacy, keep only attendance_records_enhanced
        'class_schedules',           # Legacy, keep only class_schedules_enhanced
        'attendance_with_names',     # View/legacy table
        'class_attendance',          # View/legacy table
        'subjects_compatible',       # Legacy compatibility table
        'teacher_subjects',          # Legacy table
        'professor_assignments_view', # View
        'student_profiles_view',     # View
        'professor_subject_assignments' # Legacy table
    ]
    
    # Define tables to keep (enhanced + core system tables)
    tables_to_keep = [
        'student_profiles_enhanced',
        'user_accounts_enhanced', 
        'subjects_enhanced',
        'attendance_records_enhanced',
        'class_schedules_enhanced',
        'departments',
        'professor_profiles',
        'facial_embeddings',
        'login_logs',
        'student_enrollments',
        'academic_terms'
    ]
    
    # Remove legacy tables
    removed_tables = []
    for table in legacy_tables:
        if table in all_tables:
            try:
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
                removed_tables.append(table)
                print(f"✓ Removed legacy table: {table}")
            except Exception as e:
                print(f"✗ Failed to remove {table}: {e}")
    
    # Remove any views that might exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='view'")
    views = [row[0] for row in cursor.fetchall()]
    for view in views:
        try:
            cursor.execute(f"DROP VIEW IF EXISTS {view}")
            print(f"✓ Removed view: {view}")
        except Exception as e:
            print(f"✗ Failed to remove view {view}: {e}")
    
    conn.commit()
    
    # Final verification
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    final_tables = [row[0] for row in cursor.fetchall()]
    print(f"\nFinal tables remaining: {final_tables}")
    
    # Check if we have only the expected tables
    unexpected_tables = [t for t in final_tables if t not in tables_to_keep]
    missing_tables = [t for t in tables_to_keep if t not in final_tables]
    
    if unexpected_tables:
        print(f"⚠️  Unexpected tables still present: {unexpected_tables}")
    
    if missing_tables:
        print(f"⚠️  Expected tables missing: {missing_tables}")
    
    if not unexpected_tables and not missing_tables:
        print("✅ Database cleanup successful! Only enhanced tables remain.")
    
    # Show table counts
    print("\nTable record counts:")
    for table in final_tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  {table}: {count} records")
        except Exception as e:
            print(f"  {table}: Error counting - {e}")
    
    conn.close()
    print(f"\nRemoved {len(removed_tables)} legacy tables: {removed_tables}")
    print("Final cleanup complete!")

if __name__ == "__main__":
    main()
