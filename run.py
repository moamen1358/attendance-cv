#!/usr/bin/env python3
"""
Entry point script for the Attendance Management System.

This script:
1. Sets up the Python path
2. Initializes essential components
3. Runs the Streamlit application
"""
import os
import sys
import logging
import subprocess
from pathlib import Path
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def setup_environment():
    """Set up the environment for running the application"""
    # Get the application directory
    app_dir = Path(__file__).parent.absolute()
    
    # Add to Python path if not already there
    if str(app_dir) not in sys.path:
        sys.path.append(str(app_dir))
        logger.info(f"Added {app_dir} to Python path")
    
    # Set environment variables
    os.environ["APP_ROOT"] = str(app_dir)
    os.environ["DATABASE_PATH"] = str(app_dir / "attendance_system.db")
    
    # Create directories if they don't exist
    (app_dir / "logs").mkdir(exist_ok=True)
    (app_dir / "backups").mkdir(exist_ok=True)
    
    logger.info("Environment setup complete")

def initialize_database():
    """Initialize the database schema and migrations"""
    try:
        # Import database schema manager
        from src.db_schema_manager import SchemaManager
        
        logger.info("Initializing database schema...")
        schema_manager = SchemaManager()
        schema_manager.init_migration_table()
        schema_manager.apply_migrations()
        schema_manager.ensure_all_tables()
        schema_manager.validate_schema()
        logger.info("Database initialization complete")
        return True
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        logger.error(traceback.format_exc())
        return False

def start_automatic_backup():
    """Start automatic database backup"""
    try:
        from src.backup_manager import start_automatic_backup
        start_automatic_backup(interval_hours=24)
        logger.info("Automatic backup scheduled")
        return True
    except Exception as e:
        logger.error(f"Could not start automatic backup: {e}")
        logger.error(traceback.format_exc())
        return False

def run_streamlit_app():
    """Run the Streamlit application"""
    try:
        # Get the path to the main module
        app_dir = Path(__file__).parent.absolute()
        main_path = app_dir / "src" / "main.py"
        
        # Check if the file exists
        if not main_path.exists():
            logger.error(f"Main application file not found: {main_path}")
            logger.info("Falling back to app.py...")
            main_path = app_dir / "src" / "app.py"
            
            if not main_path.exists():
                logger.error("No application entry point found!")
                return False
        
        # Run Streamlit
        cmd = [sys.executable, "-m", "streamlit", "run", str(main_path), "--server.enableCORS=false"]
        logger.info(f"Starting Streamlit with command: {' '.join(cmd)}")
        
        # Execute the command
        process = subprocess.Popen(cmd)
        process.wait()
        
        return True
    except Exception as e:
        logger.error(f"Error running Streamlit application: {e}")
        logger.error(traceback.format_exc())
        return False

def main():
    """Main entry point function"""
    try:
        # Setup environment
        setup_environment()
        
        # Initialize database
        if not initialize_database():
            logger.warning("Database initialization had errors - continuing anyway")
        
        # Start automatic backup
        start_automatic_backup()
        
        # Run Streamlit app
        success = run_streamlit_app()
        
        return 0 if success else 1
    except Exception as e:
        logger.error(f"Unhandled error in main function: {e}")
        logger.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())
