#!/usr/bin/env python3
"""
Database Cleanup Script

This script removes unused tables from the attendance_system database
while preserving all active data and essential tables.
"""

import sqlite3
import os

DATABASE_PATH = 'attendance_system.db'

def create_backup():
    """Create a backup of the database before cleanup"""
    import shutil
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"attendance_system_backup_before_cleanup_{timestamp}.db"
    
    shutil.copy2(DATABASE_PATH, backup_path)
    print(f"✅ Database backup created: {backup_path}")
    return backup_path

def get_table_info():
    """Get information about all tables"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    all_tables = [row[0] for row in cursor.fetchall()]
    
    # Check which tables have data
    tables_with_data = []
    empty_tables = []
    view_tables = []
    
    for table in all_tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            if count > 0:
                tables_with_data.append((table, count))
            else:
                empty_tables.append(table)
        except Exception as e:
            # Might be a view or corrupted table
            view_tables.append(table)
    
    conn.close()
    return tables_with_data, empty_tables, view_tables

def remove_unused_tables():
    """Remove unused tables from the database"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Tables that are definitely unused and can be safely removed
    unused_tables = [
        # Legacy tables that have been replaced by enhanced versions
        'subjects',  # Replaced by subjects_enhanced
        'attendance_records',  # Replaced by attendance_records_enhanced
        'class_schedules',  # Replaced by class_schedules_enhanced
        'user_accounts',  # Keep this as it might have legacy admin users
        
        # Empty legacy tables
        'professor_profiles',  # Empty
        'class_attendance',  # Empty
        'login_logs',  # Empty
        'teacher_subjects',  # Empty
        'students',  # Empty - legacy table
        'presidents_embeds',  # Empty - facial data moved to facial_embeddings
        'professor_subject_assignments',  # Empty
        'courses',  # Empty
        'subjects_new',  # Empty
        'classes',  # Empty
        'student_classes',  # Empty
        'attendance_sessions',  # Empty
        'attendance_records_new',  # Empty
        'attendance_log',  # Empty - legacy table
        'facial_recognition_data',  # Empty
        
        # Views that might be orphaned (we'll recreate needed ones)
        'attendance_name_view',
        'attendance_records_compat',
        'attendance_records_view',
        'attendance_unified',
        'attendance_unified_view',
        'attendance_with_names',
        'current_students',
        'professor_assignments_view',
        'professor_teaching_schedule',
        'student_complete_profile',
        'student_name_mapping',
        'student_profiles_compat',
        'student_profiles_view',
        'subjects_compat',
        'subjects_compatible',
        'unified_attendance',
        'unified_attendance_summary',
        'unified_students',
        'v_attendance_summary',
        'v_class_rosters',
        'v_professor_teaching_load',
        'v_student_attendance_summary',
        'v_student_dashboard',
        'v_student_enrollments',
        'v_subject_enrollment'
    ]
    
    # Keep essential tables with data
    essential_tables = [
        'academic_terms',
        'departments', 
        'subjects_enhanced',
        'student_profiles_enhanced',
        'student_enrollments',
        'user_accounts_enhanced',
        'class_schedules_enhanced',
        'attendance_records_enhanced',
        'facial_embeddings',
        'student_profiles'  # Keep this as it has some data
    ]
    
    removed_count = 0
    failed_removals = []
    
    for table in unused_tables:
        try:
            # Check if table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
            if cursor.fetchone():
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
                print(f"✅ Removed table: {table}")
                removed_count += 1
            else:
                # Check if it's a view
                cursor.execute("SELECT name FROM sqlite_master WHERE type='view' AND name=?", (table,))
                if cursor.fetchone():
                    cursor.execute(f"DROP VIEW IF EXISTS {table}")
                    print(f"✅ Removed view: {table}")
                    removed_count += 1
        except Exception as e:
            print(f"❌ Failed to remove {table}: {e}")
            failed_removals.append((table, str(e)))
    
    conn.commit()
    conn.close()
    
    return removed_count, failed_removals

