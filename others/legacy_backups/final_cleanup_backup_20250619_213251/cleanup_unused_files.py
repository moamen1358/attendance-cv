#!/usr/bin/env python3
"""
Safe File Cleanup Script
========================
Remove confirmed unused files from the project
"""

import os
import shutil
from datetime import datetime

def backup_before_deletion():
    """Create a backup directory for deleted files"""
    backup_dir = f"deleted_files_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir, exist_ok=True)
    return backup_dir

def safe_remove_files():
    """Remove files that are confirmed to be safe to delete"""
    
    project_root = "/home/invisa/Desktop/my_grad_streamlit"
    
    # Files that are DEFINITELY safe to remove (completed migrations/tests)
    safe_to_remove = [
        # Completed database migration scripts
        'database_analysis.py',
        'database_cleanup.py', 
        'database_final_optimization.py',
        'fix_student_connections.py',
        
        # Test files (no longer needed)
        'test_db_explorer.py',
        'test_enhanced_registration.py',
        'testagent.py',
        
        # Old/redundant files
        'old_registration_form.py',
        'fix_streamlit_path.py',
        
        # Redundant shell scripts
        'run_app_with_kafka.sh',
        'run_with_kafka.sh',
    ]
    
    # Files that might be safe to remove (with caution)
    potentially_safe = [
        'src/analytics_fix.py',
        'src/bootstrap_tables.py',
        'src/database_sync.py',
        'src/display_patch.py',
        'src/error_handling.py',  # keeping error_handler.py
        'src/fix_admin_users.py',
        'src/global_css_handler.py',
        'src/import_legacy.py',
        'src/import_utilities.py',
        'src/initialize_db_tables.py',
        'src/persistent_session_manager.py',
        'src/role_session_persistence.py',
        'src/setup_teacher_subjects.py',
        'src/sync_professor_tables.py',
        'src/table_name_fixer.py',
    ]
    
    return safe_to_remove, potentially_safe

def main():
    print("🧹 Safe File Cleanup")
    print("=" * 50)
    
    project_root = "/home/invisa/Desktop/my_grad_streamlit"
    safe_to_remove, potentially_safe = safe_remove_files()
    
    # Create backup directory
    backup_dir = backup_before_deletion()
    print(f"📦 Created backup directory: {backup_dir}")
    
    removed_count = 0
    
    print(f"\n🗑️ Removing SAFE files:")
    print("-" * 30)
    
    for file_path in safe_to_remove:
        full_path = os.path.join(project_root, file_path)
        backup_path = os.path.join(project_root, backup_dir, file_path)
        
        if os.path.exists(full_path):
            # Create backup directory structure
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            
            # Move to backup first
            shutil.move(full_path, backup_path)
            removed_count += 1
            print(f"✅ Removed: {file_path}")
        else:
            print(f"⚠️  Not found: {file_path}")
    
    print(f"\n📊 Summary:")
    print(f"  • Files removed: {removed_count}")
    print(f"  • Backup location: {backup_dir}")
    
    print(f"\n⚠️  Files NOT removed (review manually):")
    print("-" * 40)
    for file_path in potentially_safe:
        full_path = os.path.join(project_root, file_path)
        if os.path.exists(full_path):
            print(f"❓ {file_path}")
    
    print(f"\n💡 Next Steps:")
    print("1. Test your application to ensure everything works")
    print("2. If issues arise, restore files from backup directory")
    print("3. Review the 'potentially safe' files manually")
    print("4. Remove backup directory after confirming everything works")
    
    print(f"\n🔧 To restore a file:")
    print(f"mv {backup_dir}/[filename] ./")

if __name__ == "__main__":
    main()
