from sqlalchemy import Column, String, Integer, Boolean, DateTime
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

class Module(Base):
    __tablename__ = "modules"

    id = Column(String, primary_key=True)
    owner = Column(String)
    namespace = Column(String)
    name = Column(String)
    version = Column(String)
    provider = Column(String)
    description = Column(String, nullable=True)
    source = Column(String)
    published_at = Column(DateTime, default=datetime.utcnow)
    downloads = Column(Integer, default=0)
    verified = Column(Boolean, default=False)

    versions = relationship("ModuleVersion", back_populates="module")

class ModuleVersion(Base):
    __tablename__ = "module_versions"

    id = Column(String, primary_key=True)
    module_id = Column(String, ForeignKey("modules.id"))
    version = Column(String)
    protocols = Column(String)  # Stored as JSON string
    source_zip = Column(String)  # Path to zip file
    
    module = relationship("Module", back_populates="versions")

# Pydantic models for API responses
class ModuleProvider(BaseModel):
    name: str
    versions: List[str]

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
