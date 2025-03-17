import streamlit as st
import os
import sys
import subprocess

def main():
    """
    Simple launcher script for the database reset tool
    """
    print("Database Reset Tool - Remove Optimized Tables")
    print("=============================================")
    print("This tool will remove the new database tables and restore your original database structure.")
    print("A backup will be created automatically.")
    print()
    
    confirm = input("Do you want to proceed with database reset? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("Operation canceled.")
        return
    
    # Execute the reset script
    try:
        print("\nResetting database...")
        
        # Try to import directly first
        try:
            from src.reset_database import reset_to_original_schema
            success, message = reset_to_original_schema()
            
            if success:
                print(f"\n✅ SUCCESS: {message}")
                print("\nYour database has been reset to the original structure.")
            else:
                print(f"\n❌ ERROR: {message}")
        except ImportError:
            # Fall back to using streamlit run
            print("Launching reset interface...")
            subprocess.run(["streamlit", "run", "src/reset_database.py"])
    
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        print("\nAlternative: You can run 'streamlit run src/reset_database.py' to use the graphical interface.")

if __name__ == "__main__":
    main()
