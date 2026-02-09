"""
DEPRECATED: This module is deprecated and redirects to app.config.

All configuration should be imported from app.config instead:
    from app.config import settings, get_settings, Settings

This file is kept for backward compatibility only.
"""
import warnings

# Issue deprecation warning
warnings.warn(
    "app.core.config is deprecated. Use 'from app.config import settings' instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export everything from the main config module for backward compatibility
from app.config import (
    Settings,
    settings,
    get_settings,
    generate_secret_key,
    validate_environment_security
)

__all__ = [
    'Settings',
    'settings',
    'get_settings',
    'generate_secret_key',
    'validate_environment_security'
]
