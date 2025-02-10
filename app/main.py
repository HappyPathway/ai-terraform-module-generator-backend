from fastapi import FastAPI, File, HTTPException, Depends, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .database import get_db, engine
from .models.base import Base
from .models.module import Module, ModuleVersion  # Update import path to use module.py
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime
from pathlib import Path
from .auth import check_permissions, Permission, verify_token
from .cache import CacheService, get_cache_service, get_redis_client
from .rate_limiter import RateLimiter, get_rate_limiter
from .stats import StatsTracker, get_stats_tracker
from .validation import ModuleValidator
from .storage import ModuleStorage
from .docs import DocGenerator
from .github import GitHubService
from .search import SearchService
from .dependencies import DependencyManager
import logging
import os

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Terraform Module Generator",
    description="Generate Terraform modules using AI with Terraform Registry Protocol support",
    version="0.1.0"
)

# Create database tables
Base.metadata.create_all(bind=engine)

class ModuleVersionSchema(BaseModel):
    version: str
    protocols: List[str]
    platforms: List[dict]

class ModuleVersions(BaseModel):
    modules: List[ModuleVersionSchema]

@app.get("/.well-known/terraform.json")
async def terraform_discovery():
    return JSONResponse({
        "modules.v1": "/v1/modules/",
        "providers.v1": "/v1/providers/"
    })

# Initialize services with dependency injection support
def get_cache_service():
    redis_client = get_redis_client(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", 6379))
    )
    return CacheService(redis_client=redis_client)

def get_rate_limiter():
    return RateLimiter()

def get_stats_tracker():
    return StatsTracker()

app.dependency_overrides[get_cache_service] = get_cache_service
app.dependency_overrides[get_rate_limiter] = get_rate_limiter
app.dependency_overrides[get_stats_tracker] = get_stats_tracker

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    rate_limiter = get_rate_limiter()
    if not await rate_limiter.check_rate_limit(str(request.client.host)):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    return await call_next(request)

@app.get("/v1/modules/search")
async def search_modules(
    query: str = "",
    provider: str = None,
    namespace: str = None,
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db),
    cache_service: CacheService = Depends(get_cache_service)
):
    cache_key = f"search:{query}:{provider}:{namespace}:{limit}:{offset}"
    cached_result = await cache_service.get(cache_key)
    if cached_result:
        return cached_result
        
    results = await SearchService.search_modules(
        db, query, provider, namespace, limit, offset
    )
    # Convert SQLAlchemy models to Pydantic response models
    modules = []
    for module in results:
        # Get the latest version for each module
        latest_version = max(module.versions, key=lambda v: v.version) if module.versions else None
        if latest_version:
            modules.append({
                "id": module.id,
                "owner": module.owner or module.namespace,
                "namespace": module.namespace,
                "name": module.name,
                "version": latest_version.version,
                "provider": module.provider,
                "description": module.description or "",
                "source": latest_version.repository_url or module.source_url or "",
                "published_at": module.published_at.isoformat(),
                "downloads": module.downloads,
                "verified": module.verified
            })
    
    response = {"modules": modules}
    await cache_service.set(cache_key, response)
    return response

@app.get("/v1/modules/{namespace}/{name}/{provider}/versions")
async def list_versions(
    namespace: str,
    name: str,
    provider: str,
    db: Session = Depends(get_db)
):
    """List available versions for a module"""
    try:
        logger.debug(f"Querying versions for {namespace}/{name}/{provider}")
        versions = db.query(ModuleVersion).join(Module).filter(
            Module.namespace == namespace,
            Module.name == name,
            Module.provider == provider
        ).all()
        
        if not versions:
            logger.debug("No versions found")
            return {"modules": []}
        
        result = {"modules": [{"version": v.version} for v in versions]}
        logger.debug(f"Returning versions: {result}")
        return result
    except Exception as e:
        logger.error(f"Error listing versions: {str(e)}")
        raise

@app.get("/v1/modules/{namespace}/{name}/{provider}/{version}/download")
async def download_module(
    namespace: str, 
    name: str, 
    provider: str, 
    version: str, 
    db: Session = Depends(get_db),
    stats_tracker: StatsTracker = Depends(get_stats_tracker),
    token: dict = Depends(verify_token)
):
    module = db.query(Module).filter(
        Module.namespace == namespace,
        Module.name == name,
        Module.provider == provider,
        Module.version == version
    ).first()
    
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    
    await stats_tracker.track_download(str(module.id))
    return {"download_url": module.download_url}

