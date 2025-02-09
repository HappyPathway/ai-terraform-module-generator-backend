import os
import shutil
from fastapi import UploadFile
from typing import Optional

STORAGE_DIR = os.getenv("MODULE_STORAGE_DIR", "./module_storage")

async def store_module_file(file: UploadFile, namespace: str, name: str, provider: str, version: str) -> str:
    """Store a module file in the local filesystem"""
    # Create the directory structure if it doesn't exist
    module_dir = os.path.join(STORAGE_DIR, namespace, name, provider, version)
    os.makedirs(module_dir, exist_ok=True)
    
    file_path = os.path.join(module_dir, file.filename)
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return file_path
    finally:
        file.file.close()

async def get_module_file(namespace: str, name: str, provider: str, version: str) -> Optional[str]:
    """Get the path to a stored module file"""
    module_dir = os.path.join(STORAGE_DIR, namespace, name, provider, version)
    if not os.path.exists(module_dir):
        return None
        
    # Return the first file found in the directory
    files = os.listdir(module_dir)
    return os.path.join(module_dir, files[0]) if files else None
