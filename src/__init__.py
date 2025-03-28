"""
Main application package.
Initializes core components on import.
"""

# Apply display patches first thing on import
from src.display_patch import patch_display_functions
patch_display_functions()

# Bootstrap essential database tables
from src.bootstrap_tables import bootstrap_essential_tables
bootstrap_essential_tables()
