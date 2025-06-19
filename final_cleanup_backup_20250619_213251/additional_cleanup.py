#!/usr/bin/env python3
"""
Additional Cleanup Script
========================
Remove additional files that are likely unused after review
"""

import os
import shutil
from datetime import datetime

def additional_cleanup():
    """Remove additional files that are likely safe to delete after review"""
    
    project_root = "/home/invisa/Desktop/my_grad_streamlit"
    
    # Additional files that are likely safe to remove
    additional_safe = [
        # Redundant/legacy initialization files
        'src/bootstrap_tables.py',
        'src/initialize_db_tables.py',
        
        # Redundant session management (we have better alternatives)
        'src/persistent_session_manager.py',
        'src/role_session_persistence.py',
        
        # Legacy import utilities (no longer needed)
        'src/import_legacy.py',
        'src/import_utilities.py',
        
        # One-time fix scripts (completed)
        'src/fix_admin_users.py',
        'src/table_name_fixer.py',
        'src/analytics_fix.py',
        
        # Redundant sync scripts (we have professional structure now)
        'src/sync_professor_tables.py',
        'src/setup_teacher_subjects.py',
        'src/database_sync.py',
        
        # UI patches that might not be needed
        'src/display_patch.py',
        'src/global_css_handler.py',
        
        # Redundant error handling (we have error_handler.py)
        'src/error_handling.py',
    ]
    
    return additional_safe

def main():
    print("🧹 Additional File Cleanup")
    print("=" * 50)
    
    project_root = "/home/invisa/Desktop/my_grad_streamlit"
    additional_safe = additional_cleanup()
    
    # Use existing backup directory if it exists, or create new one
    backup_dirs = [d for d in os.listdir(project_root) if d.startswith('deleted_files_backup_')]
    if backup_dirs:
        backup_dir = sorted(backup_dirs)[-1]  # Use most recent
        print(f"📦 Using existing backup directory: {backup_dir}")
    else:
        backup_dir = f"deleted_files_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(backup_dir, exist_ok=True)
        print(f"📦 Created new backup directory: {backup_dir}")
    
    removed_count = 0
    
    print(f"\n🗑️ Removing ADDITIONAL files:")
    print("-" * 30)
    
    for file_path in additional_safe:
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
    
    print(f"\n📊 Additional Cleanup Summary:")
    print(f"  • Additional files removed: {removed_count}")
    print(f"  • Total backup location: {backup_dir}")
    
    # Show remaining src files
    print(f"\n📁 Remaining src/ files:")
    print("-" * 25)
    src_files = []
    src_path = os.path.join(project_root, 'src')
    if os.path.exists(src_path):
        for file in sorted(os.listdir(src_path)):
            if file.endswith('.py') and file != '__init__.py':
                src_files.append(file)
    
    for file in src_files:
        print(f"📄 src/{file}")
    
    print(f"\n✅ Cleanup Complete!")
    print(f"  • Total src/ modules remaining: {len(src_files)}")
    print(f"  • Backup directory: {backup_dir}")
    
    print(f"\n💡 Final Steps:")
    print("1. Test your application thoroughly")
    print("2. If everything works, you can remove the backup directory")
    print("3. The remaining src/ files are the core application modules")

if __name__ == "__main__":
    main()
