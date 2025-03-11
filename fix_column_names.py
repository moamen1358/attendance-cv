import re
import os

def fix_column_names():
    """Directly fix the column names issue in report.py"""
    filepath = '/home/invisa/Desktop/my_grad_streamlit/src/report.py'
    
    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        return
    
    # Read the file
    with open(filepath, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Create a backup
    with open(f"{filepath}.bak", 'w', encoding='utf-8') as backup:
        backup.write(content)
    
    # Look for the problematic line (the one with 6 column names)
    problem_pattern = r"all_students_df\.columns\s*=\s*\[\s*'Student'\s*,\s*'Classes Attended'\s*,\s*'Total Classes'\s*,\s*'Attendance Rate \(%\)'\s*,\s*'First Date'\s*,\s*'Last Date'\s*\]"
    
    # The corrected version with 8 column names
    fix = """all_students_df.columns = [
                'Student', 
                'ID', 
                'Section', 
                'Classes Attended', 
                'Total Classes', 
                'Attendance Rate (%)', 
                'First Date', 
                'Last Date'
            ]"""
    
    # Check if the problematic line exists
    if re.search(problem_pattern, content):
        # Replace the problematic line
        new_content = re.sub(problem_pattern, fix, content)
        
        # Write the fixed content
        with open(filepath, 'w', encoding='utf-8') as file:
            file.write(new_content)
        
        print(f"Fixed the column names issue in {filepath}")
        print("Original file backed up to {filepath}.bak")
    else:
        print("The problematic line was not found. The file might already be fixed or has a different issue.")

if __name__ == "__main__":
    fix_column_names()
