#!/usr/bin/env python3
from app.client import TerraformModuleClient
import os
import zipfile
import tempfile
import logging
import time

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def create_module_zip(module_path: str, output_path: str):
    """Create a zip file of the module"""
    abs_module_path = os.path.abspath(module_path)
    logger.debug(f"Creating zip from absolute path: {abs_module_path}")
    
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(abs_module_path):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, abs_module_path)
                logger.debug(f"Adding file to zip: {file_path} as {rel_path}")
                zipf.write(file_path, rel_path)

def upload_module(client, module_info: dict, zip_path: str) -> bool:
    """Upload a module and verify it was uploaded successfully"""
    try:
        logger.debug("Starting module upload...")
        start_time = time.time()
        
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

def main():
    # Initialize client with auth token
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0LXVzZXIiLCJwZXJtaXNzaW9ucyI6WyJyZWFkOm1vZHVsZSIsIndyaXRlOm1vZHVsZSIsInVwbG9hZDptb2R1bGUiLCJnZW5lcmF0ZTptb2R1bGUiXSwiZXhwIjoxNzM5MTgwMjYwfQ.RgN6X1ws2iKDor1YSLRHmVgngLzcmHeSxdD5Pz_r1OQ"
    client = TerraformModuleClient(base_url="http://localhost:8000", token=token)
    
    # Paths to our test modules
    modules = [
        {
            "path": "module_storage/test/aws-vpc",
            "namespace": "testns",
            "name": "tfvpc",
            "provider": "aws",
            "version": "1.0.0"
        },
        {
            "path": "module_storage/test/azure-storage",
            "namespace": "testns",
            "name": "tfstorage",
            "provider": "azure",
            "version": "1.0.0"
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
    main()