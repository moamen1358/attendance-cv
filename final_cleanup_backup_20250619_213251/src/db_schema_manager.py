import sqlite3
import os
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database path
DATABASE_PATH = 'attendance_system.db'

class SchemaManager:
    """Centralized manager for database schema operations"""
    
    def __init__(self, db_path=DATABASE_PATH):
        self.db_path = db_path
        self.migrations_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'migrations')
        # Create migrations directory if it doesn't exist
        if not os.path.exists(self.migrations_dir):
            os.makedirs(self.migrations_dir)
    
    def get_connection(self):
        """Get a database connection"""
        return sqlite3.connect(self.db_path)
    
    def init_migration_table(self):
        """Initialize the migration tracking table"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version TEXT UNIQUE NOT NULL,
                description TEXT,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            conn.commit()
            logger.info("Migration tracking table initialized")
        except Exception as e:
            conn.rollback()
            logger.error(f"Error initializing migration table: {e}")
        finally:
            conn.close()
    
    def get_applied_migrations(self):
        """Get list of already applied migrations"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT version FROM schema_migrations ORDER BY version")
            return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error retrieving applied migrations: {e}")
            return []
        finally:
            conn.close()
    
    def apply_migrations(self):
        """Apply any pending migrations"""
        self.init_migration_table()
        applied = self.get_applied_migrations()
        
        # Get all migration files
        migrations = []
        for file in os.listdir(self.migrations_dir):
            if file.endswith('.sql') and file.startswith('V'):
                version = file.split('__')[0][1:]  # Extract version number
                if version not in applied:
                    migrations.append((version, file))
        
        # Sort migrations by version
        migrations.sort(key=lambda x: x[0])
        
        # Apply each migration
        conn = self.get_connection()
        for version, filename in migrations:
            try:
                # Start transaction
                conn.execute("BEGIN")
                
                # Read and execute migration SQL
                filepath = os.path.join(self.migrations_dir, filename)
                with open(filepath, 'r') as f:
                    sql = f.read()
                
                conn.executescript(sql)
                
                # Record the migration
                description = filename.split('__')[1].replace('.sql', '').replace('_', ' ')
                conn.execute(
                    "INSERT INTO schema_migrations (version, description) VALUES (?, ?)",
                    (version, description)
                )
                
                # Commit transaction
                conn.commit()
                logger.info(f"Applied migration {version}: {description}")
                
            except Exception as e:
                conn.rollback()
                logger.error(f"Error applying migration {version}: {e}")
                break
        
        conn.close()
    
    def create_migration(self, description):
        """Create a new migration file"""
        # Format version as timestamp
        version = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Format description for filename
        safe_desc = description.replace(' ', '_').lower()
        filename = f"V{version}__{safe_desc}.sql"
        filepath = os.path.join(self.migrations_dir, filename)
        
        # Create file with template
        with open(filepath, 'w') as f:
            f.write(f"-- Migration: {description}\n")
            f.write(f"-- Version: {version}\n")
            f.write(f"-- Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("-- Write your SQL migration here\n\n")
        
        logger.info(f"Created new migration file: {filename}")
        return filepath
    
    def ensure_all_tables(self):
        """Ensure all required tables exist in the database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Define essential tables
            essential_tables = {
                'user_accounts': '''
                    CREATE TABLE user_accounts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        salt TEXT NOT NULL,
                        role TEXT NOT NULL,
                        last_login TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''',
                'student_profiles': '''
                    CREATE TABLE student_profiles (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        name TEXT NOT NULL,
                        student_id TEXT UNIQUE,
                        section TEXT,
                        email TEXT,
                        phone TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (username) REFERENCES user_accounts(username)
                    )
                ''',
                'professor_profiles': '''
                    CREATE TABLE professor_profiles (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        name TEXT NOT NULL, 
                        department TEXT,
                        email TEXT,
                        phone TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (username) REFERENCES user_accounts(username)
                    )
                ''',
                'subjects': '''
                    CREATE TABLE subjects (
                        subject_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        subject_name TEXT NOT NULL,
                        course_code TEXT,
                        credit_hours INTEGER DEFAULT 3,
                        description TEXT
                    )
                ''',
                'attendance_records': '''
                    CREATE TABLE attendance_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL,
                        name TEXT,
                        timestamp TIMESTAMP NOT NULL,
                        confidence REAL DEFAULT 1.0,
                        device_id TEXT,
                        day_of_week TEXT,
                        FOREIGN KEY (username) REFERENCES user_accounts(username)
                    )
                '''
            }
            
            # Check existing tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = {row[0] for row in cursor.fetchall()}
            
            # Create missing tables
            for table, create_sql in essential_tables.items():
                if table not in existing_tables:
                    cursor.execute(create_sql)
                    logger.info(f"Created table: {table}")
            
            conn.commit()
            return True
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Error ensuring tables: {e}")
            return False
        finally:
            conn.close()
    
    def validate_schema(self):
        """Validate database schema and fix inconsistencies"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # First ensure all required tables exist
            self.ensure_all_tables()
            
            # Fix common column issues
            fixes = [
                # Add missing columns to user_accounts if needed
                "SELECT 1 FROM pragma_table_info('user_accounts') WHERE name='password_hash'",
                "ALTER TABLE user_accounts ADD COLUMN password_hash TEXT",
                
                "SELECT 1 FROM pragma_table_info('user_accounts') WHERE name='salt'",
                "ALTER TABLE user_accounts ADD COLUMN salt TEXT",
                
                # Add indexes for performance
                "CREATE INDEX IF NOT EXISTS idx_attendance_username ON attendance_records(username)",
                "CREATE INDEX IF NOT EXISTS idx_attendance_timestamp ON attendance_records(timestamp)",
            ]
            
            # Execute fixes in pairs (check, fix if needed)
            for i in range(0, len(fixes), 2):
                check_sql = fixes[i]
                fix_sql = fixes[i+1]
                
                # Check if fix is needed
                cursor.execute(check_sql)
                if not cursor.fetchone():
                    try:
                        cursor.execute(fix_sql)
                        logger.info(f"Applied schema fix: {fix_sql}")
                    except sqlite3.OperationalError:
                        logger.warning(f"Could not apply fix (already exists?): {fix_sql}")
            
            conn.commit()
            return True
        
        except Exception as e:
            conn.rollback()
            logger.error(f"Error validating schema: {e}")
            return False
        finally:
            conn.close()
