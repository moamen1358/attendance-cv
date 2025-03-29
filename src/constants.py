"""
Application-wide constants.

This module contains constants used throughout the application.
"""
import os
from pathlib import Path

# Base paths
ROOT_DIR = Path(__file__).parent.parent
SRC_DIR = ROOT_DIR / "src"
DATA_DIR = ROOT_DIR / "data"
MIGRATIONS_DIR = ROOT_DIR / "migrations"
LOGS_DIR = ROOT_DIR / "logs"
BACKUPS_DIR = ROOT_DIR / "backups"
SESSIONS_DIR = ROOT_DIR / ".sessions"

# Create directories if they don't exist
for directory in [DATA_DIR, LOGS_DIR, BACKUPS_DIR, SESSIONS_DIR]:
    directory.mkdir(exist_ok=True)

# Database
DEFAULT_DB_NAME = "attendance_system.db"
DATABASE_PATH = ROOT_DIR / DEFAULT_DB_NAME

# Application settings
APP_NAME = "Attendance Management System"
APP_VERSION = "1.0.0"
APP_ICON = "📊"
DEFAULT_LAYOUT = "wide"
DEFAULT_SIDEBAR_STATE = "auto"

# Time settings
BACKUP_INTERVAL_HOURS = 24
BACKUP_RETENTION_DAYS = 7
SESSION_TIMEOUT_MINUTES = 60

# User roles
ROLE_ADMIN = "admin"
ROLE_PROFESSOR = "professor" 
ROLE_STUDENT = "student"
ROLE_GUEST = "guest"

# Authentication
MIN_PASSWORD_LENGTH = 8
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin"
