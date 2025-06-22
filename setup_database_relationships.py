#!/usr/bin/env python3
"""
Database setup script to ensure proper relationships for student-subject enrollment
"""

import sqlite3
from datetime import datetime

DATABASE_PATH = 'attendance_system.db'

def setup_academic_structure():
    """Set up academic structure tables and relationships"""
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # Create departments table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS departments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert default departments
        departments = [
            ("Computer Science", "Computer Science and Programming"),
            ("Information Technology", "Information Technology and Systems"),
            ("Software Engineering", "Software Development and Engineering"),
            ("Electrical Engineering", "Electrical and Electronics Engineering"),
            ("Mechanical Engineering", "Mechanical Engineering and Design"),
            ("Civil Engineering", "Civil and Construction Engineering"),
            ("Business Administration", "Business Management and Administration"),
            ("Accounting", "Accounting and Finance"),
            ("Marketing", "Marketing and Sales")
        ]
        
        for dept_name, dept_desc in departments:
            cursor.execute("""
                INSERT OR IGNORE INTO departments (name, description)
                VALUES (?, ?)
            """, (dept_name, dept_desc))
        
        # Ensure academic_terms table exists and has data
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS academic_terms (
                term_id INTEGER PRIMARY KEY AUTOINCREMENT,
                term_name TEXT UNIQUE NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                is_active BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert current academic terms
        current_year = datetime.now().year
        terms = [
            (f"Fall {current_year}", f"{current_year}-09-01", f"{current_year}-12-15", 1),
            (f"Spring {current_year + 1}", f"{current_year + 1}-01-15", f"{current_year + 1}-05-15", 0),
            (f"Summer {current_year + 1}", f"{current_year + 1}-06-01", f"{current_year + 1}-08-15", 0)
        ]
        
        for term_name, start_date, end_date, is_active in terms:
            cursor.execute("""
                INSERT OR IGNORE INTO academic_terms (term_name, start_date, end_date, is_active)
                VALUES (?, ?, ?, ?)
            """, (term_name, start_date, end_date, is_active))
        
        # Ensure subjects table has proper structure
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                course_code TEXT,
                credit_hours INTEGER DEFAULT 3,
                department_id INTEGER,
                academic_year TEXT,
                FOREIGN KEY (department_id) REFERENCES departments(id)
            )
        """)
        
        # Add sample subjects for different departments and years
        sample_subjects = [
            # Computer Science Year 1
            ("Introduction to Programming", "CS101", 3, "Computer Science", "Year 1", "Basic programming concepts and logic"),
            ("Computer Fundamentals", "CS102", 3, "Computer Science", "Year 1", "Computer architecture and systems"),
            ("Mathematics I", "MATH101", 4, "Computer Science", "Year 1", "Calculus and discrete mathematics"),
            ("English Communication", "ENG101", 2, "Computer Science", "Year 1", "Technical writing and communication"),
            
            # Computer Science Year 2
            ("Data Structures", "CS201", 4, "Computer Science", "Year 2", "Advanced data structures and algorithms"),
            ("Object-Oriented Programming", "CS202", 3, "Computer Science", "Year 2", "OOP concepts and design patterns"),
            ("Database Systems", "CS203", 3, "Computer Science", "Year 2", "Database design and management"),
            ("Mathematics II", "MATH201", 3, "Computer Science", "Year 2", "Linear algebra and statistics"),
            
            # Information Technology Year 1
            ("IT Fundamentals", "IT101", 3, "Information Technology", "Year 1", "Basic IT concepts and systems"),
            ("Network Basics", "IT102", 3, "Information Technology", "Year 1", "Introduction to networking"),
            ("Web Development", "IT103", 3, "Information Technology", "Year 1", "HTML, CSS, and basic web design"),
            
            # Information Technology Year 2
            ("System Administration", "IT201", 3, "Information Technology", "Year 2", "Server and system management"),
            ("Network Security", "IT202", 3, "Information Technology", "Year 2", "Cybersecurity fundamentals"),
            ("Database Management", "IT203", 3, "Information Technology", "Year 2", "Database administration"),
            
            # Business Administration Year 1
            ("Introduction to Business", "BUS101", 3, "Business Administration", "Year 1", "Basic business concepts"),
            ("Accounting Principles", "ACC101", 3, "Business Administration", "Year 1", "Financial accounting basics"),
            ("Business Mathematics", "MATH110", 3, "Business Administration", "Year 1", "Mathematics for business"),
            
            # Engineering subjects
            ("Engineering Mathematics", "ENGM101", 4, "Electrical Engineering", "Year 1", "Advanced mathematics for engineers"),
            ("Circuit Analysis", "EE101", 4, "Electrical Engineering", "Year 1", "Basic electrical circuits"),
            ("Mechanics", "ME101", 4, "Mechanical Engineering", "Year 1", "Statics and dynamics"),
        ]
        
        for subject_name, course_code, credit_hours, dept_name, academic_year, description in sample_subjects:
            # Get department ID
            cursor.execute("SELECT id FROM departments WHERE name = ?", (dept_name,))
            dept_result = cursor.fetchone()
            dept_id = dept_result[0] if dept_result else None
            
            cursor.execute("""
                INSERT OR IGNORE INTO subjects (name, course_code, credit_hours, department_id, academic_year, description)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (subject_name, course_code, credit_hours, dept_id, academic_year, description))
        
        # Ensure classes table exists with proper structure
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS classes (
                class_id INTEGER PRIMARY KEY AUTOINCREMENT,
                class_code TEXT UNIQUE NOT NULL,
                subject_id INTEGER NOT NULL,
                professor_id INTEGER DEFAULT 1,
                term_id INTEGER NOT NULL,
                section TEXT DEFAULT 'A',
                max_students INTEGER DEFAULT 50,
                room TEXT,
                schedule_days TEXT,
                start_time TIME,
                end_time TIME,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (subject_id) REFERENCES subjects(id),
                FOREIGN KEY (term_id) REFERENCES academic_terms(term_id)
            )
        """)
        
        # Ensure student_classes table exists with proper structure
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS student_classes (
                enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                class_id INTEGER NOT NULL,
                enrollment_date DATE DEFAULT (DATE('now')),
                status TEXT DEFAULT 'enrolled',
                grade TEXT,
                attendance_percentage REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(student_id, class_id),
                FOREIGN KEY (student_id) REFERENCES student_profiles(id),
                FOREIGN KEY (class_id) REFERENCES classes(class_id)
            )
        """)
        
        conn.commit()
        print("✅ Academic structure setup completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error setting up academic structure: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def create_classes_for_subjects():
    """Create default classes for all subjects"""
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # Get current active term
        cursor.execute("SELECT term_id FROM academic_terms WHERE is_active = 1 LIMIT 1")
        term_result = cursor.fetchone()
        term_id = term_result[0] if term_result else 1
        
        # Get all subjects that don't have classes yet
        cursor.execute("""
            SELECT s.id, s.name, s.course_code, s.academic_year
            FROM subjects s
            LEFT JOIN classes c ON s.id = c.subject_id
            WHERE c.subject_id IS NULL
        """)
        
        subjects_without_classes = cursor.fetchall()
        
        for subject_id, subject_name, course_code, academic_year in subjects_without_classes:
            # Create a default class for this subject
            class_code = f"{course_code}-A" if course_code else f"{subject_name.replace(' ', '')}-A"
            
            cursor.execute("""
                INSERT OR IGNORE INTO classes (
                    class_code, subject_id, term_id, section, max_students, status
                ) VALUES (?, ?, ?, 'A', 50, 'active')
            """, (class_code, subject_id, term_id))
        
        conn.commit()
        print(f"✅ Created classes for {len(subjects_without_classes)} subjects")
        return True
        
    except Exception as e:
        print(f"❌ Error creating classes: {e}")
        return False
    finally:
        conn.close()

def verify_database_structure():
    """Verify that all required tables and relationships exist"""
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # Check required tables
        required_tables = [
            'departments', 'academic_terms', 'subjects', 'classes', 
            'student_classes', 'student_profiles', 'user_accounts'
        ]
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        missing_tables = set(required_tables) - set(existing_tables)
        
        if missing_tables:
            print(f"⚠️ Missing tables: {', '.join(missing_tables)}")
            return False
        
        # Check data counts
        for table in required_tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"📊 {table}: {count} records")
        
        print("✅ Database structure verification completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error verifying database structure: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("🔧 Setting up academic database structure...")
    
    # Setup academic structure
    if setup_academic_structure():
        print("✅ Academic structure setup completed")
    else:
        print("❌ Academic structure setup failed")
        exit(1)
    
    # Create classes for subjects
    if create_classes_for_subjects():
        print("✅ Classes creation completed")
    else:
        print("❌ Classes creation failed")
    
    # Verify structure
    if verify_database_structure():
        print("✅ Database structure verified")
    else:
        print("⚠️ Database structure verification has issues")
    
    print("🎉 Database setup completed!")
