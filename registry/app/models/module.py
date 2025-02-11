"""Module and ModuleVersion models for the registry"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

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