from fastapi import FastAPI, Depends, HTTPException, Request, UploadFile, File
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional, List, Dict
from pydantic import BaseModel
import json, os, logging, tempfile
from pathlib import Path
from .database import get_db, engine, Base
from .models import Module, ModuleResponse, DBModuleVersion
from .storage import ModuleStorage
from .validation import ModuleValidator
from .github import GitHubService
from .docs import DocGenerator
from .auth.auth import verify_token
from .auth.dependencies import check_permissions, Permission
from .cache import CacheService
from .search import SearchService
from .middleware import RateLimiter
from .stats import StatsTracker
from .dependencies import DependencyManager

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

class ModuleVersion(BaseModel):
    version: str
    protocols: List[str]
    platforms: List[dict]

class ModuleVersions(BaseModel):
    modules: List[ModuleVersion]

@app.get("/.well-known/terraform.json")
async def terraform_discovery():
    return JSONResponse({
        "modules.v1": "/v1/modules/",
        "providers.v1": "/v1/providers/"
    })

# Initialize services with dependency injection support
def get_cache_service():
    return CacheService()

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
    response = {"modules": [module.dict() for module in results]}
    await cache_service.set(cache_key, response)
    return response

@app.get("/v1/modules/{namespace}/{name}/{provider}/versions")
async def list_versions(
    namespace: str,
    name: str,
    provider: str,
    db: Session = Depends(get_db)
):
    modules = db.query(Module).filter(
        Module.namespace == namespace,
        Module.name == name,
        Module.provider == provider
    ).all()
    
    if not modules:
        raise HTTPException(status_code=404, detail="Module not found")
    
    versions = [ModuleResponse.from_orm(module) for module in modules]
    return {"modules": versions}

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
    # Validate metadata
    logger.debug(f"Validating metadata: namespace={namespace}, name={name}, provider={provider}, version={version}")
    is_valid_metadata, metadata_errors = ModuleValidator.validate_module_metadata(
        namespace, name, provider, version
    )
    if not is_valid_metadata:
        logger.error(f"Metadata validation failed: {metadata_errors}")
        raise HTTPException(status_code=400, detail=metadata_errors)

    # Save file temporarily for validation
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
    try:
        content = await file.read()
        with open(temp_file.name, 'wb') as f:
            f.write(content)
        logger.debug(f"Module saved temporarily at {temp_file.name}")
        
        # Validate module structure
        logger.debug(f"Validating module structure at {temp_file.name}")
        is_valid_structure, structure_errors = ModuleValidator.validate_module_structure(temp_file.name)
        if not is_valid_structure:
            logger.error(f"Structure validation failed: {structure_errors}")
            raise HTTPException(status_code=400, detail=list(structure_errors.values()))
        
        # Store module
        storage = ModuleStorage()
        temp_path = await storage.save_module(namespace, name, provider, version, file)
        
        # Generate documentation
        logger.debug("Generating documentation")
        docs = DocGenerator.generate_module_docs(Path(temp_path).parent)
        
        # Create GitHub repository
        github_service = GitHubService(os.getenv("GITHUB_TOKEN"))
        repo_url = await github_service.create_module_repo(
            namespace, name, provider, version, Path(temp_path).parent
        )
        
        # Update database with new module version and documentation
        module_version = DBModuleVersion(
            id=f"{namespace}-{name}-{provider}-{version}",
            module_id=f"{namespace}-{name}-{provider}",
            version=version,
            protocols=json.dumps(["5.0"]),
            source_zip=temp_path,
            documentation=json.dumps(docs),
            repository_url=repo_url
        )
        db.add(module_version)
        db.commit()
        
        return {
            "status": "success",
            "file_path": temp_path,
            "documentation": docs,
            "repository_url": repo_url
        }
    finally:
        if os.path.exists(temp_file.name):
            os.unlink(temp_file.name)

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)