def create_essential_views():
    """Create essential views for compatibility"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Create compatibility views for the application
    views_to_create = [
        # Attendance records compatibility view
        ("attendance_records_compat", """
            CREATE VIEW IF NOT EXISTS attendance_records_compat AS
            SELECT 
                ar.attendance_id as id,
                sp.username as student_username,
                sp.name,
                ar.subject_id,
                ar.check_in_time as timestamp,
                ar.status,
                ar.attendance_date as class_date,
                sp.name as student_name,
                sp.username,
                ar.confidence_score as confidence,
                'facial_recognition' as device_id,
                CAST(strftime('%w', ar.attendance_date) AS INTEGER) as day_of_week
            FROM attendance_records_enhanced ar
            JOIN student_profiles_enhanced sp ON ar.student_id = sp.student_id
        """),
        
        # Student profiles compatibility view
        ("student_profiles_compat", """
            CREATE VIEW IF NOT EXISTS student_profiles_compat AS
            SELECT 
                student_id as id,
                username,
                name,
                student_number as student_id,
                email,
                phone,
                CASE 
                    WHEN current_semester = 1 THEN 'Section A'
                    WHEN current_semester = 2 THEN 'Section B'
                    ELSE 'Section A'
                END as section,
                created_at,
                academic_year,
                current_semester
            FROM student_profiles_enhanced
        """),
        
        # Subjects compatibility view
        ("subjects_compat", """
            CREATE VIEW IF NOT EXISTS subjects_compat AS
            SELECT 
                subject_id as id,
                subject_name as name,
                description,
                subject_code as course_code,
                credits as credit_hours,
                created_at
            FROM subjects_enhanced
        """)
    ]
    
    created_views = 0
    for view_name, view_sql in views_to_create:
        try:
            cursor.execute(view_sql)
            print(f"✅ Created view: {view_name}")
            created_views += 1
        except Exception as e:
            print(f"❌ Failed to create view {view_name}: {e}")
    
    conn.commit()
    conn.close()
    
    return created_views

def vacuum_database():
    """Vacuum the database to reclaim space"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("VACUUM")
        print("✅ Database vacuumed successfully")
    except Exception as e:
        print(f"❌ Failed to vacuum database: {e}")
    finally:
        conn.close()

def main():
    """Main cleanup function"""
    print("🧹 Starting Database Cleanup...")
    print("⚠️ This will remove unused tables and views from the database")
    
    # Ask for confirmation
    response = input("Do you want to proceed? (y/N): ").lower().strip()
    if response != 'y':
        print("❌ Cleanup cancelled")
        return
    
    try:
        # Step 1: Create backup
        print("\n📝 Step 1: Creating backup...")
        backup_path = create_backup()
        
        # Step 2: Analyze current state
        print("\n📝 Step 2: Analyzing database...")
        tables_with_data, empty_tables, view_tables = get_table_info()
        
        print(f"Tables with data: {len(tables_with_data)}")
        print(f"Empty tables: {len(empty_tables)}")
        print(f"Views/Other: {len(view_tables)}")
        
        # Step 3: Remove unused tables
        print("\n📝 Step 3: Removing unused tables...")
        removed_count, failed_removals = remove_unused_tables()
        
        # Step 4: Create essential views
        print("\n📝 Step 4: Creating essential compatibility views...")
        created_views = create_essential_views()
        
        # Step 5: Vacuum database
        print("\n📝 Step 5: Optimizing database...")
        vacuum_database()
        
        # Step 6: Final report
        print("\n🎉 Database cleanup completed!")
        print(f"✅ Backup created: {backup_path}")
        print(f"✅ Removed {removed_count} unused tables/views")
        print(f"✅ Created {created_views} compatibility views")
        
        if failed_removals:
            print(f"⚠️ {len(failed_removals)} items failed to remove:")
            for item, error in failed_removals:
                print(f"  - {item}: {error}")
        
        # Show final table count
        print("\n📊 Final Summary:")
        tables_with_data, empty_tables, view_tables = get_table_info()
        print(f"Active tables: {len(tables_with_data)}")
        print(f"Empty tables remaining: {len(empty_tables)}")
        
        print("\nActive tables:")
        for table, count in tables_with_data:
            print(f"  - {table}: {count} rows")
            
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
