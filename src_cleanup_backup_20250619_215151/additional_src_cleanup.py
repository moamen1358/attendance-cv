#!/usr/bin/env python3
"""
Additional Source Directory Cleanup
===================================
Review and clean up remaining potentially unused files in the src directory.
"""

import os
import shutil
import datetime
from pathlib import Path

def create_backup_directory():
    """Create a timestamped backup directory"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"src_cleanup_backup_{timestamp}"
    os.makedirs(backup_dir, exist_ok=True)
    return backup_dir

def backup_and_remove(file_path, backup_dir):
    """Backup and remove a file"""
    try:
        # Create backup
        relative_path = os.path.relpath(file_path, ".")
        backup_path = os.path.join(backup_dir, relative_path)
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        
        if os.path.isfile(file_path):
            shutil.copy2(file_path, backup_path)
            os.remove(file_path)
            print(f"✅ Removed: {file_path}")
            return True
    except Exception as e:
        print(f"❌ Failed to process {file_path}: {e}")
        return False

def main():
    """Main cleanup function"""
    print("🧹 Additional Source Directory Cleanup")
    print("=" * 40)
    
    # Create backup directory
    backup_dir = create_backup_directory()
    print(f"📦 Created backup directory: {backup_dir}")
    
    # Files that are likely unused or redundant in src/
    potentially_unused_files = [
        "src/admin_creator.py",  # One-time admin creation script
        "src/admin_validator.py",  # May be unused
        "src/config.py",  # Simple config that may be handled elsewhere
        "src/error_handler.py",  # May be unused
        "src/home.py",  # Very simple home page, might be unused
        "src/login_page.py",  # May be duplicate of login.py
        "src/professional_db_explorer.py",  # May be duplicate of enhanced_db_explorer
        "src/professor_assignments.py",  # Complex feature that may be unused
        "src/professor_subject_assignment.py",  # Complex feature that may be unused
        "src/security.py",  # May be unused
        "src/student_visualization.py",  # May be unused advanced feature
        "src/subject_management.py",  # Complex feature that may be unused
    ]
    
    print("\n🔍 ANALYZING FILES:")
    print("=" * 25)
    
    removed_count = 0
    
    for file_path in potentially_unused_files:
        if os.path.exists(file_path):
            # Check file size and content to help decide
            file_size = os.path.getsize(file_path)
            print(f"\n📁 {file_path} ({file_size} bytes)")
            
            # Read first few lines to understand the file
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    first_lines = f.readlines()[:5]
                    print("   First few lines:")
                    for line in first_lines:
                        print(f"   {line.strip()[:80]}")
            except:
                print("   (Could not read file)")
            
            # Ask user for decision (in a real scenario, this would be manual review)
            # For automation, we'll use heuristics
            should_remove = False
            
            # Remove files that are clearly utility/setup scripts
            if any(keyword in file_path.lower() for keyword in ['creator', 'validator', 'config']):
                should_remove = True
                print("   💡 Detected as utility/setup script")
            
            # Remove files that appear to be duplicates
            if 'login_page' in file_path and os.path.exists('src/login.py'):
                should_remove = True
                print("   💡 Detected as duplicate of login.py")
            
            # Remove simple/minimal files
            if file_size < 500:  # Very small files
                should_remove = True
                print("   💡 Very small file, likely minimal/unused")
            
            if should_remove:
                if backup_and_remove(file_path, backup_dir):
                    removed_count += 1
            else:
                print("   ⏭️ Keeping file")
        else:
            print(f"⏭️  {file_path} doesn't exist")
    
    print("\n" + "=" * 40)
    print("📊 CLEANUP SUMMARY")
    print("=" * 40)
    print(f"✅ Files removed: {removed_count}")
    print(f"📦 Backup directory: {backup_dir}")
    
    print("\n🔍 REMAINING SRC FILES:")
    print("=" * 25)
    
    src_files = [f for f in os.listdir('src') if f.endswith('.py')]
    for file in sorted(src_files):
        print(f"✅ src/{file}")
    
    print(f"\n📝 To restore any file, check: {backup_dir}")
    print("🎉 Source directory cleanup complete!")

if __name__ == "__main__":
    main()
