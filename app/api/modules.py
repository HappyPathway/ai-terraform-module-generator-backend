import os
import tempfile
import aiofiles
from fastapi import APIRouter, Depends, HTTPException, UploadFile, Form
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..models.models import Module, ModuleVersion
from ..validation import ModuleValidator
from ..database import get_db
from ..storage import ModuleStorage
from ..dependencies import get_storage, get_current_user
from ..models import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/{namespace}/{name}/{provider}/{version}/upload")
async def upload_module(
    namespace: str,
    name: str,
    provider: str,
    version: str,
    file: UploadFile,
    db: Session = Depends(get_db),
    storage: ModuleStorage = Depends(get_storage),
    current_user: User = Depends(get_current_user)
):
    """Upload a new module version"""
    try:
        # Validate metadata format
        is_valid, errors = ModuleValidator.validate_module_metadata(namespace, name, provider, version)
        if not is_valid:
            raise HTTPException(status_code=400, detail=errors)

        # Save uploaded file temporarily for validation
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        try:
            async with aiofiles.open(temp_file.name, 'wb') as out_file:
                content = await file.read()
                await out_file.write(content)

            logger.debug(f"Module saved temporarily at {temp_file.name}")
            
            # Validate module structure
            is_valid, errors = ModuleValidator.validate_module_structure(temp_file.name)
            if not is_valid:
                logger.error(f"Structure validation failed: {errors}")
                raise HTTPException(status_code=400, detail=errors)
                
            # Store the module
            module_id = f"{namespace}-{name}-{provider}"
            storage_key = storage.store_module(temp_file.name, namespace, name, provider, version)
            
            # Create or update database records
            module = db.query(Module).filter_by(
                namespace=namespace,
                name=name,
                provider=provider
            ).first()
            
            if not module:
                module = Module(
                    id=module_id,
                    namespace=namespace,
                    name=name,
                    provider=provider,
                    owner=current_user.username
                )
                db.add(module)
                db.flush()
                
            module_version = ModuleVersion(
                id=f"{module_id}-{version}",
                module_id=module_id,
                version=version,
                source_zip=storage_key
            )
            db.add(module_version)
            db.commit()
            
            return {"module_id": module_id}
            
        finally:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
                
    except Exception as e:
        logger.error(f"Error uploading module: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/modules/{namespace}/{name}/versions")
async def list_versions(namespace: str, name: str, db: Session = Depends(get_db)):
    query = select(ModuleVersion).join(Module).where(
        Module.namespace == namespace,
        Module.name == name
    )
    versions = db.execute(query).scalars().all()
    return {"versions": [v.version for v in versions]}

@router.get("/modules/search")
async def search_modules(q: str, db: Session = Depends(get_db)):
    query = select(Module).where(
        Module.name.ilike(f"%{q}%")
    )
    modules = db.execute(query).scalars().all()
    return {"modules": [{"name": m.name, "namespace": m.namespace} for m in modules]}
