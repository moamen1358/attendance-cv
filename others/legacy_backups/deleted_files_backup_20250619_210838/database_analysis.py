#!/usr/bin/env python3
"""
Database Cleanup and Relationship Analysis Script
This script analyzes the database structure, identifies unused tables, 
and establishes proper relationships between tables.
"""

import sqlite3
import pandas as pd
from datetime import datetime

# Database connection
conn = sqlite3.connect('attendance_system.db')
cursor = conn.cursor()

def analyze_database():
    """Analyze database structure and usage"""
    print("🔍 Database Analysis Report")
    print("=" * 50)
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence'")
    tables = [row[0] for row in cursor.fetchall()]
    
    table_analysis = []
    
    for table in tables:
        # Get record count
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        
        # Get table info
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        
        # Check for username column
        has_username = any(col[1] == 'username' for col in columns)
        
        # Check for foreign key references
        cursor.execute(f"PRAGMA foreign_key_list({table})")
        foreign_keys = cursor.fetchall()
        
        table_analysis.append({
            'table_name': table,
            'record_count': count,
            'column_count': len(columns),
            'has_username': has_username,
            'foreign_keys': len(foreign_keys),
            'columns': [col[1] for col in columns]
        })
    
    # Display analysis
    print("\\n📊 Table Usage Analysis:")
    print("-" * 80)
    for analysis in table_analysis:
        status = "✅ ACTIVE" if analysis['record_count'] > 0 else "❌ UNUSED"
        username_info = "👤 Has username" if analysis['has_username'] else ""
        
        print(f"{analysis['table_name']:<25} | {status:<10} | Records: {analysis['record_count']:<6} | {username_info}")
    
    # Identify potentially unused tables
    unused_tables = [t for t in table_analysis if t['record_count'] == 0]
    
    print(f"\\n🗑️ Potentially Unused Tables ({len(unused_tables)}):")
    for table in unused_tables:
        print(f"  - {table['table_name']} (0 records)")
    
    # Identify duplicate/redundant tables
    print("\\n🔄 Potential Redundancy Analysis:")
    
    # Group tables with similar purposes
    student_tables = [t for t in table_analysis if 'student' in t['table_name'].lower()]
    attendance_tables = [t for t in table_analysis if 'attendance' in t['table_name'].lower()]
    professor_tables = [t for t in table_analysis if 'prof' in t['table_name'].lower()]
    
    print("\\n👨‍🎓 Student-related tables:")
    for table in student_tables:
        print(f"  - {table['table_name']}: {table['record_count']} records")
        print(f"    Columns: {', '.join(table['columns'][:5])}{'...' if len(table['columns']) > 5 else ''}")
    
    print("\\n📚 Attendance-related tables:")
    for table in attendance_tables:
        print(f"  - {table['table_name']}: {table['record_count']} records")
        print(f"    Columns: {', '.join(table['columns'][:5])}{'...' if len(table['columns']) > 5 else ''}")
    
    print("\\n👨‍🏫 Professor-related tables:")
    for table in professor_tables:
        print(f"  - {table['table_name']}: {table['record_count']} records")
        print(f"    Columns: {', '.join(table['columns'][:5])}{'...' if len(table['columns']) > 5 else ''}")
    
    return table_analysis, unused_tables

