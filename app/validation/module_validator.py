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

class ModuleValidator:
    @staticmethod
    def validate_terraform_module(module_path: str) -> Tuple[bool, Dict[str, str]]:
        """Run terraform init and validate on a module"""
        errors = {}
        try:
            # Check if .terraform-version file exists and use that version
            version_file = os.path.join(module_path, '.terraform-version')
            if os.path.exists(version_file):
                with open(version_file, 'r') as f:
                    version = f.read().strip()
                logger.debug(f"Found .terraform-version file, using version: {version}")
                # Install specified version using tfenv
                subprocess.run(['tfenv', 'install', version], 
                            check=True, 
                            capture_output=True,
                            text=True)
                subprocess.run(['tfenv', 'use', version],
                            check=True,
                            capture_output=True,
                            text=True)
            
            # Run terraform init first
            result = subprocess.run(['terraform', 'init'], 
                                 cwd=module_path, 
                                 check=True, 
                                 capture_output=True,
                                 text=True)
            logger.debug(f"Terraform init output: {result.stdout}")
            
            # Run terraform validate
            result = subprocess.run(['terraform', 'validate'], 
                                 cwd=module_path, 
                                 check=True, 
                                 capture_output=True,
                                 text=True)
            logger.debug(f"Terraform validate output: {result.stdout}")
            return True, {}
            
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr or e.stdout
            errors["terraform_validation"] = f"Terraform validation failed: {error_msg}"
            return False, errors

    @staticmethod
    def validate_module_structure(zip_path: str) -> Tuple[bool, Dict[str, Any]]:
        errors = {}
        
        if not os.path.exists(zip_path):
            errors["path"] = f"Module path {zip_path} does not exist"
            return False, errors

        try:
            with tempfile.TemporaryDirectory(prefix="terraform_module_") as tmpdir:
                logger.debug(f"Created temporary directory for validation: {tmpdir}")

                # Extract the zip file
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(tmpdir)
                    logger.debug(f"Extracted module to temporary directory: {tmpdir}")
                    file_list = zip_ref.namelist()
                    logger.debug(f"Files in zip: {file_list}")
                    
                # Check for at least one .tf file
                tf_files = [f for f in os.listdir(tmpdir) if f.endswith('.tf')]
                if not tf_files:
                    errors["terraform_files"] = "Module must contain at least one .tf file"
                    return False, errors

                # Run terraform validation
                is_valid, tf_errors = ModuleValidator.validate_terraform_module(tmpdir)
                if not is_valid:
                    errors.update(tf_errors)
                    return False, errors

                logger.debug(f"Validation complete, temporary directory will be cleaned up: {tmpdir}")

        except zipfile.BadZipFile:
            errors["zip"] = "Invalid zip file format"
            return False, errors
        except Exception as e:
            errors["validation"] = f"Error validating module: {str(e)}"
            return False, errors
                
        return True, {}

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
        if not version or not validate_version(version):
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
