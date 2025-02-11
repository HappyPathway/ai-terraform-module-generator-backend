"""FastAPI application for the Terraform Registry"""
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from .services.registry import RegistryService
from .database import get_db
from typing import Optional
import logging

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Terraform Registry",
    description="Private Terraform Registry implementing the Terraform Registry Protocol",
    version="1.0.0"
)

@app.get("/.well-known/terraform.json")
async def terraform_discovery(request: Request):
    """Service discovery endpoint for the Terraform Registry Protocol"""
    host = request.headers.get("X-Forwarded-Host") or request.headers.get("Host", "registry.local")
    scheme = request.headers.get("X-Forwarded-Proto") or request.url.scheme
    base_url = f"{scheme}://{host}/v1/modules/"
    
    return JSONResponse({
        "modules.v1": base_url
    }, media_type="application/json")

@app.get("/v1/modules/{namespace}/{name}/{provider}/versions")
async def list_versions(
    namespace: str,
    name: str,
    provider: str,
    db: Session = Depends(get_db)
):
    """List available versions for a module"""
    versions = await RegistryService.list_versions(db, namespace, name, provider)
    return {"modules": [{"versions": versions}]}

@app.get("/v1/modules/{namespace}/{name}/{provider}/{version}")
async def get_module_version(
    namespace: str,
    name: str,
    provider: str,
    version: str,
    db: Session = Depends(get_db)
):
    """Get a specific module version"""
    module = await RegistryService.get_module(db, namespace, name, provider, version)
    if not module:
        raise HTTPException(status_code=404, detail="Module version not found")
    return module

@app.get("/v1/modules/{namespace}/{name}/{provider}")
async def get_latest_module(
    namespace: str,
    name: str,
    provider: str,
    db: Session = Depends(get_db)
):
    """Get the latest version of a module"""
    module = await RegistryService.get_module(db, namespace, name, provider)
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    return module