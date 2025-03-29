"""
Main entry point for the Attendance Management System.

This module initializes the application and starts the Streamlit server.
When you run `python -m src` or execute the module directly, the application starts.
"""
import os
import sys
import logging
import streamlit.web.cli as stcli
from pathlib import Path

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Application entry point"""
    logger.info("Starting Attendance Management System")
    
    # Find the absolute path to this file
    current_dir = Path(__file__).parent.absolute()
    
    # Add project root to Python path if needed
    project_root = current_dir.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # Path to the main application file
    main_file = current_dir / "main.py"
    
    # Start Streamlit
    sys.argv = ["streamlit", "run", str(main_file), "--server.headless=true"]
    logger.info(f"Running Streamlit with: {' '.join(sys.argv)}")
    
    # Use Streamlit's CLI to run the application
    sys.exit(stcli.main())

if __name__ == "__main__":
    main()
