from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, JSON, Boolean
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
    source = Column(String)
    published_at = Column(DateTime, default=datetime.utcnow)
    downloads = Column(Integer, default=0)
    verified = Column(Boolean, default=False)
    versions = relationship("ModuleVersion", back_populates="module")

class ModuleVersion(Base):
    __tablename__ = 'module_versions'
    __table_args__ = {'extend_existing': True}

    id = Column(String, primary_key=True)
    version = Column(String, nullable=False)
    module_id = Column(String, ForeignKey('modules.id'), nullable=False)
    protocols = Column(JSON)
    platforms = Column(JSON)
    source_zip = Column(String)
    documentation = Column(JSON)
    repository_url = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    module = relationship("Module", back_populates="versions")