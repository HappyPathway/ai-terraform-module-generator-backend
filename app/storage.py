"""Module storage functionality"""
from pathlib import Path
from fastapi import UploadFile
import shutil

async def store_module_file(file: UploadFile, destination: Path) -> None:
    """Store an uploaded module file at the specified destination"""
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("wb") as f:
        shutil.copyfileobj(file.file, f)

class ModuleStorage:
    STORAGE_DIR = "module_storage"

    @classmethod
    async def save_module(cls, namespace: str, name: str, provider: str, version: str, file: UploadFile) -> str:
        """Save an uploaded module file"""
        storage_path = cls._get_storage_path(namespace, name, provider, version)
        await store_module_file(file, storage_path)
        return str(storage_path)

    @classmethod
    def get_module_path(cls, namespace: str, name: str, provider: str, version: str) -> Path:
        """Get the path to a stored module"""
        return cls._get_storage_path(namespace, name, provider, version)

    @classmethod
    def _get_storage_path(cls, namespace: str, name: str, provider: str, version: str) -> Path:
        """Generate the storage path for a module"""
        base_path = Path(cls.STORAGE_DIR)
        return base_path / namespace / name / provider / version / "module.zip"

__all__ = ['ModuleStorage', 'store_module_file']
