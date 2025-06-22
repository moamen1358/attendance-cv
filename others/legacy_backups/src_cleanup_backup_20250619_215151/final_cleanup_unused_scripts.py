#!/usr/bin/env python3
"""
Final Cleanup Script for Unused Files
=====================================
This script identifies and removes the remaining unused or redundant files
in the attendance management system to create a clean, professional codebase.
"""

import os
import shutil
import datetime
from pathlib import Path

def create_backup_directory():
    """Create a timestamped backup directory"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"final_cleanup_backup_{timestamp}"
    os.makedirs(backup_dir, exist_ok=True)
    return backup_dir

def backup_file(file_path, backup_dir):
    """Backup a file before deletion"""
    try:
        # Create subdirectories in backup if needed
        relative_path = os.path.relpath(file_path, ".")
        backup_path = os.path.join(backup_dir, relative_path)
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        
        if os.path.isfile(file_path):
            shutil.copy2(file_path, backup_path)
        elif os.path.isdir(file_path):
            shutil.copytree(file_path, backup_path, dirs_exist_ok=True)
        
        print(f"✅ Backed up: {file_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to backup {file_path}: {e}")
        return False

def remove_file_or_dir(path):
    """Remove a file or directory"""
    try:
        if os.path.isfile(path):
            os.remove(path)
            print(f"🗑️  Removed file: {path}")
        elif os.path.isdir(path):
            shutil.rmtree(path)
            print(f"🗑️  Removed directory: {path}")
        return True
    except Exception as e:
        print(f"❌ Failed to remove {path}: {e}")
        return False

def main():
    """Main cleanup function"""
    print("🧹 Final Cleanup of Unused Scripts and Files")
    print("=" * 50)
    
    # Create backup directory
    backup_dir = create_backup_directory()
    print(f"📦 Created backup directory: {backup_dir}")
    
    # Files/directories to remove - identified as unused or redundant
    files_to_remove = [
        # Legacy/unused scripts in root
        "fix_streamlit_path.py",  # Path fixing script no longer needed
        "professional_academic_system.py",  # Duplicate/alternative system
        "professional_database_restructure.py",  # Migration script
        "professional_restructure_report.json",  # Migration report
        
        # Cleanup scripts (now that cleanup is done)
        "additional_cleanup.py",
        "cleanup_unused_files.py",
        "remove_redundant_files.py",
        "final_utils_cleanup.py",
        "remove_redundant_files.sh",
        
        # Kafka-related scripts (if not using Kafka)
        "run_app_with_kafka.sh",
        "run_with_kafka.sh",
        
        # Test directory
        "testttttttt",
        
        # Utils files that appear unused
        "utils/db_operations_menu.py",  # Replaced by enhanced_db_explorer
        "utils/reset_db.py",  # Basic reset tool
        
        # Potentially unused src files
        "src/analytics_fix.py",  # Appears to be a fix script
        "src/backup_manager.py",  # May be redundant with database_maintenance
        "src/create_admin_user.py",  # One-time setup script
        "src/custom_table_view.py",  # May be unused
        "src/db_pool.py",  # Connection pooling may not be needed
        "src/db_schema_manager.py",  # May be redundant
        "src/startup.py",  # Initialization handled elsewhere
        "src/time_format_utils.py",  # Simple utility that may be unused
        
        # Scripts directory if it exists and is empty/unused
        "scripts",
        
        # Multiple backup databases (keep only the latest)
        "attendance_system_backup_20250619_163848.db",
        "attendance_system_professional_backup_20250619_174030.db",
        "attendance_system_professional_backup_20250619_174225.db",
        "attendance_system_professional_backup_20250619_174510.db",
        # Keep the latest: attendance_system_professional_backup_20250619_174645.db
        
        # Documentation that might be outdated
        "DATABASE_CLEANUP_REPORT.md",
        "ENHANCED_DB_EXPLORER_FEATURES.md",
        "FINAL_VALIDATION_REPORT.md",
        "PROFESSIONAL_RESTRUCTURE_REPORT.md",
        "README_ATTENDANCE_FIX.md",
    ]
    
    removed_count = 0
    failed_count = 0
    
    for file_path in files_to_remove:
        if os.path.exists(file_path):
            print(f"\n📁 Processing: {file_path}")
            
            # Backup first
            if backup_file(file_path, backup_dir):
                # Then remove
                if remove_file_or_dir(file_path):
                    removed_count += 1
                else:
                    failed_count += 1
            else:
                failed_count += 1
        else:
            print(f"⏭️  Already removed or doesn't exist: {file_path}")
    
    # Check for empty directories and remove them
    empty_dirs = []
    for root, dirs, files in os.walk("."):
        if not dirs and not files and root != ".":
            empty_dirs.append(root)
    
    for empty_dir in empty_dirs:
        if empty_dir != backup_dir:  # Don't remove our backup directory
            print(f"🗑️  Removing empty directory: {empty_dir}")
            try:
                os.rmdir(empty_dir)
            except:
                pass
    
    print("\n" + "=" * 50)
    print("📊 CLEANUP SUMMARY")
    print("=" * 50)
    print(f"✅ Files/directories successfully removed: {removed_count}")
    print(f"❌ Failed removals: {failed_count}")
    print(f"📦 Backup directory: {backup_dir}")
    
    print("\n🔍 REMAINING CORE FILES:")
    print("=" * 30)
    
    # List remaining important files
    core_files = [
        "src/app.py",
        "src/login.py", 
        "src/main.py",
        "src/registration_form.py",
        "src/real_time_prediction.py",
        "src/admin_dashboard.py",
        "src/enhanced_db_explorer.py",
        "src/database_explorer.py",
        "src/report.py",
        "src/student_report.py",
        "attendance_system.db",
        "requirements.txt",
        "run.py",
        "run_app.sh",
        "run_streamlit.sh",
        "simple_registration.py",
        "registration_selector.py"
    ]
    
    for file in core_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} (missing)")
    
    print(f"\n📝 To restore any file, check the backup directory: {backup_dir}")
    print("🎉 Final cleanup complete! Your project is now clean and professional.")

if __name__ == "__main__":
    main()
