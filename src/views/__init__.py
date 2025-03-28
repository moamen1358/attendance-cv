"""
View modules for different user roles and pages.

This package contains the Streamlit views for different application roles:
- admin: Admin dashboard and management views
- professor: Teacher dashboards and attendance reporting
- student: Student dashboard and attendance records
- reports: Shared reporting components
"""

from enum import Enum

class ViewType(Enum):
    """Types of views available in the application"""
    ADMIN = "admin"
    PROFESSOR = "professor"
    STUDENT = "student"
    LOGIN = "login"

def get_view_for_role(role: str):
    """
    Get the appropriate view function for a user role
    
    Args:
        role: User role (admin, professor, student)
        
    Returns:
        function: View function to display
    """
    if role.lower() == "admin":
        from src.views.admin import show_admin_view
        return show_admin_view
    elif role.lower() == "professor":
        from src.views.professor import show_professor_view
        return show_professor_view
    elif role.lower() == "student":
        from src.views.student import show_student_view
        return show_student_view
    else:
        from src.views.login import show_login_view
        return show_login_view
