"""
Database models representing key application entities.

This module defines classes that represent the primary database entities,
providing a more object-oriented approach to database access.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any

@dataclass
class User:
    """User model representing a user account"""
    id: int = None
    username: str = None
    role: str = None
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None
    
    @property
    def is_admin(self) -> bool:
        """Check if user is an administrator"""
        return self.role.lower() == 'admin'
    
    @property
    def is_professor(self) -> bool:
        """Check if user is a professor"""
        return self.role.lower() == 'professor'
    
    @property
    def is_student(self) -> bool:
        """Check if user is a student"""
        return self.role.lower() == 'student'

@dataclass
class Student:
    """Student profile model"""
    id: int = None
    username: str = None
    name: str = None
    student_id: str = None
    section: str = None
    email: Optional[str] = None
    phone: Optional[str] = None
    created_at: Optional[datetime] = None

@dataclass
class Professor:
    """Professor profile model"""
    id: int = None
    username: str = None
    name: str = None
    department: str = None
    email: Optional[str] = None
    phone: Optional[str] = None
    created_at: Optional[datetime] = None

@dataclass
class Subject:
    """Subject model"""
    id: int = None
    name: str = None
    course_code: Optional[str] = None
    credit_hours: int = 3
    description: Optional[str] = None

@dataclass
class Attendance:
    """Attendance record model"""
    id: int = None
    username: str = None
    name: Optional[str] = None
    timestamp: datetime = None
    confidence: float = 1.0
    device_id: Optional[str] = None
    day_of_week: Optional[str] = None
    
    @property
    def date_string(self) -> str:
        """Get formatted date string"""
        if self.timestamp:
            return self.timestamp.strftime('%Y-%m-%d')
        return ''
    
    @property
    def time_string(self) -> str:
        """Get formatted time string"""
        if self.timestamp:
            return self.timestamp.strftime('%H:%M:%S')
        return ''
