#!/usr/bin/env python3
"""
Example: How to Use Centralized Database Initialization

This script demonstrates the proper way to initialize the database
in any new module or application entry point.
"""

import sys
import os

# Add the src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def main():
    print("=== Centralized Database Initialization Example ===")
    
    # Step 1: Import the centralized initialization functions
    try:
        from db_init import initialize_database, check_database_integrity, get_table_info
        print("✅ Successfully imported centralized database functions")
    except ImportError as e:
        print(f"❌ Failed to import database functions: {e}")
        return False
    
    # Step 2: Initialize the database (creates all required tables)
    print("\n🔧 Initializing database...")
    success = initialize_database()
    
    if not success:
        print("❌ Database initialization failed!")
        return False
    
    print("✅ Database initialization completed successfully")
    
    # Step 3: Check database integrity (optional but recommended)
    print("\n🔍 Checking database integrity...")
    integrity_ok = check_database_integrity()
    
    if not integrity_ok:
        print("⚠️  Database integrity check failed")
        return False
    
    print("✅ Database integrity check passed")
    
    # Step 4: Verify specific tables exist (example)
    print("\n📋 Verifying key tables...")
    key_tables = ['students_enhanced', 'subjects_enhanced', 'teachers_enhanced']
    
    for table in key_tables:
        columns = get_table_info(table)
        if columns:
            print(f"✅ {table}: {len(columns)} columns")
        else:
            print(f"❌ {table}: Not found")
            return False
    
    print("\n🎉 All checks passed! Database is ready for use.")
    
    # Step 5: Your application logic would go here
    print("\n💡 Your application can now safely use the database.")
    print("   All tables are guaranteed to exist with the correct schema.")
    
    return True

def example_usage_in_module():
    """
    Example of how to use centralized initialization in any module
    """
    print("\n=== Example: Module-Level Usage ===")
    
    # This is how you would typically use it in a real module
    from db_init import initialize_database
    
    # Initialize database at module startup (if not already done)
    if not hasattr(example_usage_in_module, '_db_initialized'):
        print("Initializing database for this module...")
        success = initialize_database()
        example_usage_in_module._db_initialized = success
        
        if success:
            print("✅ Module database initialization complete")
        else:
            print("❌ Module database initialization failed")
    
    # Now you can safely use the database
    print("🔓 Database is ready - you can now run queries against enhanced tables")

if __name__ == "__main__":
    print("Centralized Database Initialization Example")
    print("=" * 50)
    
    # Run the main example
    success = main()
    
    if success:
        # Show module-level usage example
        example_usage_in_module()
        
        print("\n" + "=" * 50)
        print("🎯 Summary:")
        print("   1. Import from db_init: initialize_database, check_database_integrity")
        print("   2. Call initialize_database() once at startup")
        print("   3. Optionally call check_database_integrity() for verification")
        print("   4. Use the enhanced tables in your queries")
        print("   5. All table creation is now centralized and consistent!")
    else:
        print("\n❌ Example failed - please check the database setup")
