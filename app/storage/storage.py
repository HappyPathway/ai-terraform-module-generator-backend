"""Module storage functionality"""
import os
import shutil
import tempfile
import logging
from pathlib import Path
from fastapi import UploadFile

logger = logging.getLogger(__name__)

class ModuleStorage:
    BASE_PATH = "module_storage"

    @classmethod
    async def save_module(cls, namespace: str, name: str, provider: str, version: str, file: UploadFile) -> str:
        """Save an uploaded module file to storage"""
        try:
            # Create directory structure
            module_path = Path(cls.BASE_PATH) / namespace / name / provider / version
            module_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created module directory at {module_path}")
            
            # Create the final file path
            final_path = module_path / "module.zip"
            logger.debug(f"Will save module to {final_path}")
            
            # Write the file directly to the destination
            content = await file.read()
            logger.debug(f"Read {len(content)} bytes from uploaded file")
            
            with open(final_path, "wb") as f:
                f.write(content)
            logger.debug(f"Successfully wrote module to {final_path}")
            
            return str(final_path)
            
        except Exception as e:
            logger.error(f"Error saving module: {str(e)}", exc_info=True)
            raise

    @classmethod
    def get_module_path(cls, namespace: str, name: str, provider: str, version: str = None) -> Path:
        """Get the path to a stored module"""
        base_path = Path(cls.BASE_PATH) / namespace / name / provider
        if version:
            return base_path / version / "module.zip"
        return base_path

    @classmethod
    async def delete_module(cls, namespace: str, name: str, provider: str, version: str) -> bool:
        """Delete a stored module"""
        path = cls.get_module_path(namespace, name, provider, version)
        if path.exists():
            shutil.rmtree(path.parent)  # Remove the version directory
            return True
        return False