def check_username_relationships():
    """Check relationships between tables with username columns"""
    print("\\n\\n🔗 Username Relationship Analysis")
    print("=" * 50)
    
    # Find all tables with username column
    username_tables = []
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        if any(col[1] == 'username' for col in columns):
            # Get unique usernames from this table
            try:
                cursor.execute(f"SELECT DISTINCT username FROM {table} WHERE username IS NOT NULL")
                usernames = [row[0] for row in cursor.fetchall()]
                username_tables.append({
                    'table': table,
                    'usernames': usernames,
                    'count': len(usernames)
                })
            except:
                username_tables.append({
                    'table': table,
                    'usernames': [],
                    'count': 0
                })
    
    print("\\n📋 Tables with username column:")
    for table_info in username_tables:
        print(f"  - {table_info['table']}: {table_info['count']} unique usernames")
        if table_info['usernames'][:3]:  # Show first 3 usernames
            print(f"    Examples: {', '.join(table_info['usernames'][:3])}")
    
    # Find common usernames across tables
    all_usernames = set()
    for table_info in username_tables:
        all_usernames.update(table_info['usernames'])
    
    print(f"\\n🔍 Total unique usernames across all tables: {len(all_usernames)}")
    
    # Check for orphaned usernames
    print("\\n⚠️ Relationship Issues:")
    
    for table_info in username_tables:
        other_tables = [t for t in username_tables if t['table'] != table_info['table']]
        other_usernames = set()
        for t in other_tables:
            other_usernames.update(t['usernames'])
        
        orphaned = set(table_info['usernames']) - other_usernames
        if orphaned and len(table_info['usernames']) > 0:
            orphan_pct = (len(orphaned) / len(table_info['usernames'])) * 100
            print(f"  - {table_info['table']}: {len(orphaned)} orphaned usernames ({orphan_pct:.1f}%)")
    
    return username_tables

def generate_cleanup_recommendations():
    """Generate recommendations for database cleanup"""
    print("\\n\\n💡 Cleanup Recommendations")
    print("=" * 50)
    
    recommendations = []
    
    # Analyze unused tables
    cursor.execute("SELECT COUNT(*) FROM attendance")
    attendance_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM attendance_log")
    attendance_log_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM course_students")
    course_students_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM student_profiles_temp")
    temp_count = cursor.fetchone()[0]
    
    # Generate specific recommendations
    if attendance_count == 0 and attendance_log_count == 0:
        recommendations.append({
            'action': 'DELETE',
            'tables': ['attendance', 'attendance_log'],
            'reason': 'Both tables are empty and likely redundant with attendance_records',
            'risk': 'LOW'
        })
    
    if course_students_count == 0:
        recommendations.append({
            'action': 'DELETE',
            'tables': ['course_students'],
            'reason': 'Table is empty and functionality likely handled elsewhere',
            'risk': 'LOW'
        })
    
    if temp_count == 0:
        recommendations.append({
            'action': 'DELETE',
            'tables': ['student_profiles_temp'],
            'reason': 'Temporary table with no data',
            'risk': 'LOW'
        })
    
    # Consolidation recommendations
    recommendations.append({
        'action': 'CONSOLIDATE',
        'tables': ['user_accounts', 'professor_profiles', 'student_profiles'],
        'reason': 'These tables have overlapping user information that could be unified',
        'risk': 'MEDIUM'
    })
    
    recommendations.append({
        'action': 'ADD_FOREIGN_KEYS',
        'tables': ['attendance_records', 'class_attendance'],
        'reason': 'Add proper foreign key relationships to user tables',
        'risk': 'LOW'
    })
    
    # Display recommendations
    for i, rec in enumerate(recommendations, 1):
        risk_color = "🔴" if rec['risk'] == 'HIGH' else "🟡" if rec['risk'] == 'MEDIUM' else "🟢"
        print(f"\\n{i}. {rec['action']} - {risk_color} {rec['risk']} RISK")
        print(f"   Tables: {', '.join(rec['tables'])}")
        print(f"   Reason: {rec['reason']}")
    
    return recommendations

def main():
    """Main analysis function"""
    print("🚀 Starting Database Analysis...")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Run analysis
        table_analysis, unused_tables = analyze_database()
        username_tables = check_username_relationships()
        recommendations = generate_cleanup_recommendations()
        
        print("\\n\\n✅ Analysis Complete!")
        print(f"\\n📊 Summary:")
        print(f"  - Total tables analyzed: {len(table_analysis)}")
        print(f"  - Unused tables found: {len(unused_tables)}")
        print(f"  - Tables with username: {len(username_tables)}")
        print(f"  - Cleanup recommendations: {len(recommendations)}")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
    
    finally:
        conn.close()

if __name__ == "__main__":
    main()
