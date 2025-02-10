from sqlalchemy import Column, String, Integer, Boolean, DateTime, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from .base import Base

class ModuleProvider(BaseModel):
    name: str
    versions: List[str]

class ModuleVersionBase(BaseModel):
    version: str
    protocols: List[str] = ["5.0"]
    platforms: List[Dict[str, str]] = [{"os": "linux", "arch": "amd64"}]
    source_zip: Optional[str] = None
    documentation: Optional[Dict[str, Any]] = None
    repository_url: Optional[str] = None
    description: Optional[str] = None

class ModuleVersionCreate(ModuleVersionBase):
    pass

class ModuleVersionResponse(ModuleVersionBase):
    id: str
    module_id: str
    created_at: datetime

    class Config:
        from_attributes = True

class Module(Base):
    __tablename__ = 'modules'
    __table_args__ = {'extend_existing': True}

    id = Column(String, primary_key=True)
    namespace = Column(String, nullable=False)
    name = Column(String, nullable=False)
    provider = Column(String, nullable=False)
    description = Column(String, nullable=True)
    source_url = Column(String)
    published_at = Column(DateTime, default=datetime.utcnow)
    downloads = Column(Integer, default=0)
    verified = Column(Boolean, default=False)
    owner = Column(String)

    versions = relationship("ModuleVersion", back_populates="module", cascade="all, delete-orphan")

class ModuleVersion(Base):
    __tablename__ = 'module_versions'
    __table_args__ = {'extend_existing': True}

    id = Column(String, primary_key=True)
    module_id = Column(String, ForeignKey('modules.id'), nullable=False)
    version = Column(String, nullable=False)
    protocols = Column(JSON)
    platforms = Column(JSON)
    source_zip = Column(String)
    documentation = Column(JSON)
    repository_url = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    description = Column(String, nullable=True)

    module = relationship("Module", back_populates="versions")

# Pydantic models for API responses
class ModuleResponse(BaseModel):
    id: str
    owner: str
    namespace: str
    name: str
    version: str
    provider: str
    description: Optional[str]
    source: str
    published_at: str
    downloads: int
    verified: bool

class ModuleDetail(ModuleResponse):
    root: Optional[dict]
    submodules: List[dict]
    providers: List[ModuleProvider]
    dependencies: List[dict]
