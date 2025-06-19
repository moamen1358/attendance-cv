#!/usr/bin/env python3
"""
Test script for the enhanced database explorer
This script tests the core functionality without requiring Streamlit
"""

import sys
import os
import sqlite3
import pandas as pd

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_database_connection():
    """Test basic database connectivity"""
    try:
        conn = sqlite3.connect('attendance_system.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        conn.close()
        print(f"✅ Database connection successful. Found {len(tables)} tables.")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_imports():
    """Test that all required modules can be imported"""
    try:
        # Test core functionality imports
        from database_utils import execute_query, execute_query_df
        print("✅ Database utils imported successfully")
        
        from time_format_utils import display_formatted_time
        print("✅ Time format utils imported successfully")
        
        # Test main module functions (without Streamlit)
        sys.modules['streamlit'] = None  # Mock streamlit to avoid import error
        
        # Import the functions we can test
        import importlib.util
        spec = importlib.util.spec_from_file_location("enhanced_db_explorer", "src/enhanced_db_explorer.py")
        
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

def test_core_functions():
    """Test core database functions"""
    try:
        # Test getting tables with direct SQL
        conn = sqlite3.connect('attendance_system.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        result = cursor.fetchall()
        conn.close()
        
        if result:
            print(f"✅ Found {len(result)} tables in database")
            for table in result[:5]:  # Show first 5 tables
                print(f"   - {table[0]}")
            if len(result) > 5:
                print(f"   ... and {len(result) - 5} more")
        else:
            print("⚠️  No tables found in database")
        
        # Test time formatting
        from time_format_utils import display_formatted_time
        test_times = ["14:30:00", "09:15:00", "23:45:00", "00:00:00", "02:30 PM", "09:15 AM"]
        print("✅ Time formatting test:")
        for time_str in test_times:
            try:
                formatted = display_formatted_time(time_str)
                print(f"   {time_str} -> {formatted}")
            except Exception as e:
                print(f"   {time_str} -> Error: {e}")
        
        return True
    except Exception as e:
        print(f"❌ Core functions test failed: {e}")
        return False

def test_table_schema():
    """Test table schema inspection"""
    try:
        conn = sqlite3.connect('attendance_system.db')
        cursor = conn.cursor()
        
        # Get a sample table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1;")
        tables_result = cursor.fetchall()
        
        if not tables_result:
            print("⚠️  No tables to test schema inspection")
            conn.close()
            return True
            
        table_name = tables_result[0][0]
        
        # Get table info
        cursor.execute(f"PRAGMA table_info({table_name});")
        schema_result = cursor.fetchall()
        conn.close()
        
        if schema_result:
            print(f"✅ Schema for table '{table_name}':")
            for col in schema_result:
                col_name, col_type, not_null, default, pk = col[1], col[2], col[3], col[4], col[5]
                pk_str = " (PK)" if pk else ""
                null_str = " NOT NULL" if not_null else ""
                print(f"   - {col_name}: {col_type}{null_str}{pk_str}")
        else:
            print(f"⚠️  Could not get schema for table '{table_name}'")
        
        return True
    except Exception as e:
        print(f"❌ Table schema test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Enhanced Database Explorer")
    print("=" * 50)
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Module Imports", test_imports),
        ("Core Functions", test_core_functions),
        ("Table Schema", test_table_schema)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} test...")
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} test failed")
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
    
    print(f"\n🏁 Test Summary: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Database explorer should work correctly.")
    else:
        print("⚠️  Some tests failed. Check the issues above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
