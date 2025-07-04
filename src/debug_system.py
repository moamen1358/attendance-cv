#!/usr/bin/env python3
"""
Quick debugging script to enable verbose logging and run database diagnostics
"""

import os
import sys
import sqlite3
sys.path.append(os.path.dirname(__file__))

DATABASE_PATH = 'attendance_system.db'

def debug_database_structure():
    """Debug function to check database structure and data"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        print("🔍 DEBUG: Checking database structure...")
        
        # Check available tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"📊 Available tables: {[table[0] for table in tables]}")
        
        # Check student_profiles_enhanced structure
        try:
            cursor.execute("PRAGMA table_info(student_profiles_enhanced);")
            columns = cursor.fetchall()
            print(f"📋 student_profiles_enhanced columns: {[col[1] for col in columns]}")
            
            # Check sample data
            cursor.execute("SELECT profile_name, student_id, status FROM student_profiles_enhanced LIMIT 5;")
            profiles = cursor.fetchall()
            print(f"👥 Sample profiles: {profiles}")
            
            # Check for encoding data
            cursor.execute("SELECT COUNT(*) FROM student_profiles_enhanced WHERE encoding_data IS NOT NULL;")
            with_encoding = cursor.fetchone()[0]
            print(f"📊 Profiles with encoding data: {with_encoding}")
            
            # Check total student profiles
            cursor.execute("SELECT COUNT(*) FROM student_profiles_enhanced;")
            total_profiles = cursor.fetchone()[0]
            print(f"📊 Total student profiles: {total_profiles}")
            
            if total_profiles == 0:
                print("⚠️ NO STUDENT PROFILES FOUND! This explains why no attendance is logged.")
                
        except Exception as e:
            print(f"⚠️ Error checking student_profiles_enhanced: {e}")
        
        # Check students_enhanced structure  
        try:
            cursor.execute("PRAGMA table_info(students_enhanced);")
            columns = cursor.fetchall()
            print(f"📋 students_enhanced columns: {[col[1] for col in columns]}")
            
            cursor.execute("SELECT student_id, name FROM students_enhanced LIMIT 5;")
            students = cursor.fetchall()
            print(f"🎓 Sample students: {students}")
            
            # Check total students
            cursor.execute("SELECT COUNT(*) FROM students_enhanced;")
            total_students = cursor.fetchone()[0]
            print(f"📊 Total students: {total_students}")
            
            if total_students == 0:
                print("⚠️ NO STUDENTS FOUND! Need to add students first.")
                
        except Exception as e:
            print(f"⚠️ Error checking students_enhanced: {e}")
            
        # Check for legacy tables that might have data
        print("\n🔍 Checking for legacy tables with data...")
        legacy_tables = ['students', 'facial_recognition_data', 'presidents_embeds', 'student_profiles']
        
        for table in legacy_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table};")
                count = cursor.fetchone()[0]
                if count > 0:
                    print(f"📊 Legacy table {table}: {count} records")
                    cursor.execute(f"SELECT * FROM {table} LIMIT 3;")
                    sample = cursor.fetchall()
                    print(f"   Sample data: {sample}")
            except Exception:
                pass  # Table doesn't exist
            
        # Check attendance records structure
        try:
            cursor.execute("PRAGMA table_info(attendance_records_enhanced);")
            columns = cursor.fetchall()
            print(f"� attendance_records_enhanced columns: {[col[1] for col in columns]}")
            
            cursor.execute("SELECT COUNT(*) FROM attendance_records_enhanced;")
            attendance_count = cursor.fetchone()[0]
            print(f"📊 Total attendance records: {attendance_count}")
        except Exception as e:
            print(f"⚠️ Error checking attendance_records_enhanced: {e}")
            
    except Exception as e:
        print(f"❌ Database debug error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    print("🔍 Starting debug session...")
    print("=" * 60)
    
    # Check database structure
    debug_database_structure()
    
    print("\n" + "=" * 60)
    print("✅ Debug session complete")
    print("📝 To run the system with verbose logging:")
    print("   - Edit src/performance_config.py")
    print("   - Set VERBOSE_LOGGING = True")
    print("   - Restart the application")

if __name__ == "__main__":
    main()
