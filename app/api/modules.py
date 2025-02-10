import os
import tempfile
import aiofiles
from fastapi import APIRouter, Depends, HTTPException, UploadFile, Form
from typing import List, Optional
from sqlalchemy.orm import Session
from ..models import Module, ModuleVersion
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
    
    # Validate metadata format
    is_valid, errors = ModuleValidator.validate_module_metadata(namespace, name, provider, version)
    if not is_valid:
        raise HTTPException(status_code=400, detail=errors)

    # Save uploaded file temporarily for validation
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
    try:
        # Write uploaded file to temp file
        async with aiofiles.open(temp_file.name, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)

        logger.debug(f"Module saved temporarily at {temp_file.name}")
        
        # Validate module structure
        logger.debug(f"Validating module structure at {temp_file.name}")
        is_valid, errors = ModuleValidator.validate_module_structure(temp_file.name)
        if not is_valid:
            logger.error(f"Structure validation failed: {errors}")
            raise HTTPException(status_code=400, detail=errors)
            
        # Store the module
        module_id = storage.store_module(temp_file.name, namespace, name, provider, version)
        
        # Create or update database records
        module = db.query(Module).filter_by(
            namespace=namespace,
            name=name,
            provider=provider
        ).first()
        
        if not module:
            module = Module(namespace=namespace, name=name, provider=provider)
            db.add(module)
            db.flush()
            
        module_version = ModuleVersion(
            module_id=module.id,
            version=version,
            storage_key=module_id
        )
        db.add(module_version)
        db.commit()
        
        return {"module_id": module_id}
        
    finally:
        # Clean up temp file
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)

from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import Depends
from ..database import get_db
from ..models import DBModule, DBModuleVersion
from ..validation.module_validator import ModuleValidator

@router.get("/modules/{namespace}/{name}/versions")
async def list_versions(namespace: str, name: str, db: Session = Depends(get_db)):
    query = select(DBModuleVersion).join(DBModule).where(
        DBModule.namespace == namespace,
        DBModule.name == name
    )
    versions = db.execute(query).scalars().all()
    return {"versions": [v.version for v in versions]}

@router.get("/modules/search")
async def search_modules(q: str, db: Session = Depends(get_db)):
    query = select(DBModule).where(
        DBModule.name.ilike(f"%{q}%")
    )
    modules = db.execute(query).scalars().all()
    return {"modules": [{"name": m.name, "namespace": m.namespace} for m in modules]}
