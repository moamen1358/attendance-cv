
-- Begin transaction for atomic operations
BEGIN TRANSACTION;

-- Clear existing data
DELETE FROM class_schedules;

-- Insert updated schedule data with lectures for both sections
-- Advanced Mathematics
INSERT INTO class_schedules (subject, day, start_time, end_time, type, section, teacher, room) VALUES
('Advanced Mathematics', 'Monday', '9:00 AM', '11:00 AM', 'lec', 'SEC 1', 'Dr. Alexander Smith', 'Hall A'),
('Advanced Mathematics', 'Tuesday', '9:00 AM', '11:00 AM', 'lec', 'SEC 2', 'Dr. Alexander Smith', 'Hall A'),
('Advanced Mathematics', 'Wednesday', '2:00 PM', '3:30 PM', 'sec', 'SEC 1', 'Prof. Linda Johnson', 'Room 201'),
('Advanced Mathematics', 'Friday', '2:00 PM', '3:30 PM', 'sec', 'SEC 2', 'Prof. Linda Johnson', 'Room 201');

-- Computer Science
INSERT INTO class_schedules (subject, day, start_time, end_time, type, section, teacher, room) VALUES
('Computer Science', 'Monday', '1:00 PM', '3:00 PM', 'lec', 'SEC 1', 'Dr. Rebecca Williams', 'Hall B'),
('Computer Science', 'Wednesday', '1:00 PM', '3:00 PM', 'lec', 'SEC 2', 'Dr. Rebecca Williams', 'Hall B'),
('Computer Science', 'Tuesday', '10:00 AM', '12:00 PM', 'lab', 'SEC 1', 'Dr. Rebecca Williams', 'Lab 101'),
('Computer Science', 'Thursday', '10:00 AM', '12:00 PM', 'lab', 'SEC 2', 'Dr. Rebecca Williams', 'Lab 101');

-- Physics
INSERT INTO class_schedules (subject, day, start_time, end_time, type, section, teacher, room) VALUES
('Physics', 'Tuesday', '2:00 PM', '4:00 PM', 'lec', 'SEC 1', 'Dr. Thomas Brown', 'Hall C'),
('Physics', 'Thursday', '2:00 PM', '4:00 PM', 'lec', 'SEC 2', 'Dr. Thomas Brown', 'Hall C'),
('Physics', 'Wednesday', '10:00 AM', '12:00 PM', 'sec', 'SEC 1', 'Prof. Sarah Davis', 'Lab 202'),
('Physics', 'Friday', '10:00 AM', '12:00 PM', 'sec', 'SEC 2', 'Prof. Sarah Davis', 'Lab 202');

-- Engineering
INSERT INTO class_schedules (subject, day, start_time, end_time, type, section, teacher, room) VALUES
('Engineering', 'Monday', '10:00 AM', '12:00 PM', 'lec', 'SEC 1', 'Dr. Emily Martin', 'Hall D'),
('Engineering', 'Wednesday', '10:00 AM', '12:00 PM', 'lec', 'SEC 2', 'Dr. Emily Martin', 'Hall D'),
('Engineering', 'Tuesday', '1:00 PM', '3:00 PM', 'lab', 'SEC 1', 'Dr. Emily Martin', 'Workshop'),
('Engineering', 'Thursday', '1:00 PM', '3:00 PM', 'lab', 'SEC 2', 'Dr. Emily Martin', 'Workshop');

-- Statistics
INSERT INTO class_schedules (subject, day, start_time, end_time, type, section, teacher, room) VALUES
('Statistics', 'Thursday', '9:00 AM', '11:00 AM', 'lec', 'SEC 1', 'Prof. Michael Taylor', 'Hall E'),
('Statistics', 'Friday', '9:00 AM', '11:00 AM', 'lec', 'SEC 2', 'Prof. Michael Taylor', 'Hall E'),
('Statistics', 'Monday', '3:00 PM', '5:00 PM', 'sec', 'SEC 1', 'Prof. Michael Taylor', 'Room 303'),
('Statistics', 'Wednesday', '3:00 PM', '5:00 PM', 'sec', 'SEC 2', 'Prof. Michael Taylor', 'Room 303');

-- Commit changes
COMMIT;

-- Verify the schedule
SELECT subject, section, type, COUNT(*) AS count
FROM class_schedules
GROUP BY subject, section, type
ORDER BY subject, section, type;