@app.post("/api/modules/{namespace}/{name}/{provider}/{version}/upload")
async def upload_module(
    namespace: str,
    name: str,
    provider: str,
    version: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: dict = Depends(check_permissions([Permission.UPLOAD_MODULE]))
):
    try:
        logger.debug(f"Starting upload for {namespace}/{name}/{provider}/{version}")
        
        # Validate metadata first
        logger.debug("Validating metadata")
        is_valid_metadata, metadata_errors = ModuleValidator.validate_module_metadata(
            namespace, name, provider, version
        )
        if not is_valid_metadata:
            logger.error(f"Metadata validation failed: {metadata_errors}")
            raise HTTPException(status_code=400, detail=metadata_errors)

        # Save the uploaded file first
        logger.debug("Saving uploaded file")
        storage = ModuleStorage()
        temp_path = await storage.save_module(namespace, name, provider, version, file)
        logger.debug(f"File saved to {temp_path}")

        # Now validate the saved file
        logger.debug("Validating module structure")
        is_valid_structure, structure_errors = ModuleValidator.validate_module_structure(temp_path)
        if not is_valid_structure:
            logger.error(f"Structure validation failed: {structure_errors}")
            # Clean up the invalid module
            await storage.delete_module(namespace, name, provider, version)
            raise HTTPException(status_code=400, detail=structure_errors)
        
        # Generate documentation from the saved file
        logger.debug("Generating documentation")
        docs = DocGenerator.generate_module_docs(Path(temp_path).parent)
        
        # Create GitHub repository if configured
        repo_url = None
        if os.getenv("GITHUB_TOKEN"):
            logger.debug("Creating GitHub repository")
            github_service = GitHubService(os.getenv("GITHUB_TOKEN"))
            repo_url = await github_service.create_module_repo(
                namespace, name, provider, version, Path(temp_path).parent
            )
        
        # Create database entries
        logger.debug("Creating database entries")
        try:
            # Create or get the module first
            module_id = f"{namespace}-{name}-{provider}"
            module = db.query(Module).filter_by(id=module_id).first()
            if not module:
                module = Module(
                    id=module_id,
                    namespace=namespace,
                    name=name,
                    provider=provider,
                    description="",
                    source_url=repo_url
                )
                db.add(module)
                db.flush()
            
            # Create the module version
            module_version = ModuleVersion(
                id=f"{module_id}-{version}",
                module_id=module.id,
                version=version,
                protocols=["5.0"],
                platforms=[{"os": "linux", "arch": "amd64"}],
                source_zip=temp_path,
                documentation=docs,
                repository_url=repo_url
            )
            db.add(module_version)
            db.commit()
            logger.debug("Database entries created successfully")
            
        except Exception as db_error:
            logger.error(f"Database error: {str(db_error)}")
            db.rollback()
            # Clean up stored module on database failure
            await storage.delete_module(namespace, name, provider, version)
            raise HTTPException(status_code=500, detail=f"Failed to save module metadata: {str(db_error)}")
        
        return {
            "status": "success",
            "file_path": temp_path,
            "documentation": docs,
            "repository_url": repo_url
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in upload_module: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/modules/{namespace}/{name}/{provider}/{version}/dependencies")
async def get_module_dependencies(
    namespace: str,
    name: str,
    provider: str,
    version: str,
    db: Session = Depends(get_db)
):
    module_path = ModuleStorage.get_module_path(namespace, name, provider, version)
    if not module_path:
        raise HTTPException(status_code=404, detail="Module not found")
        
    dependencies = DependencyManager.parse_dependencies(module_path.parent)
    return {"dependencies": dependencies}

@app.get("/v1/modules/{namespace}/{name}/{provider}/stats")
async def get_module_stats(
    namespace: str,
    name: str,
    provider: str,
    db: Session = Depends(get_db),
    stats_tracker: StatsTracker = Depends(get_stats_tracker)
):
    module_id = f"{namespace}-{name}-{provider}"
    return await stats_tracker.get_module_stats(db, module_id)

class GenerateModuleRequest(BaseModel):
    prompt: str
    namespace: str
    name: str
    provider: str

@app.post("/api/generate")
async def generate_module(
    request: GenerateModuleRequest,
    _: dict = Depends(check_permissions([Permission.GENERATE_MODULE]))
):
    """
    Generate a new Terraform module based on the provided prompt using Claude.
    Creates a new GitHub repository and implements the module according to best practices.
    """
    # TODO: Implement module generation logic using Claude
    pass

@app.get("/v1/modules/{namespace}/{name}/{provider}")
async def get_latest_module(
    namespace: str,
    name: str,
    provider: str,
    db: Session = Depends(get_db)
):
    """Get the latest version of a module"""
    latest_version = db.query(ModuleVersion).join(Module).filter(
        Module.namespace == namespace,
        Module.name == name,
        Module.provider == provider
    ).order_by(ModuleVersion.version.desc()).first()
    
    if not latest_version:
        raise HTTPException(status_code=404, detail="Module not found")
    
    return {
        "id": latest_version.id,
        "owner": namespace,
        "namespace": namespace,
        "name": name,
        "version": latest_version.version,
        "provider": provider,
        "description": latest_version.description,
        "source": latest_version.repository_url,
        "published_at": latest_version.created_at.isoformat(),
        "downloads": 0,  # TODO: Implement download counting
        "verified": False
    }

@app.get("/v1/modules/{namespace}/{name}/{provider}/{version}")
async def get_module_version(
    namespace: str,
    name: str,
    provider: str,
    version: str,
    db: Session = Depends(get_db)
):
    """Get a specific version of a module"""
    module_version = db.query(ModuleVersion).join(Module).filter(
        Module.namespace == namespace,
        Module.name == name,
        Module.provider == provider,
        ModuleVersion.version == version
    ).first()
    
    if not module_version:
        raise HTTPException(status_code=404, detail="Module version not found")
    
    return {
        "id": module_version.id,
        "owner": namespace,
        "namespace": namespace,
        "name": name,
        "version": version,
        "provider": provider,
        "description": module_version.description,
        "source": module_version.repository_url,
        "published_at": module_version.created_at.isoformat(),
        "downloads": 0,  # TODO: Implement download counting
        "verified": False
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)