#!/usr/bin/env python3
"""
Test script for professor subject assignment functionality
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import sqlite3
import pandas as pd
from database_utils import get_professors_list

def test_subjects_access():
    """Test accessing subjects"""
    print("Testing subjects access...")
    conn = sqlite3.connect('attendance_system.db')
    cursor = conn.cursor()
    
    # Check if subjects exists
    cursor.execute("SELECT name FROM sqlite_master WHERE (type='table' OR type='view') AND name='subjects'")
    result = cursor.fetchone()
    print(f"Subjects found: {result}")
    
    if result:
        # Get schema
        cursor.execute("PRAGMA table_info(subjects)")
        columns = {col[1] for col in cursor.fetchall()}
        print(f"Available columns: {columns}")
        
        # Check for required columns
        id_col = 'subject_id' if 'subject_id' in columns else 'id'
        name_col = 'subject_name' if 'subject_name' in columns else 'name'
        
        if id_col in columns and name_col in columns:
            query = f"SELECT {id_col} as subject_id, {name_col} as subject_name FROM subjects"
            df = pd.read_sql_query(query, conn)
            print(f"Found {len(df)} subjects:")
            print(df.head())
            return True
        else:
            print(f"Required columns not found. Available: {columns}")
            return False
    else:
        print("Subjects table/view not found")
        return False
    
    conn.close()

def test_professors_access():
    """Test accessing professors"""
    print("\nTesting professors access...")
    try:
        professors_df = get_professors_list()
        print(f"Found {len(professors_df)} professors:")
        print(professors_df.head())
        return True
    except Exception as e:
        print(f"Error getting professors: {e}")
        return False

def test_assignments_table():
    """Test professor subject assignments table"""
    print("\nTesting professor subject assignments...")
    conn = sqlite3.connect('attendance_system.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE (type='table' OR type='view') AND name='professor_subject_assignments'")
    result = cursor.fetchone()
    print(f"Professor assignments found: {result}")
    
    if result:
        cursor.execute("SELECT COUNT(*) FROM professor_subject_assignments")
        count = cursor.fetchone()[0]
        print(f"Existing assignments: {count}")
        
        cursor.execute("SELECT * FROM professor_subject_assignments LIMIT 3")
        assignments = cursor.fetchall()
        print("Sample assignments:", assignments)
        return True
    else:
        print("Professor assignments table/view not found")
        return False
    
    conn.close()

if __name__ == "__main__":
    print("=== Testing Professor Subject Assignment Components ===")
    
    subjects_ok = test_subjects_access()
    professors_ok = test_professors_access() 
    assignments_ok = test_assignments_table()
    
    print(f"\n=== Results ===")
    print(f"Subjects access: {'✅' if subjects_ok else '❌'}")
    print(f"Professors access: {'✅' if professors_ok else '❌'}")
    print(f"Assignments table: {'✅' if assignments_ok else '❌'}")
    
    if subjects_ok and professors_ok and assignments_ok:
        print("\n🎉 All components working correctly!")
    else:
        print("\n⚠️  Some components need fixing")
