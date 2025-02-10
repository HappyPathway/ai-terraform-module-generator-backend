# This file is deprecated.
# All validation logic has been moved to app/validation.py
# This file will be removed in a future update.

from pathlib import Path
import warnings

warnings.warn("This module is deprecated. Use app.validation instead.", DeprecationWarning)

# Import from the new location for backwards compatibility
from ..validation import ModuleValidator, validate_version, validate_module_metadata