-- Migration: Initial schema
-- Version: 20230801000000
-- Created: 2023-08-01 00:00:00

-- Create user_accounts table with secure password fields
CREATE TABLE IF NOT EXISTS user_accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    password_hash TEXT,
    salt TEXT,
    role TEXT NOT NULL,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create student_profiles table
CREATE TABLE IF NOT EXISTS student_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    student_id TEXT UNIQUE,
    section TEXT,
    email TEXT,
    phone TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (username) REFERENCES user_accounts(username)
);

-- Create professor_profiles table
CREATE TABLE IF NOT EXISTS professor_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    department TEXT,
    email TEXT,
    phone TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (username) REFERENCES user_accounts(username)
);

-- Create subjects table with consistent column naming
CREATE TABLE IF NOT EXISTS subjects (
    subject_id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_name TEXT NOT NULL,
    course_code TEXT,
    credit_hours INTEGER DEFAULT 3,
    description TEXT
);

-- Create class_schedules table
CREATE TABLE IF NOT EXISTS class_schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    day TEXT NOT NULL,
    subject TEXT NOT NULL,
    subject_id INTEGER,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    type TEXT DEFAULT 'lec',
    room TEXT,
    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id)
);

-- Create professor_subject_assignments table
CREATE TABLE IF NOT EXISTS professor_subject_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    professor_username TEXT NOT NULL,
    subject_id INTEGER NOT NULL,
    assigned_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(professor_username, subject_id),
    FOREIGN KEY (professor_username) REFERENCES user_accounts(username),
    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id)
);

-- Create teacher_subjects table for backward compatibility
CREATE TABLE IF NOT EXISTS teacher_subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    teacher_name TEXT,
    subject_id INTEGER,
    UNIQUE(teacher_name, subject_id),
    FOREIGN KEY (teacher_name) REFERENCES user_accounts(username)
);

-- Create class_attendance table
CREATE TABLE IF NOT EXISTS class_attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_name TEXT NOT NULL,
    class_date TEXT NOT NULL,
    subject TEXT NOT NULL,
    subject_id INTEGER,
    start_time TEXT,
    end_time TEXT,
    attended INTEGER DEFAULT 0,
    type TEXT DEFAULT 'lec',
    FOREIGN KEY (student_name) REFERENCES user_accounts(username),
    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id)
);

-- Create attendance_records table (main format)
CREATE TABLE IF NOT EXISTS attendance_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    name TEXT,  
    student_name TEXT,
    timestamp TIMESTAMP NOT NULL,
    confidence REAL DEFAULT 1.0,
    device_id TEXT,
    day_of_week TEXT,
    FOREIGN KEY (username) REFERENCES user_accounts(username)
);

-- Create attendance_log view for compatibility 
CREATE VIEW IF NOT EXISTS attendance_log AS
SELECT * FROM attendance_records;

-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_user_accounts_username ON user_accounts(username);
CREATE INDEX IF NOT EXISTS idx_student_profiles_username ON student_profiles(username);
CREATE INDEX IF NOT EXISTS idx_professor_profiles_username ON professor_profiles(username);
CREATE INDEX IF NOT EXISTS idx_class_attendance_student ON class_attendance(student_name);
CREATE INDEX IF NOT EXISTS idx_class_attendance_subject ON class_attendance(subject);
CREATE INDEX IF NOT EXISTS idx_class_attendance_date ON class_attendance(class_date);
CREATE INDEX IF NOT EXISTS idx_attendance_records_username ON attendance_records(username);
CREATE INDEX IF NOT EXISTS idx_attendance_records_timestamp ON attendance_records(timestamp);

-- Create configuration table for system settings
CREATE TABLE IF NOT EXISTS system_config (
    key TEXT PRIMARY KEY,
    value TEXT,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Initialize default system config
INSERT OR IGNORE INTO system_config (key, value, description) VALUES
('backup_retention_days', '7', 'Number of days to keep database backups'),
('auto_backup_interval', '24', 'Hours between automatic database backups'),
('min_password_length', '8', 'Minimum required password length'),
('enable_password_security', 'true', 'Enable secure password hashing'),
('enable_debug_logs', 'false', 'Enable detailed debug logging');

-- Insert default admin user if not exists
INSERT OR IGNORE INTO user_accounts (username, password, role)
VALUES ('admin', 'admin', 'admin');
