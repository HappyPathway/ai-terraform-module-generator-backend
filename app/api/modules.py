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
