from datetime import datetime, time

def convert_to_ampm_format(time_str):
    """
    Convert time string to AM/PM format
    
    Handles both 24-hour format and existing AM/PM format
    
    Args:
        time_str (str): Time string in either "HH:MM" or "HH:MM AM/PM" format
        
    Returns:
        str: Time in "HH:MM AM/PM" format
    """
    try:
        # Check if already in AM/PM format
        if " AM" in time_str or " PM" in time_str:
            return time_str
        
        # Try parsing as 24-hour format
        time_obj = datetime.strptime(time_str, "%H:%M").time()
        return time_obj.strftime("%I:%M %p")
    except ValueError:
        # Try other possible formats
        try:
            time_obj = datetime.strptime(time_str, "%H:%M:%S").time()
            return time_obj.strftime("%I:%M %p")
        except ValueError:
            # Return original if can't parse
            return time_str

def convert_to_24hour_format(time_str):
    """
    Convert time string from AM/PM to 24-hour format
    
    Args:
        time_str (str): Time string in "HH:MM AM/PM" format
        
    Returns:
        str: Time in "HH:MM" format
    """
    try:
        # Check if already in 24-hour format
        if " AM" not in time_str and " PM" not in time_str:
            return time_str
            
        time_obj = datetime.strptime(time_str, "%I:%M %p").time()
        return time_obj.strftime("%H:%M")
    except ValueError:
        # Return original if can't parse
        return time_str

def time_between(test_time, start_time, end_time):
    """
    Check if test_time is between start_time and end_time
    
    Works with both 24-hour and AM/PM formats
    
    Args:
        test_time (str): Time to test
        start_time (str): Start time
        end_time (str): End time
        
    Returns:
        bool: True if test_time is between start and end times
    """
    # Convert all times to datetime.time objects for comparison
    try:
        # First, ensure all times are in 24-hour format for comparison
        test_24h = convert_to_24hour_format(test_time)
        start_24h = convert_to_24hour_format(start_time)
        end_24h = convert_to_24hour_format(end_time)
        
        # Parse as time objects
        test_obj = datetime.strptime(test_24h, "%H:%M").time()
        start_obj = datetime.strptime(start_24h, "%H:%M").time()
        end_obj = datetime.strptime(end_24h, "%H:%M").time()
        
        # Compare times
        return start_obj <= test_obj <= end_obj
    except ValueError:
        # If parsing fails, return False
        return False

def get_current_time_ampm():
    """Get current time in AM/PM format"""
    return datetime.now().strftime("%I:%M %p")

def normalize_time_format(time_str):
    """
    Normalize time format for consistent storage
    
    - Ensures times are stored in AM/PM format
    - Handles various input formats
    - Returns a standardized format
    
    Args:
        time_str (str): Time string in any reasonable format
        
    Returns:
        str: Time in standardized "HH:MM AM/PM" format
    """
    try:
        # Try various formats
        for fmt in ["%H:%M", "%H:%M:%S", "%I:%M %p", "%I:%M%p", "%I:%M %P", "%I:%M%P", "%I%p"]:
            try:
                time_obj = datetime.strptime(time_str, fmt).time()
                return time_obj.strftime("%I:%M %p")
            except ValueError:
                continue
        
        # If all parsing attempts fail
        return time_str
    except Exception:
        return time_str

def format_datetime_for_db(date_str, time_str):
    """
    Combine date and time strings into a datetime string format suitable for SQLite
    
    Args:
        date_str (str): Date in YYYY-MM-DD format
        time_str (str): Time in either 12 or 24 hour format
    
    Returns:
        str: Datetime string in SQLite compatible format
    """
    try:
        # Ensure time is normalized
        time_str = normalize_time_format(time_str)
        
        # Combine date and time
        datetime_str = f"{date_str} {time_str}"
        
        # Parse as datetime
        if "AM" in datetime_str or "PM" in datetime_str:
            dt_obj = datetime.strptime(datetime_str, "%Y-%m-%d %I:%M %p")
        else:
            dt_obj = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
            
        # Return in SQLite format
        return dt_obj.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        # If parsing fails, return original
        return f"{date_str} {time_str}"
