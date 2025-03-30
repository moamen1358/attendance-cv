"""
Main application package.
Initializes core components on import.
"""

# Apply display patches first thing on import
from display_patch import patch_display_functions  # Changed from src.display_patch
patch_display_functions()

# Bootstrap essential database tables
from bootstrap_tables import bootstrap_essential_tables  # Changed from src.bootstrap_tables
bootstrap_essential_tables()
