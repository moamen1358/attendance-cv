#!/usr/bin/env python3
"""
Database Centralization Verification Script
Verifies that all CREATE TABLE statements have been removed from active code
and that all files are using the centralized database initialization.
"""

import os
import re
from pathlib import Path

def scan_files_for_create_table():
    """Scan all Python files in src directory for CREATE TABLE statements"""
    
    src_dir = Path('src')
    create_table_files = []
    centralized_import_files = []
    
    print("🔍 SCANNING SRC DIRECTORY FOR DATABASE TABLE CREATION")
    print("=" * 60)
    
    # Pattern to match CREATE TABLE statements (not commented out)
    create_table_pattern = re.compile(r'^\s*CREATE TABLE', re.IGNORECASE | re.MULTILINE)
    
    # Pattern to match centralized imports
    centralized_import_pattern = re.compile(r'from db_init import.*initialize_database', re.IGNORECASE)
    
    for py_file in src_dir.glob('*.py'):
        if py_file.name in ['__pycache__', 'db_init.py'] or 'backup' in py_file.name.lower():  # Skip cache, centralized file, and backup files
            continue
            
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Check for CREATE TABLE statements
            create_matches = create_table_pattern.findall(content)
            if create_matches:
                create_table_files.append({
                    'file': py_file.name,
                    'matches': len(create_matches)
                })
            
            # Check for centralized import
            if centralized_import_pattern.search(content):
                centralized_import_files.append(py_file.name)
                
        except Exception as e:
            print(f"⚠️ Error reading {py_file}: {e}")
    
    # Report results
    print(f"\n📊 SCAN RESULTS:")
    print(f"   Total Python files scanned: {len(list(src_dir.glob('*.py'))) - 1}")  # -1 for db_init.py
    print(f"   Files with CREATE TABLE: {len(create_table_files)}")
    print(f"   Files with centralized import: {len(centralized_import_files)}")
    
    if create_table_files:
        print(f"\n❌ FILES WITH CREATE TABLE STATEMENTS:")
        for file_info in create_table_files:
            print(f"   {file_info['file']}: {file_info['matches']} statements")
    else:
        print(f"\n✅ NO CREATE TABLE STATEMENTS FOUND IN ACTIVE CODE")
    
    print(f"\n📋 FILES USING CENTRALIZED INITIALIZATION:")
    for filename in sorted(centralized_import_files):
        print(f"   ✅ {filename}")
    
    # Check which important files might be missing centralized initialization
    important_files = [
        'app.py', 'login.py', 'student_report.py', 'database_utils.py',
        'subject_management.py', 'professor_subject_assignment.py', 'report.py'
    ]
    
    missing_files = []
    for important_file in important_files:
        if important_file not in centralized_import_files:
            file_path = src_dir / important_file
            if file_path.exists():
                missing_files.append(important_file)
    
    if missing_files:
        print(f"\n⚠️ IMPORTANT FILES NOT USING CENTRALIZED INITIALIZATION:")
        for filename in missing_files:
            print(f"   ⚠️ {filename}")
    else:
        print(f"\n✅ ALL IMPORTANT FILES USING CENTRALIZED INITIALIZATION")
    
    return len(create_table_files) == 0 and len(missing_files) == 0

def check_db_init_completeness():
    """Check if db_init.py contains all necessary tables"""
    
    print(f"\n🏗️ CHECKING DB_INIT.PY COMPLETENESS")
    print("=" * 40)
    
    try:
        with open('src/db_init.py', 'r') as f:
            content = f.read()
        
        # Expected tables for a complete attendance system
        expected_tables = [
            'students_enhanced',
            'subjects_enhanced', 
            'teachers_enhanced',
            'teacher_subjects_enhanced',
            'class_schedules_enhanced',
            'attendance_records_enhanced',
            'student_profiles_enhanced',
            'users_enhanced',
            'attendance_sessions_enhanced',
            'student_enrollments_enhanced'
        ]
        
        found_tables = []
        for table in expected_tables:
            if table in content:
                found_tables.append(table)
        
        print(f"Expected tables: {len(expected_tables)}")
        print(f"Found tables: {len(found_tables)}")
        
        if len(found_tables) == len(expected_tables):
            print("✅ All expected tables found in db_init.py")
            return True
        else:
            missing_tables = set(expected_tables) - set(found_tables)
            print(f"❌ Missing tables: {missing_tables}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking db_init.py: {e}")
        return False

def main():
    """Main verification function"""
    
    print("🎯 DATABASE CENTRALIZATION VERIFICATION")
    print("=" * 50)
    
    # Check current directory
    if not os.path.exists('src'):
        print("❌ src directory not found. Run this script from the project root.")
        return False
    
    # Run checks
    clean_code = scan_files_for_create_table()
    complete_init = check_db_init_completeness()
    
    # Final result
    print(f"\n🏁 FINAL RESULT:")
    print("=" * 20)
    
    if clean_code and complete_init:
        print("✅ DATABASE CENTRALIZATION COMPLETE!")
        print("   • All CREATE TABLE statements removed from active code")
        print("   • All important files using centralized initialization")
        print("   • db_init.py contains all necessary tables")
        return True
    else:
        print("❌ DATABASE CENTRALIZATION INCOMPLETE!")
        if not clean_code:
            print("   • Some files still have CREATE TABLE statements or missing imports")
        if not complete_init:
            print("   • db_init.py is missing some tables")
        return False

if __name__ == "__main__":
    main()
