import os
import re
import glob

# Constants
BASE_DIR = '/home/invisa/Desktop/my_grad_streamlit'
PYTHON_FILE_PATTERN = '**/*.py'
EXCLUDE_DIRS = ['__pycache__', 'venv', 'env', '.git', 'myenvDone']

# Table name mappings
TABLE_MAPPINGS = {
    'students': 'student_profiles',
    'users': 'user_accounts', 
    'presidents_embeds': 'facial_recognition_data',
    'attendance_log': 'attendance_records',
    'control_4': 'class_schedules',
    'class_attendance': 'class_attendance_records'
}

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

def update_file_references(file_path):
    """Update table name references in a Python file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes = 0
        
        # Replace table names in SQL statements
        # This handles table names in various SQL contexts (FROM, INSERT INTO, etc.)
        for old_name, new_name in TABLE_MAPPINGS.items():
            # Match table names in SQL statements with various patterns
            patterns = [
                # FROM table
                rf'FROM\s+{old_name}\b',
                # INSERT INTO table
                rf'INSERT\s+INTO\s+{old_name}\b',
                # UPDATE table
                rf'UPDATE\s+{old_name}\b',
                # DELETE FROM table
                rf'DELETE\s+FROM\s+{old_name}\b',
                # CREATE TABLE table
                rf'CREATE\s+TABLE\s+{old_name}\b',
                # ALTER TABLE table
                rf'ALTER\s+TABLE\s+{old_name}\b',
                # DROP TABLE table
                rf'DROP\s+TABLE\s+{old_name}\b',
                # JOIN table
                rf'JOIN\s+{old_name}\b',
                # table AS alias or table alias
                rf'\b{old_name}\s+AS\s+\w+|\b{old_name}\s+\w+\b',
            ]
            
            for pattern in patterns:
                replacement = lambda match: match.group(0).replace(old_name, new_name)
                new_content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
                if new_content != content:
                    changes += 1
                    content = new_content
        
        # Only write back if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, changes
        return False, 0
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False, 0

def main():
    print("=== Updating Table Name References in Code ===")
    print("\nThis script will search for references to the old table names")
    print("in all Python files and update them to use the new names.")
    
    print("\nTable name mappings:")
    for old, new in TABLE_MAPPINGS.items():
        print(f"  • {old} → {new}")
    
    confirm = input("\nDo you want to continue? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Operation cancelled.")
        return
    
    # Find all Python files
    py_files = find_python_files()
    print(f"\nFound {len(py_files)} Python files to process.")
    
    # Process each file
    updated_files = 0
    total_changes = 0
    
    for file_path in py_files:
        print(f"Processing: {os.path.relpath(file_path, BASE_DIR)}")
        updated, changes = update_file_references(file_path)
        if updated:
            updated_files += 1
            total_changes += changes
    
    print(f"\nUpdate complete! Modified {updated_files} files with {total_changes} table name references.")
    
    print("\nIMPORTANT: This script attempts to update SQL references, but it might not catch all cases.")
    print("Please test your application thoroughly after this update.")

if __name__ == "__main__":
    main()
