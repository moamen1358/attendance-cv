import streamlit as st
import traceback
import logging
import json
import os
import sys
from datetime import datetime
from functools import wraps

# Configure logging
log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_file = os.path.join(log_dir, 'app_errors.log')
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Error categories
ERROR_CATEGORIES = {
    'database': {
        'title': 'Database Error',
        'message': 'There was an issue accessing the database. Please try again later.',
        'color': 'red',
        'icon': '🛢️'
    },
    'auth': {
        'title': 'Authentication Error',
        'message': 'There was a problem with your authentication. Please log in again.',
        'color': 'orange',
        'icon': '🔒'
    },
    'input': {
        'title': 'Input Error',
        'message': 'Please check your input and try again.',
        'color': 'yellow',
        'icon': '⚠️'
    },
    'system': {
        'title': 'System Error',
        'message': 'A system error occurred. Please contact support if the problem persists.',
        'color': 'red',
        'icon': '⚙️'
    },
    'permission': {
        'title': 'Permission Error',
        'message': 'You do not have permission to access this resource.',
        'color': 'orange',
        'icon': '🚫'
    }
}

def categorize_error(error):
    """Categorize an error based on its type and message"""
    error_str = str(error).lower()
    
    if isinstance(error, sqlite3.Error) or 'database' in error_str or 'sql' in error_str:
        return 'database'
    elif 'permission' in error_str or 'access' in error_str or 'denied' in error_str:
        return 'permission'
    elif 'auth' in error_str or 'login' in error_str or 'password' in error_str or 'credential' in error_str:
        return 'auth'
    elif 'invalid' in error_str or 'required' in error_str or 'missing' in error_str or 'input' in error_str:
        return 'input'
    else:
        return 'system'

def log_error(error, category='system', user=None, additional_info=None):
    """Log an error with detailed information"""
    error_data = {
        'error': str(error),
        'error_type': error.__class__.__name__,
        'traceback': traceback.format_exc(),
        'category': category,
        'timestamp': datetime.now().isoformat(),
        'user': user or st.session_state.get('username', 'unknown'),
        'additional_info': additional_info or {}
    }
    
    # Log to file
    logger.error(json.dumps(error_data, default=str))
    
    # Return error data (could be used for display or analytics)
    return error_data

def show_error_message(error=None, category='system', custom_message=None, show_details=False):
    """Display a user-friendly error message in the Streamlit UI"""
    error_info = ERROR_CATEGORIES.get(category, ERROR_CATEGORIES['system'])
    
    # Base error container
    st.error(f"{error_info['icon']} **{error_info['title']}**")
    
    # Show custom message or default message
    st.write(custom_message or error_info['message'])
    
    # Add developer contact info
    st.write("If this problem persists, please contact the administrator.")
    
    # Show technical details if requested and available
    if show_details and error:
        with st.expander("Technical Details"):
            st.code(f"Error Type: {error.__class__.__name__}\n\nError Message: {str(error)}")

def error_boundary(func):
    """Decorator to handle errors in Streamlit pages"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Determine error category
            category = categorize_error(e)
            
            # Log the error
            error_data = log_error(
                error=e,
                category=category,
                user=st.session_state.get('username', 'unknown'),
                additional_info={
                    'function': func.__name__,
                    'arguments': str(args),
                    'page': st.session_state.get('current_page', 'unknown')
                }
            )
            
            # Show error message to user
            show_error_message(
                error=e,
                category=category,
                show_details=st.session_state.get('user_role') == 'admin'
            )
            
            # For admin users, show more details
            if st.session_state.get('user_role') == 'admin':
                with st.expander("Error Details (Admin Only)"):
                    st.json(error_data)
    
    return wrapper

# Context manager for error handling
class ErrorContext:
    def __init__(self, operation_name="Operation", category=None):
        self.operation_name = operation_name
        self.category = category
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is not None:
            # Determine error category
            category = self.category or categorize_error(exc_value)
            
            # Log the error
            log_error(
                error=exc_value,
                category=category,
                additional_info={'operation': self.operation_name}
            )
            
            # Show error message to user
            show_error_message(
                error=exc_value,
                category=category,
                custom_message=f"Error during {self.operation_name}: {str(exc_value)}",
                show_details=st.session_state.get('user_role') == 'admin'
            )
            
            # Handled the exception
            return True
