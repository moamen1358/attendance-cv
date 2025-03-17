
# Optimized Database Schema Documentation

This document describes the optimized minimal database schema implemented in the attendance system.

## Tables Overview

The database has been optimized to use just 6 core tables:

1. **user_accounts** - Unified table for all users (students, professors, admins)
2. **subjects** - Information about courses/subjects
3. **teacher_subjects** - Assigns teachers to subjects
4. **class_schedules** - Schedules for classes
5. **attendance_records** - Records of student attendance
6. **facial_recognition_data** - Facial biometric data for authentication

## Table Schemas

### user_accounts

This table consolidates all user types (students, professors, administrators) into a single table.

```sql
CREATE TABLE user_accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL,  -- 'student', 'professor', or 'admin'
    name TEXT,
    email TEXT,
    department TEXT,     -- For professors
    section TEXT,        -- For students
    student_id TEXT,     -- For students
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

### subjects

This table contains all subject/course information.

```sql
CREATE TABLE subjects (
    subject_id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_name TEXT NOT NULL UNIQUE,
    course_code TEXT,
    credit_hours INTEGER DEFAULT 3,
    description TEXT
);
```

### teacher_subjects

This table creates a many-to-many relationship between teachers and subjects.

```sql
CREATE TABLE teacher_subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    teacher_username TEXT NOT NULL,
    subject_id INTEGER NOT NULL,
    FOREIGN KEY (teacher_username) REFERENCES user_accounts(username),
    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id),
    UNIQUE(teacher_username, subject_id)
);
```

### class_schedules

This table stores information about when and where classes meet.

```sql
CREATE TABLE class_schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id INTEGER NOT NULL,
    subject TEXT NOT NULL,       -- Denormalized for convenience
    day TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    room TEXT,
    type TEXT DEFAULT 'lec',     -- 'lec' or 'sec'
    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id)
);
```

### attendance_records

This table records student attendance for classes.

```sql
CREATE TABLE attendance_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_username TEXT NOT NULL,
    subject_id INTEGER NOT NULL,
    class_date TEXT NOT NULL,
    status TEXT DEFAULT 'present',
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_username) REFERENCES user_accounts(username),
    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id)
);
```

### facial_recognition_data

This table stores biometric data for facial recognition.

```sql
CREATE TABLE facial_recognition_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    facial_features TEXT NOT NULL,
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (username) REFERENCES user_accounts(username)
);
```

## Benefits of the Optimized Schema

1. **Reduced Redundancy**: Consolidates multiple user tables into one
2. **Simplified Queries**: Fewer joins needed for common operations
3. **Better Data Integrity**: Proper foreign key relationships
4. **Improved Performance**: Appropriate indexes on key columns
5. **Easier Maintenance**: Fewer tables to manage and update
