"""
Main entry point for the application.
Uses proper module imports to avoid relative import errors.
"""
import os
import sys
import streamlit as st

# Add the project root to Python's path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up environment variable to help modules resolve
os.environ['PYTHONPATH'] = os.path.dirname(os.path.abspath(__file__))

# Import the app module directly
if __name__ == "__main__":
    try:
        # Try direct import of main app components (without src prefix)
        from src.app import show_app  # Keep this import as is - we're outside the src directory
        show_app()
    except ModuleNotFoundError as e:
        st.title("Attendance Management System")
        st.error(f"Import error: {e}")
        st.write("There appears to be an issue with the application structure.")
        
        # Attempt to run with streamlit directly
        st.info("Try running the following command from the project root:")
        st.code("cd /home/invisa/Desktop/my_grad_streamlit && streamlit run src/app.py")
