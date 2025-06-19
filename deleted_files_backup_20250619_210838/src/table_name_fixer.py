#!/usr/bin/env python3
"""
Table Name Fixer - automatically updates Python files to use 
database_utils.py functions instead of direct sqlite3 calls
"""

import os
import sys
import re
import argparse
from database_utils import get_table_names

# Constants
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(PROJECT_ROOT, 'src')

# Get existing table names
existing_tables = get_table_names()

# Define mappings for incorrect table names to correct ones
table_mappings = {
    'class_attendance_records': 'class_attendance',
    'attendance_log': 'attendance_records',
    'students': 'student_profiles',
    'professors': 'user_accounts',
    'user_accounts': 'user_accounts',  # This one is correct, included for completeness
}

def fix_file(file_path, dry_run=True):
    """Fix table references in a Python file"""
    print(f"Processing file: {file_path}")
    
    # Read file content
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Track changes
    changes_made = False
    
    # 1. Add import for database_utils if needed
    if 'import sqlite3' in content and 'from database_utils import' not in content:
        if dry_run:
            print(f"  Would add import for database_utils")
        else:
            # Add import after sqlite3
            content = re.sub(
                r'import sqlite3(\n)',
                'import sqlite3\\1from database_utils import execute_query, execute_query_df\\1',
                content
            )
            changes_made = True
    
    # 2. Fix table references in queries
    for wrong_name, correct_name in table_mappings.items():
        if wrong_name not in existing_tables and correct_name in existing_tables:
            # Count occurrences
            count = content.count(wrong_name)
            if count > 0:
                if dry_run:
                    print(f"  Would replace {count} occurrences of '{wrong_name}' with '{correct_name}'")
                else:
                    content = content.replace(f" {wrong_name} ", f" {correct_name} ")
                    content = content.replace(f" {wrong_name}\n", f" {correct_name}\n")
                    content = content.replace(f" {wrong_name},", f" {correct_name},")
                    content = content.replace(f"({wrong_name})", f"({correct_name})")
                    content = content.replace(f"({wrong_name} ", f"({correct_name} ")
                    
                    # Handle beginning and end of lines
                    content = re.sub(f"^{wrong_name} ", f"{correct_name} ", content, flags=re.MULTILINE)
                    content = re.sub(f" {wrong_name}$", f" {correct_name}", content, flags=re.MULTILINE)
                    
                    changes_made = True
    
    # 3. Replace direct pd.read_sql_query calls with execute_query_df
    pd_read_sql_pattern = r'pd\.read_sql(?:_query)?\s*\(\s*([^,]+),\s*conn(?:,\s*params\s*=\s*([^)]+))?\)'
    pd_matches = re.findall(pd_read_sql_pattern, content)
    
    if pd_matches:
        if dry_run:
            print(f"  Would replace {len(pd_matches)} pd.read_sql_query calls with execute_query_df")
        else:
            for match_data in pd_matches:
                query_var = match_data[0].strip()
                params_var = match_data[1].strip() if len(match_data) > 1 and match_data[1].strip() else None
                
                old_call = f"pd.read_sql_query({query_var}, conn{', params=' + params_var if params_var else ''})"
                new_call = f"execute_query_df({query_var}{', ' + params_var if params_var else ''})"
                
                content = content.replace(old_call, new_call)
                changes_made = True
    
    # 4. Replace direct cursor.execute calls with execute_query
    cursor_execute_pattern = r'cursor\.execute\s*\(\s*([^,]+)(?:,\s*([^)]+))?\)'
    cursor_matches = re.findall(cursor_execute_pattern, content)
    
    if cursor_matches and 'execute_query' in content:  # Only replace if we added the import
        if dry_run:
            print(f"  Would replace suitable cursor.execute calls with execute_query")
        else:
            # This is trickier because we don't want to replace all execute calls
            # For now we'll just do simple cases where cursor.execute is followed by fetchall/fetchone
            for i, line in enumerate(content.split('\n')):
                if 'cursor.execute' in line and ('fetchall' in line or 'fetchone' in line or 'fetchall' in content.split('\n')[i+1] or 'fetchone' in content.split('\n')[i+1]):
                    # Simple case - direct replacement
                    match = re.search(cursor_execute_pattern, line)
                    if match:
                        query_var = match.group(1).strip()
                        params_var = match.group(2).strip() if match.group(2) else None
                        
                        old_pattern = f"cursor.execute({query_var}{', ' + params_var if params_var else ''})"
                        new_pattern = f"execute_query({query_var}{', ' + params_var if params_var else ''})"
                        
                        content = content.replace(old_pattern, new_pattern)
                        changes_made = True
    
    # Save changes
    if changes_made and not dry_run:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"  Updated file: {file_path}")
    elif not changes_made:
        print(f"  No changes needed for {file_path}")
    
    return changes_made

def find_python_files(directory):
    """Find all Python files in a directory recursively"""
    python_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    return python_files

def main():
    parser = argparse.ArgumentParser(description='Fix database table references in Python files')
    parser.add_argument('--dry-run', action='store_true', help='Show changes without modifying files')
    parser.add_argument('--file', help='Process a specific file')
    parser.add_argument('--all', action='store_true', help='Process all Python files in src directory')
    
    args = parser.parse_args()
    
    if args.file:
        fix_file(args.file, dry_run=args.dry_run)
    elif args.all:
        python_files = find_python_files(SRC_DIR)
        print(f"Found {len(python_files)} Python files in {SRC_DIR}")
        
        changed_files = []
        for file_path in python_files:
            if fix_file(file_path, dry_run=args.dry_run):
                changed_files.append(file_path)
        
        if args.dry_run:
            print(f"\nWould change {len(changed_files)} files")
        else:
            print(f"\nChanged {len(changed_files)} files")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
