from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from .base import Base

class DBModule(Base):
    __tablename__ = "modules"
    __table_args__ = {'extend_existing': True}

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

    versions = relationship("DBModuleVersion", back_populates="module")

class DBModuleVersion(Base):
    __tablename__ = "module_versions"
    __table_args__ = {'extend_existing': True}

    id = Column(String, primary_key=True)
    module_id = Column(String, ForeignKey("modules.id"))
    version = Column(String)
    protocols = Column(String)
    source_zip = Column(String)
    
    module = relationship("DBModule", back_populates="versions")

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
