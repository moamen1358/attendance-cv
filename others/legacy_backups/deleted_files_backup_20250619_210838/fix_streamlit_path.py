#!/usr/bin/env python
import os
import sys
import subprocess
import shutil

def fix_streamlit_path():
    """
    Fix the path discrepancy in the Streamlit shebang line
    by creating a symlink from the expected to the actual path.
    """
    # Path information
    expected_path = "/home/invisa/miniconda3/envs/test_/bin/python"
    actual_path = "/media/invisa/inVisA/miniconda3/envs/test_/bin/python"
    streamlit_bin = "/media/invisa/inVisA/miniconda3/envs/test_/bin/streamlit"
    
    print(f"Fixing Streamlit Python path:")
    print(f"Expected path: {expected_path}")
    print(f"Actual path: {actual_path}")

    # Check if the actual path exists
    if not os.path.exists(actual_path):
        print(f"Error: Actual Python path does not exist: {actual_path}")
        return False

    # Create the directory structure if it doesn't exist
    expected_dir = os.path.dirname(expected_path)
    if not os.path.exists(expected_dir):
        try:
            os.makedirs(expected_dir, exist_ok=True)
            print(f"Created directory: {expected_dir}")
        except Exception as e:
            print(f"Error creating directory: {e}")
            return False

    # Create a symlink from the expected path to the actual path
    if not os.path.exists(expected_path):
        try:
            # Create a symlink
            os.symlink(actual_path, expected_path)
            print(f"Created symlink: {expected_path} -> {actual_path}")
        except Exception as e:
            print(f"Error creating symlink: {e}")
            
            # Alternative: try to fix the shebang in the streamlit script directly
            if os.path.exists(streamlit_bin):
                print("Attempting to fix the streamlit script directly...")
                try:
                    # Read the streamlit script
                    with open(streamlit_bin, 'r') as f:
                        content = f.read()
                    
                    # Fix the shebang line
                    content = content.replace(expected_path, actual_path)
                    
                    # Write the modified script
                    with open(streamlit_bin, 'w') as f:
                        f.write(content)
                    
                    # Make it executable
                    os.chmod(streamlit_bin, 0o755)
                    print(f"Updated shebang line in {streamlit_bin}")
                    return True
                except Exception as e:
                    print(f"Error updating streamlit script: {e}")
    else:
        print(f"Path already exists: {expected_path}")
        
    # Create a simple wrapper script as a fallback
    wrapper_path = os.path.join(os.path.dirname(streamlit_bin), "streamlit_wrapper")
    try:
        with open(wrapper_path, 'w') as f:
            f.write(f"""#!/bin/bash
{actual_path} {streamlit_bin} "$@"
""")
        os.chmod(wrapper_path, 0o755)
        print(f"Created wrapper script: {wrapper_path}")
    except Exception as e:
        print(f"Error creating wrapper script: {e}")
    
    print("\nTo run Streamlit, use one of these methods:")
    print(f"1. Run: {actual_path} -m streamlit run src/login.py")
    print(f"2. Run: {wrapper_path} run src/login.py")
    
    return True

if __name__ == "__main__":
    success = fix_streamlit_path()
    if success:
        print("\nStreamlit path fixed successfully!")
    else:
        print("\nFailed to fix Streamlit path.")
