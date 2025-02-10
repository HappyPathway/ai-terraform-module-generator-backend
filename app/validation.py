import zipfile
import json
import os
import tempfile
import subprocess
import shutil
from typing import Tuple, List, Dict, Any, Optional
import hcl2
import re
import semver
import logging

logger = logging.getLogger(__name__)

# All validation logic has been moved to app/validation/module_validator.py
from .validation.module_validator import ModuleValidator, validate_version, validate_module_metadata
