"""
Database backup management utilities.

This module provides functionality for backing up and restoring the database.
"""
import os
import shutil
import sqlite3
import zipfile
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Tuple, Optional, Dict, List, Union

from src.constants import DATABASE_PATH, BACKUPS_DIR, BACKUP_RETENTION_DAYS

# Setup logging
logger = logging.getLogger(__name__)

class BackupManager:
    """Manages database backups and restoration"""
    
    def __init__(self, db_path=DATABASE_PATH, backup_dir=BACKUPS_DIR, retention_days=BACKUP_RETENTION_DAYS):
        """
        Initialize the backup manager
        """
        self.db_path = db_path
        self.backup_dir = backup_dir
        self.retention_days = retention_days
        
        # Ensure backup directory exists
        self.backup_dir.mkdir(exist_ok=True)
    
    # ...existing code for create_backup, list_backups, restore_backup, cleanup_old_backups, etc...

# Function to start automatic backup in a separate thread
def start_automatic_backup(interval_hours=24):
    """Start automatic backup in a separate thread"""
    import threading
    
    backup_manager = BackupManager()
    t = threading.Thread(
        target=backup_manager.schedule_automatic_backup,
        args=(interval_hours,),
        daemon=True
    )
    t.start()
    logger.info(f"Automatic backup scheduled every {interval_hours} hours")
