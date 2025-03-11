import sqlite3
import pandas as pd
import time

# Constants
DATABASE_PATH = 'attendance_system.db'

def check_database_integrity():
    """Check overall database integrity"""
    print("🔍 Checking database integrity...")
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Run integrity check
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()
        
        if result and result[0] == "ok":
            print("✅ Database integrity check passed")
        else:
            print(f"❌ Database integrity issues found: {result}")
            return False
        
        # Run foreign key check
        cursor.execute("PRAGMA foreign_key_check")
        fk_issues = cursor.fetchall()
        
        if not fk_issues:
            print("✅ Foreign key check passed")
        else:
            print(f"❌ Foreign key violations found: {len(fk_issues)}")
            for issue in fk_issues:
                print(f"   - Table: {issue[0]}, RowID: {issue[1]}, Referenced Table: {issue[2]}")
        
        conn.close()
        return True
    
    except Exception as e:
        print(f"❌ Error checking database: {str(e)}")
        return False

def verify_required_tables():
    """Verify all required tables are present"""
    required_tables = [
        'student_profiles',       # Students table
        'user_accounts',          # Users table
        'facial_recognition_data', # Facial recognition data
        'attendance_records',     # Attendance logs
        'class_schedules',        # Class schedules
        'class_attendance_records' # Class attendance
    ]
    
    print("\n🔍 Checking required tables...")
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        missing_tables = [table for table in required_tables if table not in existing_tables]
        
        if not missing_tables:
            print("✅ All required tables are present")
        else:
            print(f"❌ Missing tables: {', '.join(missing_tables)}")
        
        # Check tables have data
        for table in required_tables:
            if table in existing_tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"   - {table}: {count} records")
        
        conn.close()
        return not missing_tables
    
    except Exception as e:
        print(f"❌ Error verifying tables: {str(e)}")
        return False

def check_query_performance():
    """Check performance of critical queries"""
    print("\n🔍 Testing query performance...")
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        
        # Test 1: Get student attendance
        print("   Testing attendance query...")
        start_time = time.time()
        query = """
        SELECT ar.name, DATE(ar.timestamp) as date, COUNT(*) as detections
        FROM attendance_records ar
        GROUP BY ar.name, DATE(ar.timestamp)
        ORDER BY date DESC
        LIMIT 100
        """
        df = pd.read_sql(query, conn)
        elapsed = time.time() - start_time
        print(f"   ✓ Query returned {len(df)} rows in {elapsed:.3f} seconds")
        
        # Test 2: Get class attendance
        print("   Testing class attendance query...")
        start_time = time.time()
        query = """
        SELECT student_name, class_date, subject, attended
        FROM class_attendance_records
        ORDER BY class_date DESC
        LIMIT 100
        """
        df = pd.read_sql(query, conn)
        elapsed = time.time() - start_time
        print(f"   ✓ Query returned {len(df)} rows in {elapsed:.3f} seconds")
        
        # Test 3: Get student list
        print("   Testing student query...")
        start_time = time.time()
        query = """
        SELECT name, section, student_id
        FROM student_profiles
        ORDER BY name
        """
        df = pd.read_sql(query, conn)
        elapsed = time.time() - start_time
        print(f"   ✓ Query returned {len(df)} rows in {elapsed:.3f} seconds")
        
        conn.close()
        return True
    
    except Exception as e:
        print(f"❌ Error testing queries: {str(e)}")
        return False

def main():
    print("🔍 Database Verification Utility")
    print("This tool checks if your database is functioning correctly\n")
    
    integrity_ok = check_database_integrity()
    tables_ok = verify_required_tables()
    queries_ok = check_query_performance()
    
    print("\n=== Verification Results ===")
    print(f"Database Integrity: {'✅ Pass' if integrity_ok else '❌ Fail'}")
    print(f"Required Tables:    {'✅ Pass' if tables_ok else '❌ Fail'}")
    print(f"Query Performance:  {'✅ Pass' if queries_ok else '❌ Fail'}")
    
    if integrity_ok and tables_ok and queries_ok:
        print("\n✅ Your database appears to be working correctly!")
    else:
        print("\n⚠️  Issues were found with your database. Consider restoring from backup.")

if __name__ == "__main__":
    main()
