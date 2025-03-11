import re
import os

def fix_bytesio_errors():
    """Fix incorrect io.Bytes.IO() references in Python files"""
    
    # Directory to scan
    src_dir = '/home/invisa/Desktop/my_grad_streamlit/src'
    
    # Ensure the src directory exists
    if not os.path.exists(src_dir):
        print(f"Error: Directory not found: {src_dir}")
        return
        
    # Count of fixes made
    fixes = 0
    
    # Walk through all Python files in the directory
    for root, _, files in os.walk(src_dir):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                
                # Read the file content
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check if the file contains the incorrect pattern
                if 'io.Bytes.IO()' in content:
                    # Create a backup first
                    backup_path = f"{file_path}.bak"
                    with open(backup_path, 'w', encoding='utf-8') as backup:
                        backup.write(content)
                    
                    # Replace the incorrect pattern
                    fixed_content = content.replace('io.Bytes.IO()', 'io.BytesIO()')
                    
                    # Write the fixed content back to the file
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(fixed_content)
                    
                    print(f"Fixed io.Bytes.IO() in {file_path}")
                    print(f"Backup saved to {backup_path}")
                    fixes += 1
    
    if fixes > 0:
        print(f"\nFixed {fixes} files with BytesIO errors")
    else:
        print("No files with io.Bytes.IO() errors were found")

if __name__ == "__main__":
    fix_bytesio_errors()
