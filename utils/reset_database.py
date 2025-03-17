import sqlite3
import os
import streamlit as st
from datetime import datetime
import shutil

# Constants
DATABASE_PATH = 'attendance_system.db'
BACKUP_DIR = 'database_backups'

def create_backup():
    """Create a backup of the current database before resetting"""
    # Ensure backup directory exists
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    
    # Create timestamped backup file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(BACKUP_DIR, f'attendance_system_{timestamp}_pre_reset.db')
    
    try:
        # Make sure the source exists
        if not os.path.exists(DATABASE_PATH):
            return False, "No database file found to back up"
            
        # Create backup using copy
        shutil.copy2(DATABASE_PATH, backup_path)
        return True, backup_path
    except Exception as e:
        return False, str(e)

def find_latest_backup(exclude_reset_backups=True):
    """Find the latest backup file before schema changes"""
    if not os.path.exists(BACKUP_DIR):
        return None
    
    backup_files = []
    for file in os.listdir(BACKUP_DIR):
        if file.startswith('attendance_system_') and file.endswith('.db'):
            # Optionally exclude the reset backups
            if exclude_reset_backups and 'pre_reset' in file:
                continue
            backup_files.append(os.path.join(BACKUP_DIR, file))
    
    if not backup_files:
        return None
    
    # Return the latest backup file
    return max(backup_files, key=os.path.getmtime)

def reset_to_original_schema():
    """Reset database to original schema by removing new tables"""
    # Create backup first
    backup_success, backup_path = create_backup()
    if not backup_success:
        return False, f"Failed to create backup: {backup_path}"
    
    # Find a previous backup to restore from
    latest_backup = find_latest_backup()
    
    # If we have a previous backup, restore from it
    if latest_backup and os.path.exists(latest_backup):
        try:
            # Make a copy of the current database as a temporary backup
            temp_path = DATABASE_PATH + '.temp'
            if os.path.exists(DATABASE_PATH):
                shutil.copy2(DATABASE_PATH, temp_path)
            
            # Copy the backup to the database path
            shutil.copy2(latest_backup, DATABASE_PATH)
            return True, f"Database restored from backup: {latest_backup}"
        except Exception as e:
            # Try to restore from temp if restore failed
            if os.path.exists(temp_path):
                shutil.copy2(temp_path, DATABASE_PATH)
            return False, f"Error restoring from backup: {str(e)}"
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    # If no backup is available, manually drop the new tables
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # List of tables that were added in the optimization
        new_tables = [
            'user_accounts',
            'teacher_subjects',
            'attendance_records',
            'facial_recognition_data'
        ]
        
        # Drop each table if it exists
        tables_dropped = []
        for table in new_tables:
            try:
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
                tables_dropped.append(table)
            except:
                pass
                
        conn.commit()
        conn.close()
        
        return True, f"Removed tables: {', '.join(tables_dropped)}"
    except Exception as e:
        return False, f"Error removing tables: {str(e)}"

def show_reset_interface():
    """Streamlit interface for the database reset function"""
    st.title("Database Reset Tool")
    st.write("This tool will remove the new optimized tables and restore your original database structure.")
    
    st.warning("""
    ⚠️ **CAUTION**:
    - This operation will DELETE the new optimized tables
    - A backup will be created automatically
    - This process cannot be undone
    """)
    
    latest_backup = find_latest_backup()
    if latest_backup:
        st.success(f"Found a previous backup that will be used for restoration: {os.path.basename(latest_backup)}")
    else:
        st.info("No previous backup found. Tables will be manually dropped.")
    
    # Checkbox to confirm understanding
    confirm = st.checkbox("I understand the risks and want to reset my database")
    
    # Execute rebuild button
    if confirm and st.button("Reset Database", type="primary"):
        with st.spinner("Resetting database... This may take several minutes..."):
            success, message = reset_to_original_schema()
        
        if success:
            st.success(message)
            st.balloons()
            st.info("Your database has been reset to its original structure.")
        else:
            st.error(message)

if __name__ == "__main__":
    show_reset_interface()
