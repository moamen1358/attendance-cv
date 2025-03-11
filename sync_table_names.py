import os
import re
import glob
import sqlite3

# Constants
BASE_DIR = '/home/invisa/Desktop/my_grad_streamlit'
DATABASE_PATH = 'attendance_system.db'
PYTHON_FILE_PATTERN = '**/*.py'
EXCLUDE_DIRS = ['__pycache__', 'venv', 'env', '.git', 'myenvDone']

# Table name mappings (old_name -> new_name)
TABLE_MAPPINGS = {
    'students': 'student_profiles',
    'users': 'user_accounts',
    'presidents_embeds': 'facial_recognition_data',
    'attendance_log': 'attendance_records',
    'control_4': 'class_schedules',
    'class_attendance': 'class_attendance_records'
}

def get_db_connection():
    """Get connection to the SQLite database"""
    return sqlite3.connect(DATABASE_PATH)

def check_database_tables():
    """Check which tables actually exist in the database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all tables in the database
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    existing_tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    print("Tables found in the database:")
    for table in existing_tables:
        print(f"  • {table}")
    
    # Check which mappings are valid
    print("\nChecking table mappings:")
    for old_name, new_name in TABLE_MAPPINGS.items():
        old_exists = old_name in existing_tables
        new_exists = new_name in existing_tables
        
        if old_exists and new_exists:
            print(f"  • ISSUE: Both {old_name} and {new_name} exist! Manual resolution needed.")
        elif old_exists:
            print(f"  • WARNING: Still using old table name: {old_name} (new name: {new_name})")
        elif new_exists:
            print(f"  • OK: Using new table name: {new_name}")
        else:
            print(f"  • MISSING: Neither {old_name} nor {new_name} exist in database!")
    
    return existing_tables

def find_python_files():
    """Find all Python files in the project"""
    py_files = []
    
    for root, dirs, files in os.walk(BASE_DIR):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        for file in files:
            if file.endswith('.py'):
                py_files.append(os.path.join(root, file))
    
    return py_files

def search_for_table_references(file_path):
    """Search for references to table names in a Python file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    references = {}
    
    # Look for patterns like FROM table_name, INSERT INTO table_name, etc.
    for table_name in list(TABLE_MAPPINGS.keys()) + list(TABLE_MAPPINGS.values()):
        # Different SQL contexts to catch
        patterns = [
            rf'FROM\s+{table_name}\b',
            rf'INSERT\s+INTO\s+{table_name}\b',
            rf'UPDATE\s+{table_name}\b',
            rf'DELETE\s+FROM\s+{table_name}\b',
            rf'JOIN\s+{table_name}\b',
            rf'CREATE\s+TABLE\s+{table_name}\b',
            rf'DROP\s+TABLE\s+{table_name}\b',
            rf'ALTER\s+TABLE\s+{table_name}\b',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                if table_name not in references:
                    references[table_name] = 0
                references[table_name] += len(matches)
    
    return references

def suggest_table_rename_fix(file_path):
    """Analyze a file and suggest fixes for table name references"""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Look for relevant lines that might need updating
    issues = []
    line_number = 0
    
    for line in lines:
        line_number += 1
        
        # Check for old table names that should be updated
        for old_name, new_name in TABLE_MAPPINGS.items():
            # Skip if this is in a string like 'TABLE_MAPPINGS' (avoid false positives)
            if re.search(r'TABLE_MAPPINGS', line):
                continue
            
            # Look for SQL patterns
            patterns = [
                (rf'FROM\s+{old_name}\b', f'FROM {new_name}'),
                (rf'INSERT\s+INTO\s+{old_name}\b', f'INSERT INTO {new_name}'),
                (rf'UPDATE\s+{old_name}\b', f'UPDATE {new_name}'),
                (rf'DELETE\s+FROM\s+{old_name}\b', f'DELETE FROM {new_name}'),
                (rf'JOIN\s+{old_name}\b', f'JOIN {new_name}'),
                (rf'CREATE\s+TABLE\s+{old_name}\b', f'CREATE TABLE {new_name}'),
                (rf'DROP\s+TABLE\s+{old_name}\b', f'DROP TABLE {new_name}'),
                (rf'ALTER\s+TABLE\s+{old_name}\b', f'ALTER TABLE {new_name}'),
            ]
            
            for pattern, replacement in patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append({
                        'line_number': line_number,
                        'line': line.strip(),
                        'table': old_name,
                        'new_table': new_name,
                        'suggested_fix': re.sub(pattern, replacement, line, flags=re.IGNORECASE)
                    })
    
    return issues

def main():
    print("=== Table Reference Sync Tool ===")
    print("This utility helps find and fix table name references after database renaming.\n")
    
    # First check what tables actually exist in the database
    existing_tables = check_database_tables()
    
    # Find Python files
    py_files = find_python_files()
    print(f"\nFound {len(py_files)} Python files to scan.")
    
    # Scan all files for table references
    all_references = {}
    for file_path in py_files:
        references = search_for_table_references(file_path)
        if references:
            all_references[file_path] = references
    
    # Summarize findings
    print("\n=== Table References Found ===")
    for table_name in sorted(TABLE_MAPPINGS.keys()):
        new_name = TABLE_MAPPINGS[table_name]
        old_count = sum(refs.get(table_name, 0) for refs in all_references.values())
        new_count = sum(refs.get(new_name, 0) for refs in all_references.values())
        
        if old_count > 0:
            print(f"• '{table_name}' (old): {old_count} references")
        
        if new_count > 0:
            print(f"• '{new_name}' (new): {new_count} references")
    
    # Now analyze files with old table references
    print("\n=== Files Needing Updates ===")
    files_with_old_refs = []
    
    for file_path, references in all_references.items():
        old_refs = [table for table in references if table in TABLE_MAPPINGS]
        if old_refs:
            rel_path = os.path.relpath(file_path, BASE_DIR)
            files_with_old_refs.append((file_path, old_refs))
            print(f"• {rel_path}: Contains references to {', '.join(old_refs)}")
    
    # Offer to show details for specific files
    if files_with_old_refs:
        print("\nWould you like to see suggested fixes? (yes/no):")
        response = input().lower()
        
        if response == 'yes':
            for file_path, _ in files_with_old_refs:
                issues = suggest_table_rename_fix(file_path)
                if issues:
                    rel_path = os.path.relpath(file_path, BASE_DIR)
                    print(f"\n=== {rel_path} ===")
                    
                    for issue in issues:
                        print(f"Line {issue['line_number']}: {issue['table']} → {issue['new_table']}")
                        print(f"  Current: {issue['line']}")
                        print(f"  Suggest: {issue['suggested_fix']}")
                    
                    # Ask if they want to fix this file
                    print(f"\nFix {rel_path}? (yes/no/quit):")
                    fix_response = input().lower()
                    
                    if fix_response == 'quit':
                        print("Exiting...")
                        break
                    
                    if fix_response == 'yes':
                        # Fix the file
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        for old_name, new_name in TABLE_MAPPINGS.items():
                            # Different SQL contexts to fix
                            patterns = [
                                (rf'FROM\s+{old_name}\b', f'FROM {new_name}'),
                                (rf'INSERT\s+INTO\s+{old_name}\b', f'INSERT INTO {new_name}'),
                                (rf'UPDATE\s+{old_name}\b', f'UPDATE {new_name}'),
                                (rf'DELETE\s+FROM\s+{old_name}\b', f'DELETE FROM {new_name}'),
                                (rf'JOIN\s+{old_name}\b', f'JOIN {new_name}'),
                                (rf'CREATE\s+TABLE\s+{old_name}\b', f'CREATE TABLE {new_name}'),
                                (rf'DROP\s+TABLE\s+{old_name}\b', f'DROP TABLE {new_name}'),
                                (rf'ALTER\s+TABLE\s+{old_name}\b', f'ALTER TABLE {new_name}'),
                            ]
                            
                            for pattern, replacement in patterns:
                                content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
                        
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        
                        print(f"Fixed {rel_path}")
    else:
        print("No files found with old table references!")
    
    print("\nDone scanning. Check output for any needed manual fixes.")

if __name__ == "__main__":
    main()
