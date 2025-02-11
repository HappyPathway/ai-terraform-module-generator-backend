"""Registry service for handling module operations"""
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
from ..models.module import Module, ModuleVersion
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

class RegistryService:
    @staticmethod
    async def list_versions(
        db: Session,
        namespace: str,
        name: str,
        provider: str
    ) -> List[Dict[str, Any]]:
        """List available versions for a module"""
        try:
            module = db.query(Module).filter(
                Module.namespace == namespace,
                Module.name == name,
                Module.provider == provider
            ).first()

            if not module:
                return []

            versions = []
            for version in module.versions:
                versions.append({
                    "version": version.version,
                    "protocols": version.protocols or ["5.0"],
                    "platforms": version.platforms or [{"os": "linux", "arch": "amd64"}]
                })

            return versions
        except Exception as e:
            logger.error(f"Error listing versions: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to list versions")

    @staticmethod
    async def get_module(
        db: Session,
        namespace: str,
        name: str,
        provider: str,
        version: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get module metadata"""
        try:
            query = db.query(ModuleVersion).join(Module).filter(
                Module.namespace == namespace,
                Module.name == name,
                Module.provider == provider
            )

            if version:
                query = query.filter(ModuleVersion.version == version)
            else:
                # Get latest version if not specified
                query = query.order_by(ModuleVersion.version.desc())

            module_version = query.first()
            if not module_version:
                return None

            return {
                "id": module_version.module.id,
                "owner": module_version.module.owner or namespace,
                "namespace": namespace,
                "name": name,
                "version": module_version.version,
                "provider": provider,
                "description": module_version.description or module_version.module.description,
                "source": module_version.repository_url or module_version.module.source_url,
                "published_at": module_version.created_at.isoformat(),
                "downloads": module_version.module.downloads,
                "verified": module_version.module.verified
            }
        except Exception as e:
            logger.error(f"Error getting module: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to get module")