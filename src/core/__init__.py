"""
Core functionality for the attendance system.

This package contains core functionality used across the application:
- Authentication & authorization (security.py)
- Error handling (error_handling.py)
- Session management (session_manager.py)
"""

from src.core.error_handling import handle_errors, ErrorContext, show_error_message
from src.core.security import verify_password, password_strength, secure_verify_credentials

__all__ = [
    'handle_errors',
    'ErrorContext',
    'show_error_message',
    'verify_password',
    'password_strength',
    'secure_verify_credentials'
]
