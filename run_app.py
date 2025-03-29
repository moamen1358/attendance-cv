"""
Launcher script for the attendance system.
"""
import os
import sys
from pathlib import Path

# Add the project root directory to the Python path
project_root = Path(__file__).parent.absolute()
sys.path.append(str(project_root))

# Now you can import from src
import streamlit.web.cli as stcli

def main():
    # Change directory to project root
    os.chdir(str(project_root))
    
    # Run the app with streamlit
    sys.argv = ["streamlit", "run", "src/app.py", "--browser.gatherUsageStats=False"]
    sys.exit(stcli.main())

if __name__ == "__main__":
    main()
