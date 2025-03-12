
-- Begin transaction for atomic operations
BEGIN TRANSACTION;

-- Drop existing tables and views
DROP TABLE IF EXISTS class_schedules;
DROP VIEW IF EXISTS control_4;

-- Create new table with proper structure
CREATE TABLE class_schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject TEXT NOT NULL,
    day TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    type TEXT NOT NULL,
    section TEXT,
    teacher TEXT,
    room TEXT,
    active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indices for better performance
CREATE INDEX idx_schedules_subject ON class_schedules(subject);
CREATE INDEX idx_schedules_day ON class_schedules(day);

-- Insert sample data with SEC 1 and SEC 2 sections
INSERT INTO class_schedules (subject, day, start_time, end_time, type, section, teacher, room) VALUES
('Advanced Mathematics', 'Monday', '9:00 AM', '11:00 AM', 'lec', 'SEC 1', 'Dr. Alexander Smith', 'Hall A'),
('Advanced Mathematics', 'Wednesday', '2:00 PM', '3:30 PM', 'sec', 'SEC 2', 'Prof. Linda Johnson', 'Room 201'),
('Computer Science', 'Tuesday', '10:00 AM', '12:00 PM', 'lec', 'SEC 1', 'Dr. Rebecca Williams', 'Hall B'),
('Computer Science', 'Thursday', '1:00 PM', '3:00 PM', 'lab', 'SEC 2', 'Dr. Rebecca Williams', 'Lab 101'),
('Physics', 'Monday', '1:00 PM', '3:00 PM', 'lec', 'SEC 1', 'Dr. Thomas Brown', 'Hall C'),
('Physics', 'Friday', '10:00 AM', '12:00 PM', 'sec', 'SEC 2', 'Prof. Sarah Davis', 'Lab 202'),
('Engineering', 'Tuesday', '2:00 PM', '4:00 PM', 'lec', 'SEC 1', 'Dr. Emily Martin', 'Hall D'),
('Engineering', 'Thursday', '9:00 AM', '11:00 AM', 'lab', 'SEC 2', 'Dr. Emily Martin', 'Workshop'),
('Statistics', 'Wednesday', '9:00 AM', '11:00 AM', 'lec', 'SEC 1', 'Prof. Michael Taylor', 'Hall E'),
('Statistics', 'Friday', '1:00 PM', '3:00 PM', 'sec', 'SEC 2', 'Prof. Michael Taylor', 'Room 303');

-- Create a view for backward compatibility
CREATE VIEW control_4 AS
SELECT subject, type, day, start_time, end_time, section, teacher, room
FROM class_schedules;

-- Commit all changes
COMMIT;

-- Verify data exists
SELECT COUNT(*) AS record_count FROM class_schedules;

-- Show sample data
SELECT * FROM class_schedules LIMIT 5;
