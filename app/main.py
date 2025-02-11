from fastapi import FastAPI, File, HTTPException, Depends, Request, UploadFile, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
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
import semver

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

# Change base path to match protocol exactly
API_BASE = "/v1/modules"

@app.get("/.well-known/terraform.json")
async def terraform_discovery(request: Request):
    """Registry discovery protocol endpoint"""
    # Build URL relative to the current host, ensuring trailing slash
    host = request.headers.get("X-Forwarded-Host") or request.headers.get("Host", "registry.local")
    scheme = request.headers.get("X-Forwarded-Proto") or request.url.scheme
    base_url = f"{scheme}://{host}/v1/modules/"
    
    return JSONResponse({
        "modules.v1": "/v1/modules/"  # Return relative URL with trailing slash as per protocol
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

@app.get(f"{API_BASE}/search")
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
    if (cached_result):
        return cached_result
        
    results = await SearchService.search_modules(
        db, query, provider, namespace, limit, offset
    )
    # Convert SQLAlchemy models to Pydantic response models
    modules = []
    for module in results:
        # Get the latest version for each module
        latest_version = max(module.versions, key=lambda v: v.version) if module.versions else None
        if (latest_version):
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

@app.get(f"{API_BASE}/{{namespace}}/{{name}}/{{system}}/versions")
async def list_versions(
    namespace: str,
    name: str,
    system: str,
    db: Session = Depends(get_db)
):
    """List available versions for a module"""
    try:
        logger.debug(f"Querying versions for {namespace}/{name}/{system}")
        versions = db.query(ModuleVersion).join(Module).filter(
            Module.namespace == namespace,
            Module.name == name,
            Module.provider == system
        ).all()
        
        logger.debug(f"Found versions: {[v.version for v in versions]}")
        
        # Validate and sort versions according to semver
        valid_versions = []
        for v in versions:
            try:
                semver.Version.parse(v.version)
                valid_versions.append(v)
            except ValueError:
                logger.warning(f"Invalid semver version found: {v.version}")
                continue
        
        logger.debug(f"Valid versions: {[v.version for v in valid_versions]}")
        
        # Sort by semver, not string comparison
        sorted_versions = sorted(valid_versions, 
                               key=lambda x: semver.Version.parse(x.version), 
                               reverse=True)
        
        logger.debug(f"Sorted versions: {[v.version for v in sorted_versions]}")
        
        # Format exactly as specified in protocol
        result = {
            "modules": [{
                "versions": [{"version": v.version} for v in sorted_versions]
            }]
        }
        logger.debug(f"Returning response: {result}")
        return JSONResponse(content=result, media_type="application/json")
        
    except Exception as e:
        logger.error(f"Error listing versions: {str(e)}")
        raise HTTPException(status_code=404, detail="Module not found")

@app.get(f"{API_BASE}/{{namespace}}/{{name}}/{{system}}/{{version}}/download")
async def get_download_url(
    namespace: str,
    name: str,
    system: str,
    version: str,
    db: Session = Depends(get_db)
):
    """Get download URL for a specific module version"""
    try:
        module_version = db.query(ModuleVersion).join(Module).filter(
            Module.namespace == namespace,
            Module.name == name,
            Module.provider == system,
            ModuleVersion.version == version
        ).first()
        
        if not module_version:
            raise HTTPException(status_code=404, detail="Module version not found")
            
        # Point to the archive download endpoint
        response = Response(status_code=204)
        response.headers["X-Terraform-Get"] = f"./source"
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting download URL: {str(e)}")
        raise HTTPException(status_code=404, detail="Module version not found")

@app.get(f"{API_BASE}/{{namespace}}/{{name}}/{{system}}/{{version}}/source")
async def download_module_source(
    namespace: str,
    name: str,
    system: str,
    version: str,
    db: Session = Depends(get_db)
):
    """Download the module source code following HashiCorp protocol"""
    try:
        logger.debug(f"Handling source download for {namespace}/{name}/{system}/{version}")
        module_version = db.query(ModuleVersion).join(Module).filter(
            Module.namespace == namespace,
            Module.name == name,
            Module.provider == system,
            ModuleVersion.version == version
        ).first()
        
        if not module_version:
            logger.error("Module version not found")
            raise HTTPException(status_code=404, detail="Module version not found")

        # Return GitHub URL if available
        if module_version.repository_url:
            logger.debug(f"Returning repository URL: {module_version.repository_url}")
            # Convert GitHub URL to tarball format
            # From: https://github.com/owner/repo
            # To: https://api.github.com/repos/owner/repo/tarball/version//*?archive=tar.gz
            repo_url = module_version.repository_url.replace("https://github.com/", "https://api.github.com/repos/")
            tarball_url = f"{repo_url}/tarball/{version}//*?archive=tar.gz"
            response = Response(
                status_code=204,
                headers={
                    "X-Terraform-Get": tarball_url
                }
            )
            return response
            
        logger.error("No GitHub repository URL found for module")
        raise HTTPException(status_code=404, detail="Module source not found in GitHub")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting module source: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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
        
        # Check if version already exists
        existing_version = db.query(ModuleVersion).join(Module).filter(
            Module.namespace == namespace,
            Module.name == name,
            Module.provider == provider,
            ModuleVersion.version == version
        ).first()
        
        if existing_version:
            raise HTTPException(
                status_code=409,
                detail=f"Version {version} already exists for module {namespace}/{name}/{provider}. Please use a different version number."
            )

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

@app.get(f"{API_BASE}/{{namespace}}/{{name}}/{{system}}/{{version}}/dependencies")
async def get_module_dependencies(
    namespace: str,
    name: str,
    system: str,
    version: str,
    db: Session = Depends(get_db)
):
    module_path = ModuleStorage.get_module_path(namespace, name, system, version)
    if not module_path:
        raise HTTPException(status_code=404, detail="Module not found")
        
    dependencies = DependencyManager.parse_dependencies(module_path.parent)
    return {"dependencies": dependencies}

@app.get(f"{API_BASE}/{{namespace}}/{{name}}/{{system}}/stats")
async def get_module_stats(
    namespace: str,
    name: str,
    system: str,
    db: Session = Depends(get_db),
    stats_tracker: StatsTracker = Depends(get_stats_tracker)
):
    module_id = f"{namespace}-{name}-{system}"
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

@app.get(f"{API_BASE}/{{namespace}}/{{name}}/{{system}}")
async def get_latest_module(
    namespace: str,
    name: str,
    system: str,
    db: Session = Depends(get_db)
):
    """Get the latest version of a module"""
    latest_version = db.query(ModuleVersion).join(Module).filter(
        Module.namespace == namespace,
        Module.name == name,
        Module.provider == system
    ).order_by(ModuleVersion.version.desc()).first()
    
    if not latest_version:
        raise HTTPException(status_code=404, detail="Module not found")
    
    return {
        "id": latest_version.id,
        "owner": namespace,
        "namespace": namespace,
        "name": name,
        "version": latest_version.version,
        "provider": system,
        "description": latest_version.description,
        "source": latest_version.repository_url,
        "published_at": latest_version.created_at.isoformat(),
        "downloads": 0,  # TODO: Implement download counting
        "verified": False
    }

@app.get(f"{API_BASE}/{{namespace}}/{{name}}/{{system}}/{{version}}")
async def get_module_version(
    namespace: str,
    name: str,
    system: str,
    version: str,
    db: Session = Depends(get_db)
):
    """Get a specific version of a module"""
    module_version = db.query(ModuleVersion).join(Module).filter(
        Module.namespace == namespace,
        Module.name == name,
        Module.provider == system,
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
        "provider": system,
        "description": module_version.description,
        "source": module_version.repository_url,
        "published_at": module_version.created_at.isoformat(),
        "downloads": 0,  # TODO: Implement download counting
        "verified": False
    }

@app.get(f"{API_BASE}/{{namespace}}/{{name}}/{{system}}/archive/module.zip")
async def download_module_archive(
    namespace: str,
    name: str,
    system: str,
    version: str,
    db: Session = Depends(get_db)
):
    """Download the module archive zip file"""
    try:
        module_version = db.query(ModuleVersion).join(Module).filter(
            Module.namespace == namespace,
            Module.name == name,
            Module.provider == system,
            ModuleVersion.version == version
        ).first()
        
        if not module_version:
            raise HTTPException(status_code=404, detail="Module version not found")
            
        if not module_version.source_zip or not os.path.exists(module_version.source_zip):
            raise HTTPException(status_code=404, detail="Module archive not found")
            
        # Return the actual zip file
        return FileResponse(
            module_version.source_zip,
            media_type="application/zip",
            filename=f"{namespace}-{name}-{system}-{version}.zip"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading module archive: {str(e)}")
        raise HTTPException(status_code=500, detail="Error accessing module archive")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)