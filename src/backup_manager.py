import os
import shutil
import sqlite3
import zipfile
import time
import logging
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
DATABASE_PATH = 'attendance_system.db'
BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backups')
RETENTION_DAYS = 7

class BackupManager:
    """
    Manages database backups and restoration
    """
    
    def __init__(self, db_path=DATABASE_PATH, backup_dir=BACKUP_DIR, retention_days=RETENTION_DAYS):
        """
        Initialize the backup manager
        
        Args:
            db_path (str): Path to the database file
            backup_dir (str): Directory to store backups
            retention_days (int): Number of days to keep backups
        """
        self.db_path = db_path
        self.backup_dir = backup_dir
        self.retention_days = retention_days
        
        # Ensure backup directory exists
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
    
    def create_backup(self, backup_name=None):
        """
        Create a backup of the database
        
        Args:
            backup_name (str, optional): Name for the backup
            
        Returns:
            tuple: (success, message, backup_path)
        """
        try:
            # Check if source database exists
            if not os.path.exists(self.db_path):
                return False, "Database file does not exist", None
            
            # Generate backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if backup_name:
                backup_name = backup_name.replace(" ", "_").replace("/", "-")
                filename = f"{backup_name}_{timestamp}.zip"
            else:
                filename = f"backup_{timestamp}.zip"
            
            backup_path = os.path.join(self.backup_dir, filename)
            
            # Create a connection to the source database
            conn = sqlite3.connect(self.db_path)
            
            # Create a temporary backup file
            temp_backup = os.path.join(self.backup_dir, f"temp_{timestamp}.db")
            
            # Create backup using SQLite's backup API
            src = conn.cursor()
            dest_conn = sqlite3.connect(temp_backup)
            dest = dest_conn.cursor()
            
            # Make sure we have a source database to back up
            src.execute("SELECT COUNT(*) FROM sqlite_master")
            table_count = src.fetchone()[0]
            
            # Create backup
            conn.backup(dest_conn)
            
            # Close connections
            dest_conn.commit()
            dest_conn.close()
            conn.close()
            
            # Create zip file containing the backup
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add database file
                zipf.write(temp_backup, arcname=os.path.basename(self.db_path))
                
                # Add metadata.txt with details about the backup
                metadata_content = f"""Backup created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Database: {os.path.basename(self.db_path)}
Table count: {table_count}
"""
                zipf.writestr("metadata.txt", metadata_content)
            
            # Remove temporary file
            os.remove(temp_backup)
            
            logger.info(f"Backup created successfully: {backup_path}")
            return True, "Backup created successfully", backup_path
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return False, f"Error creating backup: {str(e)}", None
    
    def list_backups(self):
        """
        List available backups
        
        Returns:
            list: List of backup files with metadata
        """
        backups = []
        
        # Ensure backup directory exists
        if not os.path.exists(self.backup_dir):
            return backups
        
        # List all zip files in backup directory
        for filename in os.listdir(self.backup_dir):
            if filename.endswith('.zip') and 'backup_' in filename:
                filepath = os.path.join(self.backup_dir, filename)
                file_info = os.stat(filepath)
                
                # Extract date from filename
                try:
                    # Parse timestamp from the filename
                    date_str = filename.split('_')[-2] + filename.split('_')[-1].split('.')[0]
                    timestamp = datetime.strptime(date_str, "%Y%m%d%H%M%S")
                except Exception:
                    # If parsing fails, use file modification time
                    timestamp = datetime.fromtimestamp(file_info.st_mtime)
                
                # Add backup to list
                backups.append({
                    'filename': filename,
                    'path': filepath,
                    'size': file_info.st_size,
                    'size_mb': round(file_info.st_size / 1024 / 1024, 2),
                    'created_at': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                    'timestamp': timestamp
                })
        
        # Sort backups by timestamp (newest first)
        backups.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return backups
    
    def restore_backup(self, backup_path):
        """
        Restore database from backup
        
        Args:
            backup_path (str): Path to the backup file
            
        Returns:
            tuple: (success, message)
        """
        try:
            # Ensure backup file exists
            if not os.path.exists(backup_path):
                return False, "Backup file does not exist"
            
            # Create temporary directory for extraction
            temp_dir = os.path.join(self.backup_dir, 'temp_restore')
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            os.makedirs(temp_dir)
            
            # Extract the backup zip file
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                zipf.extractall(temp_dir)
            
            # Get the path to the extracted database file
            extracted_db = os.path.join(temp_dir, os.path.basename(self.db_path))
            if not os.path.exists(extracted_db):
                return False, "Could not find database file in backup"
            
            # Create a backup of the current database before restoring
            current_backup_path = os.path.join(self.backup_dir, f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
            shutil.copy2(self.db_path, current_backup_path)
            
            # Close any open connections
            try:
                conn = sqlite3.connect(self.db_path)
                conn.close()
            except:
                pass
            
            # Replace the current database with the backup
            shutil.copy2(extracted_db, self.db_path)
            
            # Clean up temporary directory
            shutil.rmtree(temp_dir)
            
            logger.info(f"Database restored from backup: {backup_path}")
            return True, f"Database restored successfully from backup. (Previous state saved as {os.path.basename(current_backup_path)})"
            
        except Exception as e:
            logger.error(f"Error restoring backup: {e}")
            return False, f"Error restoring backup: {str(e)}"
    
    def cleanup_old_backups(self):
        """
        Delete backups older than retention_days
        
        Returns:
            int: Number of deleted backups
        """
        try:
            backups = self.list_backups()
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            deleted_count = 0
            
            for backup in backups:
                if backup['timestamp'] < cutoff_date:
                    os.remove(backup['path'])
                    logger.info(f"Deleted old backup: {backup['filename']}")
                    deleted_count += 1
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old backups: {e}")
            return 0
    
    def schedule_automatic_backup(self, interval_hours=24):
        """
        Schedule automatic backups at regular intervals
        
        Args:
            interval_hours (int): Backup interval in hours
        """
        while True:
            # Create backup
            success, message, _ = self.create_backup()
            logger.info(f"Automatic backup: {message}")
            
            # Clean up old backups
            deleted = self.cleanup_old_backups()
            logger.info(f"Automatic cleanup: {deleted} old backups removed")
            
            # Wait for next backup
            time.sleep(interval_hours * 60 * 60)

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
