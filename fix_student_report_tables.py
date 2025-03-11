import os
import re

def update_table_references():
    """Update all table references in the student_report.py file"""
    
    filepath = '/home/invisa/Desktop/my_grad_streamlit/src/student_report.py'
    
    if not os.path.exists(filepath):
        print(f"Error: Could not find {filepath}")
        return False
        
    # Create a backup before making changes
    backup_path = f"{filepath}.bak"
    with open(filepath, 'r', encoding='utf-8') as file:
        original_content = file.read()
        
    with open(backup_path, 'w', encoding='utf-8') as backup:
        backup.write(original_content)
    
    print(f"Created backup at {backup_path}")
    
    # Define table name mappings (old -> new)
    table_mappings = {
        'class_attendance': 'class_attendance_records',
        'attendance_log': 'attendance_records',
        'control_4': 'class_schedules',
        'students': 'student_profiles',
        'users': 'user_accounts',
        'presidents_embeds': 'facial_recognition_data'
    }
    
    # Replace all table references
    updated_content = original_content
    changes_made = 0
    
    for old_name, new_name in table_mappings.items():
        # Different SQL query patterns
        patterns = [
            rf'FROM\s+{old_name}\b',
            rf'INTO\s+{old_name}\b',
            rf'UPDATE\s+{old_name}\b',
            rf'JOIN\s+{old_name}\b',
            rf'TABLE\s+{old_name}\b',
            rf'(\'|\"|\`)({old_name})(\'|\"|\`)'  # Quoted table names
        ]
        
        for pattern in patterns:
            # Count occurrences before replacement
            before_count = len(re.findall(pattern, updated_content, re.IGNORECASE))
            
            # Replace pattern
            if pattern.endswith('\b'):
                # For word boundaries, need to replace the word
                updated_content = re.sub(pattern, lambda m: m.group(0).replace(old_name, new_name), updated_content, flags=re.IGNORECASE)
            else:
                # For quoted names, replace carefully
                updated_content = re.sub(rf'(\'|\"|\`)({old_name})(\'|\"|\`)', rf'\1{new_name}\3', updated_content, flags=re.IGNORECASE)
            
            # Count occurrences after replacement
            after_count = len(re.findall(pattern.replace(old_name, new_name), updated_content, re.IGNORECASE))
            
            # Track changes
            changes_made += before_count - after_count + after_count
            
    # Write the updated content
    if changes_made > 0:
        with open(filepath, 'w', encoding='utf-8') as file:
            file.write(updated_content)
        print(f"Updated {changes_made} table references in {filepath}")
        return True
    else:
        print("No changes needed in the file")
        return False

if __name__ == "__main__":
    print("Fixing table references in student_report.py...")
    if update_table_references():
        print("Done! Please restart your application.")
    else:
        print("No changes were made.")
