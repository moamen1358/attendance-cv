#!/usr/bin/env python3
"""
Unused Files Cleanup Script
===========================
Analyze and identify unused scripts in the project
"""

import os
import re
import glob
from pathlib import Path

def analyze_file_usage():
    """Analyze which files are used and which are potentially unused"""
    
    project_root = "/home/invisa/Desktop/my_grad_streamlit"
    
    # Get all Python files
    python_files = []
    for root, dirs, files in os.walk(project_root):
        # Skip certain directories
        skip_dirs = {'.git', '__pycache__', '.vscode', 'insightface_model', 
                    'database_backups', 'backups', 'store', 'vid', 'testttttttt'}
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    # Categorize files
    main_scripts = []
    src_modules = []
    test_scripts = []
    utility_scripts = []
    database_scripts = []
    
    for file_path in python_files:
        file_name = os.path.basename(file_path)
        rel_path = os.path.relpath(file_path, project_root)
        
        if file_path.startswith(os.path.join(project_root, 'src')):
            src_modules.append(rel_path)
        elif 'test' in file_name.lower():
            test_scripts.append(rel_path)
        elif any(keyword in file_name.lower() for keyword in ['database', 'db_', 'fix_', 'cleanup']):
            database_scripts.append(rel_path)
        elif file_name in ['run.py', 'main.py', 'app.py']:
            main_scripts.append(rel_path)
        else:
            utility_scripts.append(rel_path)
    
    return {
        'main_scripts': main_scripts,
        'src_modules': src_modules,
        'test_scripts': test_scripts,
        'utility_scripts': utility_scripts,
        'database_scripts': database_scripts
    }

def find_unused_files():
    """Find potentially unused files"""
    
    project_root = "/home/invisa/Desktop/my_grad_streamlit"
    
    # Files that are likely unused based on your recent work
    potentially_unused = [
        # Old/redundant scripts
        'old_registration_form.py',
        'testagent.py',
        'fix_streamlit_path.py',
        
        # Database migration scripts (completed)
        'database_analysis.py',
        'database_cleanup.py', 
        'database_final_optimization.py',
        'fix_student_connections.py',
        
        # Test/development files
        'test_db_explorer.py',
        'test_enhanced_registration.py',
        
        # Redundant run scripts
        'run_app_with_kafka.sh',
        'run_with_kafka.sh',
        
        # Potentially redundant src files
        'src/analytics_fix.py',
        'src/fix_admin_users.py',
        'src/table_name_fixer.py',
        'src/import_legacy.py',
        'src/sync_professor_tables.py',
        'src/setup_teacher_subjects.py',
        'src/error_handling.py',  # if error_handler.py exists
        'src/database_sync.py',
        'src/import_utilities.py',
        'src/bootstrap_tables.py',
        'src/initialize_db_tables.py',
        'src/display_patch.py',
        'src/global_css_handler.py',
        'src/persistent_session_manager.py',
        'src/role_session_persistence.py',
    ]
    
    # Check which files actually exist
    existing_unused = []
    for file_path in potentially_unused:
        full_path = os.path.join(project_root, file_path)
        if os.path.exists(full_path):
            existing_unused.append(file_path)
    
    return existing_unused

def identify_core_files():
    """Identify core files that should NOT be removed"""
    core_files = [
        # Main application files
        'run.py',
        'src/app.py',
        'src/main.py',
        'src/home.py',
        'src/login.py',
        
        # Essential modules
        'src/registration_form.py',
        'src/database_utils.py',
        'src/config.py',
        'src/real_time_prediction.py',
        'src/report.py',
        
        # Professional system
        'professional_academic_system.py',
        'professional_database_restructure.py',
        'src/professional_db_explorer.py',
        'src/enhanced_db_explorer.py',
        
        # Admin functionality
        'src/admin_dashboard.py',
        'src/admin_creator.py',
        'src/create_admin_user.py',
        
        # Configuration and utilities
        'requirements.txt',
        'docker-compose.yml',
        'Dockerfile',
    ]
    
    return core_files

def main():
    print("🔍 Analyzing Project Files")
    print("=" * 50)
    
    # Analyze file usage
    file_categories = analyze_file_usage()
    
    print("📊 File Categories:")
    for category, files in file_categories.items():
        print(f"\n{category.upper().replace('_', ' ')} ({len(files)} files):")
        for file in sorted(files):
            print(f"  • {file}")
    
    print("\n" + "=" * 50)
    print("🗑️  POTENTIALLY UNUSED FILES")
    print("=" * 50)
    
    unused_files = find_unused_files()
    
    if unused_files:
        print("These files appear to be unused and can likely be removed:")
        print()
        for file_path in sorted(unused_files):
            print(f"❌ {file_path}")
    else:
        print("No obviously unused files found.")
    
    print("\n" + "=" * 50)
    print("✅ CORE FILES (DO NOT REMOVE)")
    print("=" * 50)
    
    core_files = identify_core_files()
    print("These files are essential for the application:")
    print()
    for file_path in sorted(core_files):
        print(f"✅ {file_path}")
    
    print("\n" + "=" * 50)
    print("💡 RECOMMENDATIONS")
    print("=" * 50)
    
    print("""
    SAFE TO REMOVE (completed migration/test files):
    • database_analysis.py
    • database_cleanup.py  
    • database_final_optimization.py
    • fix_student_connections.py
    • test_db_explorer.py
    • test_enhanced_registration.py
    
    CONSIDER REMOVING (redundant/old files):
    • old_registration_form.py
    • testagent.py
    • fix_streamlit_path.py
    • run_app_with_kafka.sh
    • run_with_kafka.sh
    
    REVIEW CAREFULLY (may have dependencies):
    • src/analytics_fix.py
    • src/import_legacy.py
    • src/sync_professor_tables.py
    """)

if __name__ == "__main__":
    main()
