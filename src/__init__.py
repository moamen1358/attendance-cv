"""
Main application package.
Initializes core components on import.
"""

# Apply display patches first thing on import
try:
    from .display_patch import patch_display_functions
    patch_display_functions()
except ImportError:
    pass

# Bootstrap essential database tables
try:
    from .bootstrap_tables import bootstrap_essential_tables
    bootstrap_essential_tables()
except ImportError:
    pass
