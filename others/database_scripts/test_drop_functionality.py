#!/usr/bin/env python3
"""
Test script to verify DROP TABLE functionality
"""

import sqlite3
import sys

def test_drop_functionality():
    """Test DROP TABLE operations"""
    
    # Create a test table
    conn = sqlite3.connect('attendance_system.db')
    cursor = conn.cursor()
    
    try:
        # Create test table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_drop_table (
            id INTEGER PRIMARY KEY,
            name TEXT
        )
        """)
        
        # Insert test data
        cursor.execute("INSERT INTO test_drop_table (name) VALUES ('test')")
        conn.commit()
        
        print("✅ Created test table: test_drop_table")
        
        # Verify table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='test_drop_table'")
        if cursor.fetchone():
            print("✅ Test table exists")
        else:
            print("❌ Test table not found")
            return False
        
        # Try to drop the table
        cursor.execute("DROP TABLE test_drop_table")
        conn.commit()
        
        print("✅ DROP TABLE command executed")
        
        # Verify table is gone
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='test_drop_table'")
        if cursor.fetchone():
            print("❌ Test table still exists after DROP")
            return False
        else:
            print("✅ Test table successfully dropped")
            return True
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
        return False
    finally:
        conn.close()

def test_transaction_commit():
    """Test transaction commit behavior"""
    
    conn = sqlite3.connect('attendance_system.db')
    cursor = conn.cursor()
    
    try:
        # Create test table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_transaction (
            id INTEGER PRIMARY KEY,
            name TEXT
        )
        """)
        
        # Test without commit
        cursor.execute("INSERT INTO test_transaction (name) VALUES ('no_commit')")
        # Don't commit here
        
        # Check if data exists in same connection
        cursor.execute("SELECT COUNT(*) FROM test_transaction")
        count_before = cursor.fetchone()[0]
        
        # Now commit
        conn.commit()
        
        # Check if data exists after commit
        cursor.execute("SELECT COUNT(*) FROM test_transaction")
        count_after = cursor.fetchone()[0]
        
        print(f"Records before commit: {count_before}")
        print(f"Records after commit: {count_after}")
        
        # Clean up
        cursor.execute("DROP TABLE test_transaction")
        conn.commit()
        
        return count_after > 0
        
    except Exception as e:
        print(f"❌ Transaction test error: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("Testing DROP TABLE functionality...")
    
    if test_drop_functionality():
        print("\n✅ DROP TABLE test PASSED")
    else:
        print("\n❌ DROP TABLE test FAILED")
        sys.exit(1)
    
    print("\nTesting transaction commit...")
    if test_transaction_commit():
        print("✅ Transaction commit test PASSED")
    else:
        print("❌ Transaction commit test FAILED")
        sys.exit(1)
    
    print("\n🎉 All tests passed! DROP functionality should work correctly.")
