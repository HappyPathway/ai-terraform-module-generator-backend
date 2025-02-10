"""Module storage functionality"""
import os
import shutil
import tempfile
from pathlib import Path
from fastapi import UploadFile

class ModuleStorage:
    BASE_PATH = "module_storage"

    @classmethod
    async def save_module(cls, namespace: str, name: str, provider: str, version: str, file: UploadFile) -> str:
        """Save an uploaded module file to storage"""
        # Create directory structure
        module_path = Path(cls.BASE_PATH) / namespace / name / provider / version
        module_path.mkdir(parents=True, exist_ok=True)
        
        # Create temporary file
        suffix = Path(file.filename).suffix if file.filename else '.zip'
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            # Copy uploaded file content to temporary file
            shutil.copyfileobj(file.file, tmp)
            temp_path = tmp.name

        return temp_path

    @classmethod
    async def get_module_path(cls, namespace: str, name: str, provider: str, version: str) -> Path:
        """Get the path to a stored module"""
        return Path(cls.BASE_PATH) / namespace / name / provider / version

    @classmethod
    async def delete_module(cls, namespace: str, name: str, provider: str, version: str) -> bool:
        """Delete a stored module"""
        path = await cls.get_module_path(namespace, name, provider, version)
        if path.exists():
            shutil.rmtree(path)
            return True
        return False