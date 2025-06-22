#!/usr/bin/env python3
"""
Test script to verify that the centralized database initialization works correctly
and that all CREATE TABLE statements have been removed from active code.
"""

import sys
import os
sys.path.append('/home/invisa/Desktop/my_grad_streamlit/src')

from db_init import initialize_database, check_database_integrity, get_table_info

def test_database_initialization():
    """Test the centralized database initialization"""
    print("=== Testing Centralized Database Initialization ===")
    
    # Test 1: Initialize database
    print("\n1. Testing database initialization...")
    success = initialize_database()
    if success:
        print("✅ Database initialization successful")
    else:
        print("❌ Database initialization failed")
        return False
    
    # Test 2: Check database integrity
    print("\n2. Testing database integrity check...")
    integrity_ok = check_database_integrity()
    if integrity_ok:
        print("✅ Database integrity check passed")
    else:
        print("❌ Database integrity check failed")
        return False
    
    # Test 3: Verify enhanced tables exist
    print("\n3. Verifying enhanced tables exist...")
    enhanced_tables = [
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
    
    for table in enhanced_tables:
        columns = get_table_info(table)
        if columns:
            print(f"✅ {table} exists with {len(columns)} columns")
        else:
            print(f"❌ {table} does not exist")
            return False
    
    print("\n=== All tests passed! ===")
    return True

def search_for_active_create_tables():
    """Search for any remaining active CREATE TABLE statements in the codebase"""
    print("\n=== Searching for Active CREATE TABLE Statements ===")
    
    import subprocess
    import re
    
    # Search for CREATE TABLE statements in Python files
    try:
        result = subprocess.run([
            'grep', '-r', '-n', '--include=*.py', 'CREATE TABLE', 
            '/home/invisa/Desktop/my_grad_streamlit/src/'
        ], capture_output=True, text=True)
        
        lines = result.stdout.strip().split('\n') if result.stdout.strip() else []
        
        active_creates = []
        for line in lines:
            # Skip commented lines and the db_init.py file
            if ('# CREATE TABLE' not in line and 
                '#CREATE TABLE' not in line and
                'db_init.py' not in line and
                'CREATE TABLE' in line):
                active_creates.append(line)
        
        if active_creates:
            print("⚠️  Found active CREATE TABLE statements:")
            for line in active_creates:
                print(f"  {line}")
            return False
        else:
            print("✅ No active CREATE TABLE statements found outside db_init.py")
            return True
            
    except Exception as e:
        print(f"Error searching for CREATE TABLE statements: {e}")
        return False

if __name__ == "__main__":
    print("Database Centralization Test Script")
    print("="*50)
    
    # Test database initialization
    init_success = test_database_initialization()
    
    # Search for any remaining active CREATE statements
    no_active_creates = search_for_active_create_tables()
    
    # Overall result
    print("\n" + "="*50)
    if init_success and no_active_creates:
        print("🎉 SUCCESS: Database centralization complete!")
        print("   - All enhanced tables created successfully")
        print("   - No active CREATE TABLE statements found in code")
        print("   - All modules should now use db_init.py for initialization")
    else:
        print("❌ ISSUES FOUND:")
        if not init_success:
            print("   - Database initialization or integrity check failed")
        if not no_active_creates:
            print("   - Active CREATE TABLE statements still exist in code")
        print("   - Review the output above for details")
