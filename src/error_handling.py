"""
Error handling utilities for consistent error management across the application.

This module provides decorators and context managers for error handling,
ensuring consistent error reporting and user feedback.
"""
import streamlit as st
import traceback
import logging
from functools import wraps
from typing import Callable, Any, Dict, Optional

# Setup logging
logger = logging.getLogger(__name__)

def handle_errors(func: Callable) -> Callable:
    """
    Decorator to handle errors in functions
    
    Args:
        func: The function to decorate
        
    Returns:
        Wrapped function with error handling
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_message = str(e)
            logger.error(f"Error in {func.__name__}: {error_message}")
            logger.error(traceback.format_exc())
            
            # Display user-friendly error in Streamlit
            st.error(f"An error occurred: {error_message}")
            
            # Return None or appropriate default value
            return None
    
    return wrapper

class ErrorContext:
    """Context manager for handling errors in a block of code"""
    
    def __init__(self, operation_name: str, show_error: bool = True):
        """
        Initialize the context manager
        
        Args:
            operation_name: Name of the operation for error messages
            show_error: Whether to display error in UI
        """
        self.operation_name = operation_name
        self.show_error = show_error
    
    def __enter__(self) -> 'ErrorContext':
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if exc_type is not None:
            error_message = str(exc_val)
            logger.error(f"Error in {self.operation_name}: {error_message}")
            logger.error(traceback.format_exc())
            
            if self.show_error:
                st.error(f"An error occurred during {self.operation_name}: {error_message}")
            
            # Return True to suppress the exception
            return True
        
        # Return False to propagate the exception
        return False

def show_error_message(message: str, exception: Optional[Exception] = None) -> None:
    """
    Display a user-friendly error message
    
    Args:
        message: User-friendly error message
        exception: Optional exception for logging
    """
    if exception:
        logger.error(f"{message}: {str(exception)}")
        logger.error(traceback.format_exc())
    
    st.error(message)
