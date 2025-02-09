import zipfile
import json
import os
from typing import Tuple, List, Dict, Any, Optional
import hcl2
import re
import semver

class ModuleValidator:
    @staticmethod
    def validate_module_structure(module_path: str) -> Tuple[bool, Dict[str, Any]]:
        errors = {}
        required_files = ["main.tf", "variables.tf", "outputs.tf"]
        
        if not os.path.exists(module_path):
            errors["path"] = f"Module path {module_path} does not exist"
            return False, errors
            
        for file in required_files:
            if not os.path.exists(os.path.join(module_path, file)):
                errors["files"] = f"Required file {file} is missing"
                
        return len(errors) == 0, errors

    @staticmethod
    def validate_module_metadata(namespace: str, name: str, provider: str, version: str) -> Tuple[bool, Dict[str, Any]]:
        errors = {}
        
        # Validate namespace
        if not namespace or not namespace.isalnum():
            errors["namespace"] = "Namespace must be alphanumeric"
            
        # Validate name
        if not name or not name.replace("-", "").isalnum():
            errors["name"] = "Name must be alphanumeric with optional hyphens"
            
        # Validate provider
        if not provider or not provider.isalnum():
            errors["provider"] = "Provider must be alphanumeric"
            
        # Validate version format (semantic versioning)
        if not version or not all(part.isdigit() for part in version.split(".")):
            errors["version"] = "Version must be in semantic versioning format (e.g., 1.0.0)"
            
        return len(errors) == 0, errors

def validate_version(version: str) -> bool:
    """Validate that a version string follows semantic versioning"""
    try:
        semver.VersionInfo.parse(version)
        return True
    except ValueError:
        return False

def validate_module_metadata(metadata: Dict[str, Any]) -> Optional[str]:
    """
    Validate module metadata meets requirements:
    - Required fields: name, provider, namespace, version
    - Version must be valid semver
    - Name/provider/namespace must be valid identifiers
    
    Returns None if valid, error message if invalid
    """
    required_fields = ["name", "provider", "namespace", "version"]
    for field in required_fields:
        if field not in metadata:
            return f"Missing required field: {field}"
            
    # Validate version follows semver
    if not validate_version(metadata["version"]):
        return "Version must follow semantic versioning (e.g. 1.0.0)"
        
    # Validate identifiers
    identifier_pattern = r"^[a-z0-9]([a-z0-9\-_]*[a-z0-9])?$"
    for field in ["name", "provider", "namespace"]:
        if not re.match(identifier_pattern, metadata[field]):
            return f"{field} must be lowercase alphanumeric and may contain hyphens or underscores"
            
    return None
