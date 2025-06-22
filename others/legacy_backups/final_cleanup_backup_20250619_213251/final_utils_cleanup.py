#!/usr/bin/env python3
"""
Utils Directory Cleanup
=======================
Clean up old utility scripts that are no longer needed
"""

import os
import shutil
from datetime import datetime

def main():
    print("🧹 Utils Directory Cleanup")
    print("=" * 50)
    
    project_root = "/home/invisa/Desktop/my_grad_streamlit"
    
    # Most of these utils scripts are old one-time setup/fix scripts
    utils_to_remove = [
        'utils/create_class_attendance.py',
        'utils/create_login_logs_table.py', 
        'utils/create_user_tables.py',
        'utils/database_init.py',
        'utils/db_operations_menu.py',
        'utils/db_rebuild.py',
        'utils/enhance_database.py',
        'utils/fix_admin_users_cli.py',
        'utils/fix_db_tables.py',
        'utils/fix_student_profiles.py',
        'utils/fix_tables_cli.py',
        'utils/fix_teacher_subjects.py',
        'utils/insert_moamen_data.py',
        'utils/rebuild_db.py',
        'utils/reset_database.py',
        'utils/reset_db.py',
        'utils/role_session_persistence.py',
        'utils/setup_admin_tables.py',
        'utils/setup_student_tables.py',
    ]
    
    # Keep these utils files (might still be useful)
    utils_to_keep = [
        'utils/__init__.py',
        'utils/admin_session_persistence.py',
        'utils/class_schedule_editor.py',
    ]
    
    # Use existing backup directory
    backup_dirs = [d for d in os.listdir(project_root) if d.startswith('deleted_files_backup_')]
    if backup_dirs:
        backup_dir = sorted(backup_dirs)[-1]
        print(f"📦 Using backup directory: {backup_dir}")
    else:
        backup_dir = f"deleted_files_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(backup_dir, exist_ok=True)
        print(f"📦 Created backup directory: {backup_dir}")
    
    removed_count = 0
    
    print(f"\n🗑️ Removing utils files:")
    print("-" * 30)
    
    for file_path in utils_to_remove:
        full_path = os.path.join(project_root, file_path)
        backup_path = os.path.join(project_root, backup_dir, file_path)
        
        if os.path.exists(full_path):
            # Create backup directory structure
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            
            # Move to backup
            shutil.move(full_path, backup_path)
            removed_count += 1
            print(f"✅ Removed: {file_path}")
        else:
            print(f"⚠️  Not found: {file_path}")
    
    print(f"\n📁 Keeping these utils files:")
    print("-" * 30)
    for file_path in utils_to_keep:
        full_path = os.path.join(project_root, file_path)
        if os.path.exists(full_path):
            print(f"✅ Kept: {file_path}")
    
    print(f"\n📊 Utils Cleanup Summary:")
    print(f"  • Utils files removed: {removed_count}")
    print(f"  • Utils files kept: {len(utils_to_keep)}")
    print(f"  • Backup location: {backup_dir}")
    
    # Final summary
    print(f"\n🎉 COMPLETE CLEANUP SUMMARY")
    print("=" * 40)
    
    # Count total files in backup
    backup_path = os.path.join(project_root, backup_dir)
    total_backed_up = 0
    if os.path.exists(backup_path):
        for root, dirs, files in os.walk(backup_path):
            total_backed_up += len(files)
    
    print(f"📊 Total files removed: {total_backed_up}")
    print(f"📁 Backup directory: {backup_dir}")
    print(f"")
    print(f"✅ Your project is now cleaned up!")
    print(f"💡 Test your application and remove backup if everything works")

if __name__ == "__main__":
    main()
