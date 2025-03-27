# Apply display patches first thing on import
from src.display_patch import patch_display_functions
patch_display_functions()

# Ensure critical tables exist on import
from src.bootstrap_tables import bootstrap_essential_tables
bootstrap_essential_tables()
