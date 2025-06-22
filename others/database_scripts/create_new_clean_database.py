#!/usr/bin/env python3
"""
Create New Clean Database

This script creates a brand new database with only the enhanced tables you use,
transfers all existing data, and ensures no old tables exist.
"""

import sqlite3
import shutil
from datetime import datetime
import json

OLD_DATABASE = 'attendance_system.db'
NEW_DATABASE = 'clean_attendance_system.db'

def create_backup():
    """Create backup of old database"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"attendance_system_backup_before_new_db_{timestamp}.db"
    shutil.copy2(OLD_DATABASE, backup_path)
    print(f"✅ Backup created: {backup_path}")
    return backup_path

def create_new_database():
    """Create the new clean database with only enhanced tables"""
    
    # Remove new database if it exists
    import os
    if os.path.exists(NEW_DATABASE):
        os.remove(NEW_DATABASE)
    
    conn = sqlite3.connect(NEW_DATABASE)
    cursor = conn.cursor()
    
    print("🏗️ Creating new clean database structure...")
    
    # 1. Create departments table
    cursor.execute('''
        CREATE TABLE departments (
            department_id INTEGER PRIMARY KEY AUTOINCREMENT,
            department_code TEXT UNIQUE NOT NULL,
            department_name TEXT NOT NULL,
            department_head TEXT,
            contact_email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 2. Create academic_terms table  
    cursor.execute('''
        CREATE TABLE academic_terms (
            term_id INTEGER PRIMARY KEY AUTOINCREMENT,
            term_name TEXT NOT NULL,
            start_date DATE,
            end_date DATE,
            is_active BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 3. Create student_profiles_enhanced table
    cursor.execute('''
        CREATE TABLE student_profiles_enhanced (
            student_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            student_number TEXT UNIQUE,
            email TEXT,
            phone TEXT,
            department_id INTEGER,
            academic_year INTEGER DEFAULT 1,
            current_semester INTEGER DEFAULT 1,
            gpa REAL,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (department_id) REFERENCES departments(department_id)
        )
    ''')
    
    # 4. Create user_accounts_enhanced table
    cursor.execute('''
        CREATE TABLE user_accounts_enhanced (
            account_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'student',
            student_id INTEGER,
            professor_id INTEGER,
            is_active BOOLEAN DEFAULT 1,
            last_login TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES student_profiles_enhanced(student_id)
        )
    ''')
    
    # 5. Create subjects_enhanced table
    cursor.execute('''
        CREATE TABLE subjects_enhanced (
            subject_id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_name TEXT NOT NULL,
            course_code TEXT UNIQUE,
            credit_hours INTEGER DEFAULT 3,
            department_id INTEGER,
            academic_year INTEGER,
            semester INTEGER,
            description TEXT,
            prerequisites TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (department_id) REFERENCES departments(department_id)
        )
    ''')
    
    # 6. Create student_enrollments table
    cursor.execute('''
        CREATE TABLE student_enrollments (
            enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            subject_id INTEGER,
            term_id INTEGER,
            status TEXT DEFAULT 'enrolled',
            grade TEXT,
            enrollment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES student_profiles_enhanced(student_id),
            FOREIGN KEY (subject_id) REFERENCES subjects_enhanced(subject_id),
            FOREIGN KEY (term_id) REFERENCES academic_terms(term_id)
        )
    ''')
    
    # 7. Create class_schedules_enhanced table
    cursor.execute('''
        CREATE TABLE class_schedules_enhanced (
            schedule_id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER,
            day_of_week TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            room TEXT,
            professor_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (subject_id) REFERENCES subjects_enhanced(subject_id)
        )
    ''')
    
    # 8. Create attendance_records_enhanced table
    cursor.execute('''
        CREATE TABLE attendance_records_enhanced (
            record_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            subject_id INTEGER,
            class_date DATE,
            status TEXT DEFAULT 'present',
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            confidence_score REAL,
            notes TEXT,
            FOREIGN KEY (student_id) REFERENCES student_profiles_enhanced(student_id),
            FOREIGN KEY (subject_id) REFERENCES subjects_enhanced(subject_id)
        )
    ''')
    
    # 9. Create facial_embeddings table
    cursor.execute('''
        CREATE TABLE facial_embeddings (
            embedding_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            embedding_data TEXT NOT NULL,
            confidence_threshold REAL DEFAULT 0.6,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES student_profiles_enhanced(student_id)
        )
    ''')
    
    # 10. Create professor_profiles table
    cursor.execute('''
        CREATE TABLE professor_profiles (
            professor_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            department_id INTEGER,
            office_location TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (department_id) REFERENCES departments(department_id)
        )
    ''')
    
    # 11. Create login_logs table
    cursor.execute('''
        CREATE TABLE login_logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            role TEXT,
            login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT,
            user_agent TEXT,
            success BOOLEAN DEFAULT 1
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ New database structure created")

def transfer_data():
    """Transfer data from old database to new database"""
    print("📊 Transferring data from old database...")
    
    old_conn = sqlite3.connect(OLD_DATABASE)
    new_conn = sqlite3.connect(NEW_DATABASE)
    
    old_cursor = old_conn.cursor()
    new_cursor = new_conn.cursor()
    
    try:
        # 1. Transfer departments
        old_cursor.execute("SELECT * FROM departments")
        departments = old_cursor.fetchall()
        for dept in departments:
            new_cursor.execute('''
                INSERT INTO departments (department_id, department_code, department_name, department_head, contact_email, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', dept)
        print(f"✅ Transferred {len(departments)} departments")
        
        # 2. Transfer academic_terms
        old_cursor.execute("SELECT * FROM academic_terms")
        terms = old_cursor.fetchall()
        for term in terms:
            new_cursor.execute('''
                INSERT INTO academic_terms (term_id, term_name, start_date, end_date, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', term)
        print(f"✅ Transferred {len(terms)} academic terms")
        
        # 3. Transfer student_profiles_enhanced
        old_cursor.execute("SELECT * FROM student_profiles_enhanced")
        students = old_cursor.fetchall()
        for student in students:
            new_cursor.execute('''
                INSERT INTO student_profiles_enhanced 
                (student_id, username, name, student_number, email, phone, department_id, academic_year, current_semester, gpa, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', student)
        print(f"✅ Transferred {len(students)} students")
        
        # 4. Transfer user_accounts_enhanced
        old_cursor.execute("SELECT * FROM user_accounts_enhanced")
        accounts = old_cursor.fetchall()
        for account in accounts:
            new_cursor.execute('''
                INSERT INTO user_accounts_enhanced 
                (account_id, username, password, role, student_id, professor_id, is_active, last_login, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', account)
        print(f"✅ Transferred {len(accounts)} user accounts")
        
        # 5. Transfer subjects_enhanced
        old_cursor.execute("SELECT * FROM subjects_enhanced")
        subjects = old_cursor.fetchall()
        for subject in subjects:
            new_cursor.execute('''
                INSERT INTO subjects_enhanced 
                (subject_id, subject_name, course_code, credit_hours, department_id, academic_year, semester, description, prerequisites, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', subject)
        print(f"✅ Transferred {len(subjects)} subjects")
        
        # 6. Transfer student_enrollments
        old_cursor.execute("SELECT * FROM student_enrollments")
        enrollments = old_cursor.fetchall()
        for enrollment in enrollments:
            new_cursor.execute('''
                INSERT INTO student_enrollments 
                (enrollment_id, student_id, subject_id, term_id, status, grade, enrollment_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', enrollment)
        print(f"✅ Transferred {len(enrollments)} enrollments")
        
        # 7. Transfer class_schedules_enhanced
        old_cursor.execute("SELECT * FROM class_schedules_enhanced")
        schedules = old_cursor.fetchall()
        for schedule in schedules:
            new_cursor.execute('''
                INSERT INTO class_schedules_enhanced 
                (schedule_id, subject_id, day_of_week, start_time, end_time, room, professor_name, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', schedule)
        print(f"✅ Transferred {len(schedules)} class schedules")
        
        # 8. Transfer attendance_records_enhanced
        old_cursor.execute("SELECT * FROM attendance_records_enhanced")
        attendance = old_cursor.fetchall()
        for record in attendance:
            new_cursor.execute('''
                INSERT INTO attendance_records_enhanced 
                (record_id, student_id, subject_id, class_date, status, timestamp, confidence_score, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', record)
        print(f"✅ Transferred {len(attendance)} attendance records")
        
        # 9. Transfer facial_embeddings
        old_cursor.execute("SELECT * FROM facial_embeddings")
        embeddings = old_cursor.fetchall()
        for embedding in embeddings:
            new_cursor.execute('''
                INSERT INTO facial_embeddings 
                (embedding_id, student_id, embedding_data, confidence_threshold, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', embedding)
        print(f"✅ Transferred {len(embeddings)} facial embeddings")
        
        # 10. Transfer professor_profiles
        old_cursor.execute("SELECT * FROM professor_profiles")
        professors = old_cursor.fetchall()
        for professor in professors:
            new_cursor.execute('''
                INSERT INTO professor_profiles 
                (professor_id, username, name, email, phone, department_id, office_location, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', professor)
        print(f"✅ Transferred {len(professors)} professors")
        
        # 11. Transfer login_logs
        old_cursor.execute("SELECT * FROM login_logs")
        logs = old_cursor.fetchall()
        for log in logs:
            new_cursor.execute('''
                INSERT INTO login_logs 
                (log_id, username, role, login_time, ip_address, user_agent, success)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', log)
        print(f"✅ Transferred {len(logs)} login logs")
        
        new_conn.commit()
        
    except Exception as e:
        print(f"❌ Error transferring data: {e}")
        new_conn.rollback()
        raise
    finally:
        old_conn.close()
        new_conn.close()

def verify_new_database():
    """Verify the new database"""
    print("\n📊 Verifying new database...")
    
    conn = sqlite3.connect(NEW_DATABASE)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    
    print(f"✅ Tables in new database: {len(tables)}")
    
    total_records = 0
    for table_name, in tables:
        if not table_name.startswith('sqlite_'):
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"   📊 {table_name}: {count} rows")
            total_records += count
    
    print(f"✅ Total records: {total_records}")
    
    # Verify key relationships
    cursor.execute("SELECT COUNT(*) FROM student_profiles_enhanced")
    students = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM user_accounts_enhanced WHERE role='student'")
    accounts = cursor.fetchone()[0]
    
    print(f"✅ Students: {students}, Accounts: {accounts}")
    print(f"✅ Consistency: {'PERFECT' if students == accounts else 'MISMATCH'}")
    
    conn.close()

def replace_old_database():
    """Replace the old database with the new clean one"""
    print("\n🔄 Replacing old database with new clean database...")
    
    # Create final backup of old database
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    final_backup = f"attendance_system_final_backup_{timestamp}.db"
    shutil.copy2(OLD_DATABASE, final_backup)
    print(f"✅ Final backup: {final_backup}")
    
    # Replace old database with new one
    shutil.copy2(NEW_DATABASE, OLD_DATABASE)
    print(f"✅ Replaced {OLD_DATABASE} with clean database")
    
    # Verify the replacement
    conn = sqlite3.connect(OLD_DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall() if not row[0].startswith('sqlite_')]
    conn.close()
    
    print(f"✅ Verification: {len(tables)} clean tables in production database")
    for table in tables:
        print(f"   - {table}")

def main():
    """Main function"""
    print("🆕 Creating New Clean Database")
    print("=" * 40)
    
    try:
        # Create backup
        backup_path = create_backup()
        
        # Create new database structure
        create_new_database()
        
        # Transfer all data
        transfer_data()
        
        # Verify new database
        verify_new_database()
        
        # Replace old database
        response = input("\n❓ Replace old database with new clean database? (y/N): ").lower().strip()
        if response == 'y':
            replace_old_database()
            print("\n🎉 Database replacement completed!")
            print("✅ Your database is now completely clean")
            print("✅ Only enhanced tables remain")
            print("✅ All data preserved")
        else:
            print(f"\n✅ New clean database created as: {NEW_DATABASE}")
            print("✅ Original database unchanged")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
