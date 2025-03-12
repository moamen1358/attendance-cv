
-- Begin transaction for atomic operations
BEGIN TRANSACTION;

-- Keep a record of what we're doing
CREATE TABLE IF NOT EXISTS cleanup_log (
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    action TEXT,
    details TEXT
);

-- Log the start
INSERT INTO cleanup_log (action, details) 
VALUES ('cleanup_start', 'Starting database cleanup');

-- Drop old tables that have been replaced by newer ones
DROP TABLE IF EXISTS students;
INSERT INTO cleanup_log (action, details) 
VALUES ('drop_table', 'Dropped students table - replaced by student_profiles');

DROP TABLE IF EXISTS users;
INSERT INTO cleanup_log (action, details) 
VALUES ('drop_table', 'Dropped users table - replaced by user_accounts');

DROP TABLE IF EXISTS presidents_embeds;
INSERT INTO cleanup_log (action, details) 
VALUES ('drop_table', 'Dropped presidents_embeds table - replaced by facial_recognition_data');

DROP TABLE IF EXISTS attendance_log;
INSERT INTO cleanup_log (action, details) 
VALUES ('drop_table', 'Dropped attendance_log table - replaced by attendance_records');

DROP TABLE IF EXISTS control_4;
INSERT INTO cleanup_log (action, details) 
VALUES ('drop_table', 'Dropped control_4 table - replaced by class_schedules');

DROP TABLE IF EXISTS class_attendance;
INSERT INTO cleanup_log (action, details) 
VALUES ('drop_table', 'Dropped class_attendance table - replaced by class_attendance_records');

-- Drop any temporary tables
DROP TABLE IF EXISTS temp_view;
DROP TABLE IF EXISTS class_schedules_temp;
DROP TABLE IF EXISTS temp_students;
DROP TABLE IF EXISTS temp_users;

-- Create compatibility views if needed
CREATE VIEW IF NOT EXISTS control_4 AS
SELECT subject, type, day, start_time, end_time, section, teacher, room
FROM class_schedules;

INSERT INTO cleanup_log (action, details) 
VALUES ('create_view', 'Created control_4 view for compatibility');

-- Log the end
INSERT INTO cleanup_log (action, details) 
VALUES ('cleanup_end', 'Database cleanup completed');

-- Show the log
SELECT * FROM cleanup_log ORDER BY timestamp DESC;

-- Commit all changes
COMMIT;

-- Show what tables remain
SELECT 
    type, 
    name,
    sql
FROM sqlite_master 
WHERE type IN ('table','view') 
AND name NOT LIKE 'sqlite_%'
ORDER BY type, name;
