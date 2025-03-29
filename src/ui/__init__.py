"""
User interface components and styles.

This package provides UI-related functionality:
- Global CSS and styling
- Reusable UI components
- Layout helpers
"""

from src.ui.styles import apply_global_css
from src.ui.components import (
    create_card, 
    create_metric_card, 
    create_sidebar_navigation
)

__all__ = [
    'apply_global_css',
    'create_card',
    'create_metric_card',
    'create_sidebar_navigation'
]
