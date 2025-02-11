#!/usr/bin/env python3
from app.client import TerraformModuleClient
import os
import zipfile
import tempfile
import logging
import time
import urllib3
import semver

# Disable SSL verification warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def create_module_zip(module_path: str, output_path: str):
    """Create a zip file of the module"""
    abs_module_path = os.path.abspath(module_path)
    logger.debug(f"Creating zip from absolute path: {abs_module_path}")
    
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Only include .tf files at the root of the module
        for filename in os.listdir(abs_module_path):
            if filename.endswith('.tf'):
                file_path = os.path.join(abs_module_path, filename)
                logger.debug(f"Adding file to zip: {file_path} as {filename}")
                # Add file at the root level in zip
                zipf.write(file_path, filename)
                
        # Log the contents of the zip after creation
        logger.debug("\nZip contents:")
        for info in zipf.filelist:
            logger.debug(f"  - {info.filename} ({info.file_size} bytes)")

def get_next_version(client: TerraformModuleClient, module_info: dict) -> str:
    """Get the next version number for a module"""
    try:
        versions = client.list_versions(
            module_info['namespace'],
            module_info['name'],
            module_info['provider']
        )
        
        # Always start with version 1.0.0 if no versions exist
        if not versions or 'modules' not in versions or not versions['modules']:
            logger.info("No existing versions found, starting with 1.0.0")
            return "1.0.0"
            
        existing_versions = versions.get('modules', [{}])[0].get('versions', [])
        if not existing_versions:
            logger.info("No existing versions array found, starting with 1.0.0")
            return "1.0.0"
            
        version_numbers = [v.get('version') for v in existing_versions if v.get('version')]
        if not version_numbers:
            logger.info("No valid version numbers found, starting with 1.0.0")
            return "1.0.0"
            
        # Get highest version
        highest_version = max(version_numbers, key=lambda v: semver.VersionInfo.parse(v))
        logger.debug(f"Current highest version: {highest_version}")
        
        # Increment patch version
        next_version = str(semver.VersionInfo.parse(highest_version).bump_patch())
        logger.debug(f"Next version will be: {next_version}")
        return next_version
        
    except Exception as e:
        logger.warning(f"Error getting versions, using 1.0.0: {str(e)}")
        return "1.0.0"

def upload_module(client, module_info: dict, zip_path: str) -> bool:
    """Upload a module and verify it was uploaded successfully"""
    try:
        logger.debug("Starting module upload...")
        start_time = time.time()
        
        # Get next version
        version = get_next_version(client, module_info)
        logger.info(f"Using version: {version}")
        module_info['version'] = version
        
        logger.debug(f"Preparing to upload module with info: {module_info}")
        logger.debug(f"ZIP file path: {zip_path}")
        
        # Log file size
        file_size = os.path.getsize(zip_path)
        logger.debug(f"ZIP file size: {file_size} bytes")
        
        logger.debug("Initiating upload request...")
        result = client.upload_module(
            namespace=module_info['namespace'],
            name=module_info['name'],
            provider=module_info['provider'],
            version=module_info['version'],
            file_path=zip_path
        )
        
        upload_time = time.time() - start_time
        logger.debug(f"Upload request completed in {upload_time:.2f} seconds")
        logger.info(f"Upload response: {result}")

        logger.debug("Starting verification process...")
        # Verify module is searchable
        logger.debug(f"Searching for module: {module_info['name']}")
        search_result = client.search_modules(module_info['name'])
        logger.info(f"Search result after upload: {search_result}")

        # List versions
        logger.debug(f"Listing versions for {module_info['namespace']}/{module_info['name']}/{module_info['provider']}")
        versions = client.list_versions(
            module_info['namespace'], 
            module_info['name'], 
            module_info['provider']
        )
        logger.info(f"Available versions: {versions}")
        
        logger.debug("Module upload and verification completed successfully")
        return True

    except Exception as e:
        logger.error(f"Upload failed: {str(e)}", exc_info=True)
        return False

def main(version: str):
    # Initialize client with auth token - load from environment variable
    token = os.getenv("TERRAFORM_MODULE_TOKEN")
    if not token:
        raise ValueError("TERRAFORM_MODULE_TOKEN environment variable must be set")
        
    client = TerraformModuleClient(base_url="https://registry.local", token=token, verify_ssl=False)
    
    # Paths to our test modules
    modules = [
        {
            "path": "module_storage/test/aws-vpc",
            "namespace": "HappyPathway",
            "name": "tfvpc",
            "provider": "aws",
            "version": version  # This will be used as default for new modules
        },
        {
            "path": "module_storage/test/azure-storage",
            "namespace": "HappyPathway",
            "name": "tfstorage",
            "provider": "azure",
            "version": version  # This will be used as default for new modules
        }
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        for module in modules:
            logger.info(f"\nProcessing {module['name']} module...")
            
            zip_path = os.path.join(tmpdir, f"{module['name']}.zip")
            # Create zip file
            create_module_zip(module['path'], zip_path)
            logger.info(f"Created zip file at {zip_path}")
            
            # Log zip contents for debugging
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                logger.debug("Zip contents:")
                for filename in zipf.namelist():
                    logger.debug(f"  - {filename}")
            
            # Upload the module - validation happens server-side
            if not upload_module(client, module, zip_path):
                logger.error(f"Failed to process module {module['name']}")

if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("--version", type=str, default="1.0.0")
    args = parser.parse_args()
    main(args.version)