import sqlite3
from database_utils import execute_query, execute_query_df
import pandas as pd
import random
from datetime import datetime, timedelta
import time
from time_format_utils import convert_to_ampm_format, normalize_time_format

# Constants
DATABASE_PATH = 'attendance_system.db'

def get_db_connection():
    """Get a connection to the SQLite database"""
    return sqlite3.connect(DATABASE_PATH)

def ensure_user_exists(username="moamen", role="student"):
    """Make sure the user exists in the database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if user exists in user_accounts table
    execute_query("SELECT username FROM user_accounts WHERE username = ?", (username,))
    if not cursor.fetchone():
        print(f"Creating user '{username}'...")
        # Create user
        cursor.execute(
            "INSERT INTO user_accounts (username, password, role) VALUES (?, ?, ?)",
            (username, "password123", role)
        )
        print(f"User '{username}' created with password 'password123'")
    
    # Check if user exists in student_profiles table
    execute_query("SELECT name FROM student_profiles WHERE name = ?", (username,))
    if not cursor.fetchone():
        print(f"Adding '{username}' to student_profiles table...")
        cursor.execute(
            "INSERT INTO student_profiles (name) VALUES (?)",
            (username,)
        )
    
    conn.commit()
    conn.close()

def get_schedule_for_range(start_date, end_date):
    """Get all scheduled classes between start_date and end_date"""
    conn = get_db_connection()
    
    # Create a date range
    dates = []
    current_date = start_date
    while current_date <= end_date:
        dates.append(current_date)
        current_date += timedelta(days=1)
    
    # For each day, get the schedule
    all_classes = []
    
    for date in dates:
        day_name = date.strftime('%A')
        
        query = """
        SELECT subject, start_time, end_time, type
        FROM class_schedules
        WHERE day = ? AND subject != ''
        ORDER BY start_time
        """
        
        cursor = conn.cursor()
        execute_query(query, (day_name,))
        classes = cursor.fetchall()
        
        # Add each class with its date
        for subject, start_time, end_time, class_type in classes:
            all_classes.append({
                'date': date.strftime('%Y-%m-%d'),
                'day_name': day_name,
                'subject': subject,
                'start_time': normalize_time_format(start_time),
                'end_time': normalize_time_format(end_time),
                'type': class_type
            })
    
    conn.close()
    return all_classes

def generate_attendance_logs(username, classes, attendance_rate=0.8):
    """Generate attendance logs for the given classes with specified attendance rate"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get current timestamp for logging
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    print(f"Generating attendance data for {len(classes)} classes...")
    
    # Count for tracking progress
    attended_count = 0
    total_count = 0
    
    # For each class, decide if the student attended and generate logs
    for class_info in classes:
        date = class_info['date']
        subject = class_info['subject']
        start_time = class_info['start_time']
        end_time = class_info['end_time']
        day_name = class_info['day_name']
        
        # Skip future dates
        if datetime.strptime(date, '%Y-%m-%d').date() > datetime.now().date():
            continue
        
        total_count += 1
        
        # Decide if student attended (with some randomness based on subject)
        # Make some subjects have better attendance than others
        subject_factor = sum(ord(c) for c in subject) % 20 / 100  # -0.2 to +0.2 based on subject
        attended = random.random() < (attendance_rate + subject_factor)
        
        if attended:
            attended_count += 1
            
            # Record in class_attendance table
            cursor.execute("""
                INSERT OR REPLACE INTO class_attendance 
                    (student_name, class_date, subject, start_time, end_time, attended)
                VALUES (?, ?, ?, ?, ?, 1)
            """, (username, date, subject, start_time, end_time))
            
            # Generate 1-4 attendance log entries during class time
            class_date_start = f"{date} {start_time}"
            class_date_end = f"{date} {end_time}"
            
            # Parse start and end time
            try:
                # Format time strings for datetime parsing
                if 'AM' in class_date_start or 'PM' in class_date_start:
                    start_dt = datetime.strptime(class_date_start, '%Y-%m-%d %I:%M %p')
                else:
                    start_dt = datetime.strptime(class_date_start, '%Y-%m-%d %H:%M')
                    
                if 'AM' in class_date_end or 'PM' in class_date_end:
                    end_dt = datetime.strptime(class_date_end, '%Y-%m-%d %I:%M %p')
                else:
                    end_dt = datetime.strptime(class_date_end, '%Y-%m-%d %H:%M')
                
                # Generate 1-4 check-ins during class
                num_checkins = random.randint(1, 4)
                
                for _ in range(num_checkins):
                    # Random time during class
                    class_minutes = (end_dt - start_dt).total_seconds() / 60
                    random_minutes = random.uniform(5, class_minutes - 5)  # 5 minutes after start to 5 minutes before end
                    checkin_time = start_dt + timedelta(minutes=random_minutes)
                    
                    # Random confidence level
                    confidence = random.uniform(0.85, 0.99)
                    
                    # Insert log
                    cursor.execute("""
                        INSERT INTO attendance_records 
                            (name, timestamp, confidence, device_id, day_of_week)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        username, 
                        checkin_time.strftime('%Y-%m-%d %H:%M:%S'),
                        confidence,
                        'camera_01',
                        day_name
                    ))
                
            except Exception as e:
                print(f"Error parsing times for {date} {start_time}-{end_time}: {e}")
                continue
        else:
            # Record as absent
            cursor.execute("""
                INSERT OR REPLACE INTO class_attendance 
                    (student_name, class_date, subject, start_time, end_time, attended)
                VALUES (?, ?, ?, ?, ?, 0)
            """, (username, date, subject, start_time, end_time))
    
    # Commit and close
    conn.commit()
    conn.close()
    
    print(f"Generated attendance data: {attended_count}/{total_count} classes attended ({attended_count/total_count*100:.1f}%)")
    return attended_count, total_count

def vary_attendance_by_day(day_name):
    """Vary attendance probability by day of week"""
    # Lower attendance on Mondays and Fridays
    if day_name == "Monday":
        return 0.7  # 70% attendance rate on Mondays
    elif day_name == "Friday":
        return 0.75  # 75% attendance rate on Fridays
    else:
        return 0.85  # 85% attendance rate on other days

def vary_attendance_by_subject(subject):
    """Vary attendance probability by subject"""
    # Example: Better attendance for certain subjects
    if "Math" in subject:
        return 0.9  # 90% attendance for Math
    elif "Science" in subject or "Physics" in subject:
        return 0.85  # 85% attendance for Science/Physics
    elif "History" in subject:
        return 0.7  # 70% attendance for History
    elif "Literature" in subject:
        return 0.75  # 75% attendance for Literature
    else:
        return 0.8  # 80% default attendance

def main():
    username = "moamen"
    
    # First make sure the user exists
    ensure_user_exists(username)
    
    # Clear existing data for this user to avoid duplicates
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print(f"Clearing existing attendance data for user '{username}'...")
    cursor.execute("DELETE FROM attendance_records WHERE name = ?", (username,))
    cursor.execute("DELETE FROM class_attendance WHERE student_name = ?", (username,))
    conn.commit()
    conn.close()
    
    # Generate attendance for the past 30 days
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)
    
    print(f"Fetching class schedule from {start_date} to {end_date}...")
    classes = get_schedule_for_range(start_date, end_date)
    
    print(f"Found {len(classes)} scheduled classes in the date range")
    
    # Create more realistic attendance patterns by varying attendance by day and subject
    for class_info in classes:
        day_factor = vary_attendance_by_day(class_info['day_name'])
        subject_factor = vary_attendance_by_subject(class_info['subject'])
        class_info['attendance_probability'] = (day_factor + subject_factor) / 2
    
    # Generate attendance logs with the varied probabilities
    attended, total = generate_attendance_logs(username, classes)
    
    print(f"Process complete. {attended} out of {total} classes attended.")
    print(f"You can now view analytics for user '{username}'")

if __name__ == "__main__":
    main()
