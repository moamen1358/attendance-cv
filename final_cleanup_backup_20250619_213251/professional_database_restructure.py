#!/usr/bin/env python3
"""
Professional Database Restructuring Script
==========================================
This script creates a comprehensive professional database structure for the attendance system
with proper relationships, constraints, and modern database design principles.
"""

import sqlite3
import logging
from datetime import datetime
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProfessionalDatabaseRestructure:
    def __init__(self, db_path='attendance_system.db'):
        self.db_path = db_path
        self.conn = None
        
    def connect(self):
        """Connect to database"""
        self.conn = sqlite3.connect(self.db_path)
        # Temporarily disable foreign keys during migration
        self.conn.execute("PRAGMA foreign_keys = OFF")
        return self.conn
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def backup_database(self):
        """Create backup before restructuring"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"attendance_system_professional_backup_{timestamp}.db"
        
        with sqlite3.connect(backup_name) as backup_conn:
            self.conn.backup(backup_conn)
        
        logger.info(f"Database backed up to: {backup_name}")
        return backup_name
    
    def analyze_current_structure(self):
        """Analyze current database structure"""
        cursor = self.conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [row[0] for row in cursor.fetchall()]
        
        structure = {}
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            
            structure[table] = {
                'count': count,
                'columns': [{'name': col[1], 'type': col[2], 'notnull': col[3], 'pk': col[5]} for col in columns]
            }
        
        return structure
    
    def create_professional_schema(self):
        """Create professional database schema"""
        cursor = self.conn.cursor()
        
        logger.info("🏗️  Creating Professional Database Schema")
        
        # 1. Create academic_terms table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS academic_terms (
                term_id INTEGER PRIMARY KEY AUTOINCREMENT,
                term_name TEXT NOT NULL UNIQUE,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                is_active BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 2. Create departments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS departments (
                department_id INTEGER PRIMARY KEY AUTOINCREMENT,
                department_code TEXT NOT NULL UNIQUE,
                department_name TEXT NOT NULL,
                description TEXT,
                head_professor_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (head_professor_id) REFERENCES professor_profiles(id)
            )
        """)
        
        # 3. Restructure subjects table with proper relationships
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subjects_new (
                subject_id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_code TEXT NOT NULL UNIQUE,
                subject_name TEXT NOT NULL,
                description TEXT,
                credits INTEGER DEFAULT 3,
                department_id INTEGER,
                professor_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (department_id) REFERENCES departments(department_id),
                FOREIGN KEY (professor_id) REFERENCES professor_profiles(id)
            )
        """)
        
        # 4. Create classes table (sections of subjects)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS classes (
                class_id INTEGER PRIMARY KEY AUTOINCREMENT,
                class_code TEXT NOT NULL UNIQUE,
                subject_id INTEGER NOT NULL,
                professor_id INTEGER NOT NULL,
                term_id INTEGER NOT NULL,
                section TEXT DEFAULT 'A',
                max_students INTEGER DEFAULT 50,
                room TEXT,
                schedule_days TEXT, -- JSON array of days
                start_time TIME,
                end_time TIME,
                status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'completed')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (subject_id) REFERENCES subjects_new(subject_id),
                FOREIGN KEY (professor_id) REFERENCES professor_profiles(id),
                FOREIGN KEY (term_id) REFERENCES academic_terms(term_id)
            )
        """)
        
        # 5. Create student_classes table (enrollments)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS student_classes (
                enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                class_id INTEGER NOT NULL,
                enrollment_date DATE DEFAULT (DATE('now')),
                status TEXT DEFAULT 'enrolled' CHECK (status IN ('enrolled', 'dropped', 'completed', 'failed')),
                grade TEXT,
                attendance_percentage REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES student_profiles(id),
                FOREIGN KEY (class_id) REFERENCES classes(class_id),
                UNIQUE(student_id, class_id)
            )
        """)
        
        # 6. Create professional attendance_sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance_sessions (
                session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                class_id INTEGER NOT NULL,
                session_date DATE NOT NULL,
                session_time TIME NOT NULL,
                session_type TEXT DEFAULT 'lecture' CHECK (session_type IN ('lecture', 'lab', 'tutorial', 'exam')),
                topic TEXT,
                notes TEXT,
                is_mandatory BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (class_id) REFERENCES classes(class_id)
            )
        """)
        
        # 7. Create professional attendance_records table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance_records_new (
                attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                status TEXT DEFAULT 'present' CHECK (status IN ('present', 'absent', 'late', 'excused')),
                check_in_time TIMESTAMP,
                check_out_time TIMESTAMP,
                notes TEXT,
                recorded_by INTEGER, -- professor who recorded
                method TEXT DEFAULT 'manual' CHECK (method IN ('manual', 'facial_recognition', 'rfid', 'qr_code')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES attendance_sessions(session_id),
                FOREIGN KEY (student_id) REFERENCES student_profiles(id),
                FOREIGN KEY (recorded_by) REFERENCES professor_profiles(id),
                UNIQUE(session_id, student_id)
            )
        """)
        
        self.conn.commit()
        logger.info("✅ Professional schema created successfully")
    
    def create_indexes(self):
        """Create comprehensive indexes for performance"""
        cursor = self.conn.cursor()
        
        logger.info("📊 Creating performance indexes")
        
        indexes = [
            # Academic terms
            "CREATE INDEX IF NOT EXISTS idx_academic_terms_active ON academic_terms(is_active)",
            "CREATE INDEX IF NOT EXISTS idx_academic_terms_dates ON academic_terms(start_date, end_date)",
            
            # Departments
            "CREATE INDEX IF NOT EXISTS idx_departments_code ON departments(department_code)",
            "CREATE INDEX IF NOT EXISTS idx_departments_head ON departments(head_professor_id)",
            
            # Subjects
            "CREATE INDEX IF NOT EXISTS idx_subjects_code ON subjects_new(subject_code)",
            "CREATE INDEX IF NOT EXISTS idx_subjects_department ON subjects_new(department_id)",
            "CREATE INDEX IF NOT EXISTS idx_subjects_professor ON subjects_new(professor_id)",
            
            # Classes
            "CREATE INDEX IF NOT EXISTS idx_classes_code ON classes(class_code)",
            "CREATE INDEX IF NOT EXISTS idx_classes_subject ON classes(subject_id)",
            "CREATE INDEX IF NOT EXISTS idx_classes_professor ON classes(professor_id)",
            "CREATE INDEX IF NOT EXISTS idx_classes_term ON classes(term_id)",
            "CREATE INDEX IF NOT EXISTS idx_classes_status ON classes(status)",
            "CREATE INDEX IF NOT EXISTS idx_classes_schedule ON classes(schedule_days, start_time)",
            
            # Student Classes
            "CREATE INDEX IF NOT EXISTS idx_student_classes_student ON student_classes(student_id)",
            "CREATE INDEX IF NOT EXISTS idx_student_classes_class ON student_classes(class_id)",
            "CREATE INDEX IF NOT EXISTS idx_student_classes_status ON student_classes(status)",
            "CREATE INDEX IF NOT EXISTS idx_student_classes_enrollment_date ON student_classes(enrollment_date)",
            
            # Attendance Sessions
            "CREATE INDEX IF NOT EXISTS idx_attendance_sessions_class ON attendance_sessions(class_id)",
            "CREATE INDEX IF NOT EXISTS idx_attendance_sessions_date ON attendance_sessions(session_date)",
            "CREATE INDEX IF NOT EXISTS idx_attendance_sessions_type ON attendance_sessions(session_type)",
            
            # Attendance Records
            "CREATE INDEX IF NOT EXISTS idx_attendance_records_session ON attendance_records_new(session_id)",
            "CREATE INDEX IF NOT EXISTS idx_attendance_records_student ON attendance_records_new(student_id)",
            "CREATE INDEX IF NOT EXISTS idx_attendance_records_status ON attendance_records_new(status)",
            "CREATE INDEX IF NOT EXISTS idx_attendance_records_date ON attendance_records_new(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_attendance_records_method ON attendance_records_new(method)",
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
        
        self.conn.commit()
        logger.info("✅ Performance indexes created")
    
    def populate_professional_data(self):
        """Populate the new professional structure with existing data"""
        cursor = self.conn.cursor()
        
        logger.info("📥 Migrating existing data to professional structure")
        
        # 1. Create default academic term
        cursor.execute("""
            INSERT OR IGNORE INTO academic_terms (term_name, start_date, end_date, is_active)
            VALUES ('Spring 2025', '2025-01-01', '2025-06-30', 1)
        """)
        
        # 2. Create default department
        cursor.execute("""
            INSERT OR IGNORE INTO departments (department_code, department_name, description)
            VALUES ('GEN', 'General Education', 'General education courses')
        """)
        
        # 3. Migrate subjects data
        cursor.execute("""
            INSERT OR IGNORE INTO subjects_new (subject_code, subject_name, description, credits, department_id, professor_id)
            SELECT 
                CASE 
                    WHEN name IS NOT NULL THEN UPPER(SUBSTR(name, 1, 3)) || '_' || id
                    ELSE 'SUB_' || id
                END as subject_code,
                COALESCE(name, 'Subject ' || id) as subject_name,
                COALESCE(description, 'Auto-migrated subject') as description,
                COALESCE(credit_hours, 3) as credits,
                1 as department_id, -- Default to General Education
                NULL as professor_id -- No professor_id in current subjects table
            FROM subjects
        """)
        
        # 4. Create classes from class_schedules
        cursor.execute("""
            INSERT OR IGNORE INTO classes (class_code, subject_id, professor_id, term_id, section, room, schedule_days, start_time, end_time)
            SELECT 
                'CLS_' || cs.id as class_code,
                COALESCE(cs.subject_id, s.subject_id) as subject_id,
                1 as professor_id, -- Default professor - will need to be updated
                1 as term_id, -- Default term
                'A' as section,
                cs.room,
                '["' || cs.day || '"]' as schedule_days,
                cs.start_time,
                cs.end_time
            FROM class_schedules cs
            LEFT JOIN subjects_new s ON cs.subject_id = s.subject_id
        """)
        
        # 5. Enroll all students in all classes (for now)
        cursor.execute("""
            INSERT OR IGNORE INTO student_classes (student_id, class_id, enrollment_date, status)
            SELECT 
                sp.id as student_id,
                c.class_id,
                DATE('now') as enrollment_date,
                'enrolled' as status
            FROM student_profiles sp
            CROSS JOIN classes c
            WHERE sp.id IS NOT NULL
        """)
        
        # 6. Create attendance sessions from existing attendance records
        cursor.execute("""
            INSERT OR IGNORE INTO attendance_sessions (class_id, session_date, session_time, session_type, topic)
            SELECT DISTINCT
                c.class_id,
                DATE(ar.timestamp) as session_date,
                TIME(ar.timestamp) as session_time,
                'lecture' as session_type,
                'Auto-created session' as topic
            FROM attendance_records ar
            JOIN student_profiles sp ON ar.student_username = sp.username
            JOIN classes c ON 1=1  -- For now, assign to first class - can be improved
            LIMIT 50  -- Limit to avoid too many sessions
        """)
        
        # 7. Migrate attendance records
        cursor.execute("""
            INSERT OR IGNORE INTO attendance_records_new (session_id, student_id, status, check_in_time, method)
            SELECT 
                ats.session_id,
                sp.id as student_id,
                CASE 
                    WHEN ar.status = '1' OR ar.status = 'present' THEN 'present'
                    ELSE 'absent'
                END as status,
                ar.timestamp as check_in_time,
                'facial_recognition' as method
            FROM attendance_records ar
            JOIN student_profiles sp ON ar.student_username = sp.username
            JOIN attendance_sessions ats ON DATE(ar.timestamp) = ats.session_date
            LIMIT 1000  -- Limit migration for performance
        """)
        
        self.conn.commit()
        logger.info("✅ Data migration completed")
        
        # Re-enable foreign keys after migration
        self.conn.execute("PRAGMA foreign_keys = ON")
    
    def create_professional_views(self):
        """Create professional views for easy data access"""
        cursor = self.conn.cursor()
        
        logger.info("👁️  Creating professional views")
        
        # Student enrollment view
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS v_student_enrollments AS
            SELECT 
                sp.id as student_id,
                sp.username,
                sp.name as student_name,
                sp.student_id as student_number,
                c.class_code,
                s.subject_name,
                s.subject_code,
                sc.status as enrollment_status,
                sc.grade,
                sc.attendance_percentage,
                sc.enrollment_date,
                p.name as professor_name,
                t.term_name,
                d.department_name
            FROM student_classes sc
            JOIN student_profiles sp ON sc.student_id = sp.id
            JOIN classes c ON sc.class_id = c.class_id
            JOIN subjects_new s ON c.subject_id = s.subject_id
            JOIN professor_profiles p ON c.professor_id = p.id
            JOIN academic_terms t ON c.term_id = t.term_id
            JOIN departments d ON s.department_id = d.department_id
        """)
        
        # Class roster view
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS v_class_rosters AS
            SELECT 
                c.class_code,
                c.section,
                s.subject_name,
                s.subject_code,
                p.name as professor_name,
                COUNT(sc.student_id) as enrolled_students,
                c.max_students,
                c.room,
                c.schedule_days,
                c.start_time,
                c.end_time,
                t.term_name,
                c.status as class_status
            FROM classes c
            JOIN subjects_new s ON c.subject_id = s.subject_id
            JOIN professor_profiles p ON c.professor_id = p.id
            JOIN academic_terms t ON c.term_id = t.term_id
            LEFT JOIN student_classes sc ON c.class_id = sc.class_id AND sc.status = 'enrolled'
            GROUP BY c.class_id
        """)
        
        # Attendance summary view
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS v_attendance_summary AS
            SELECT 
                sp.username,
                sp.name as student_name,
                c.class_code,
                s.subject_name,
                COUNT(arn.attendance_id) as total_sessions,
                SUM(CASE WHEN arn.status = 'present' THEN 1 ELSE 0 END) as present_count,
                SUM(CASE WHEN arn.status = 'absent' THEN 1 ELSE 0 END) as absent_count,
                SUM(CASE WHEN arn.status = 'late' THEN 1 ELSE 0 END) as late_count,
                ROUND(
                    (SUM(CASE WHEN arn.status = 'present' THEN 1 ELSE 0 END) * 100.0) / 
                    NULLIF(COUNT(arn.attendance_id), 0), 2
                ) as attendance_percentage
            FROM student_profiles sp
            JOIN student_classes sc ON sp.id = sc.student_id
            JOIN classes c ON sc.class_id = c.class_id
            JOIN subjects_new s ON c.subject_id = s.subject_id
            LEFT JOIN attendance_sessions ats ON c.class_id = ats.class_id
            LEFT JOIN attendance_records_new arn ON ats.session_id = arn.session_id AND sp.id = arn.student_id
            GROUP BY sp.id, c.class_id
        """)
        
        # Professor teaching load view
        cursor.execute("""
            CREATE VIEW IF NOT EXISTS v_professor_teaching_load AS
            SELECT 
                p.id as professor_id,
                p.username as professor_username,
                p.name as professor_name,
                COUNT(DISTINCT c.class_id) as classes_taught,
                COUNT(DISTINCT s.subject_id) as subjects_taught,
                COUNT(DISTINCT sc.student_id) as total_students,
                SUM(s.credits) as total_credits,
                t.term_name
            FROM professor_profiles p
            JOIN classes c ON p.id = c.professor_id
            JOIN subjects_new s ON c.subject_id = s.subject_id
            JOIN academic_terms t ON c.term_id = t.term_id
            LEFT JOIN student_classes sc ON c.class_id = sc.class_id AND sc.status = 'enrolled'
            WHERE c.status = 'active'
            GROUP BY p.id, t.term_id
        """)
        
        self.conn.commit()
        logger.info("✅ Professional views created")
    
    def generate_restructure_report(self):
        """Generate comprehensive restructure report"""
        cursor = self.conn.cursor()
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'database_structure': {},
            'migration_summary': {},
            'performance_metrics': {}
        }
        
        # Get table counts
        tables = [
            'academic_terms', 'departments', 'subjects_new', 'classes', 
            'student_classes', 'attendance_sessions', 'attendance_records_new',
            'student_profiles', 'professor_profiles'
        ]
        
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                report['database_structure'][table] = count
            except sqlite3.OperationalError:
                report['database_structure'][table] = 'Not found'
        
        # Get view counts
        views = ['v_student_enrollments', 'v_class_rosters', 'v_attendance_summary', 'v_professor_teaching_load']
        for view in views:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {view}")
                count = cursor.fetchone()[0]
                report['database_structure'][view] = count
            except sqlite3.OperationalError:
                report['database_structure'][view] = 'Not found'
        
        return report
    
    def run_restructure(self):
        """Run the complete professional database restructure"""
        try:
            self.connect()
            
            print("🚀 Starting Professional Database Restructure")
            print("=" * 60)
            
            # Analyze current structure
            current_structure = self.analyze_current_structure()
            print(f"📊 Current database has {len(current_structure)} tables")
            
            # Create backup
            backup_file = self.backup_database()
            print(f"💾 Backup created: {backup_file}")
            
            # Create professional schema
            self.create_professional_schema()
            
            # Create indexes
            self.create_indexes()
            
            # Populate data
            self.populate_professional_data()
            
            # Create views
            self.create_professional_views()
            
            # Generate report
            report = self.generate_restructure_report()
            
            print("\n✅ PROFESSIONAL DATABASE RESTRUCTURE COMPLETE")
            print("=" * 60)
            print("📊 New Database Structure:")
            for table, count in report['database_structure'].items():
                print(f"  • {table}: {count} records")
            
            print(f"\n📋 Full report saved to: professional_restructure_report.json")
            
            with open('professional_restructure_report.json', 'w') as f:
                json.dump(report, f, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"Error during restructure: {e}")
            return False
        finally:
            self.close()

if __name__ == "__main__":
    restructure = ProfessionalDatabaseRestructure()
    success = restructure.run_restructure()
    
    if success:
        print("\n🎉 Database successfully restructured!")
        print("💡 Your database now has a professional academic structure with:")
        print("   • Proper academic terms and departments")
        print("   • Professional class management")
        print("   • Comprehensive student enrollment system")
        print("   • Advanced attendance tracking")
        print("   • Performance-optimized indexes")
        print("   • Professional reporting views")
    else:
        print("\n❌ Restructure failed. Check logs for details.")
