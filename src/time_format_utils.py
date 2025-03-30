"""
Time Format Utilities Module

This module provides utilities for handling time formats and calculations.
"""
from datetime import datetime, timedelta
import re

def normalize_time_format(time_str):
    """
    Normalize a time string to ensure it's in a consistent format (HH:MM AM/PM)
    
    Args:
        time_str (str): Time string in various formats
        
    Returns:
        str: Normalized time string in "HH:MM AM/PM" format
    """
    # Already in correct format
    if re.match(r'\d{1,2}:\d{2}\s[AP]M', time_str):
        return time_str
    
    # 24-hour format (HH:MM)
    if re.match(r'\d{1,2}:\d{2}$', time_str):
        try:
            dt = datetime.strptime(time_str, "%H:%M")
            return dt.strftime("%I:%M %p")
        except:
            pass
    
    # Try other common formats
    formats = [
        "%H:%M:%S",  # 24-hour with seconds
        "%I:%M:%S %p",  # 12-hour with seconds
        "%I%p",  # Like 9AM
        "%I:%M%p"  # Like 9:30AM (no space)
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(time_str, fmt)
            return dt.strftime("%I:%M %p")
        except:
            continue
    
    # Return original if no format matches
    print(f"Warning: Could not normalize time format: {time_str}")
    return time_str

def convert_to_ampm_format(time_str):
    """
    Convert time string to AM/PM format
    
    Args:
        time_str (str): Time string, likely in 24-hour format
        
    Returns:
        str: Time string in AM/PM format
    """
    try:
        # Handle 24-hour format (HH:MM)
        if re.match(r'\d{1,2}:\d{2}$', time_str):
            dt = datetime.strptime(time_str, "%H:%M")
            return dt.strftime("%I:%M %p")
        
        # If already in AM/PM format, return as is
        return time_str
    except:
        # Return original if conversion fails
        return time_str

def time_between(start_time, end_time):
    """
    Calculate duration between two time strings
    
    Args:
        start_time (str): Start time
        end_time (str): End time
        
    Returns:
        str: Duration in hours and minutes (e.g., "2h 30m")
    """
    try:
        # Normalize both times to ensure consistent format
        start_time = normalize_time_format(start_time)
        end_time = normalize_time_format(end_time)
        
        # Parse times
        start = datetime.strptime(start_time, "%I:%M %p")
        end = datetime.strptime(end_time, "%I:%M %p")
        
        # Calculate difference
        diff = end - start
        
        # Handle negative time (crossing midnight)
        if diff.total_seconds() < 0:
            end = end + timedelta(days=1)
            diff = end - start
        
        # Calculate hours and minutes
        hours, remainder = divmod(diff.total_seconds(), 3600)
        minutes = remainder // 60
        
        # Format result
        if hours > 0:
            return f"{int(hours)}h {int(minutes)}m"
        else:
            return f"{int(minutes)}m"
    except:
        # Return fallback if calculation fails
        return "Unknown"
