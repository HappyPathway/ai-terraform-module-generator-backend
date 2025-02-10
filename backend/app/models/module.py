from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class Module(Base):
    __tablename__ = 'modules'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    namespace = Column(String, nullable=False)
    name = Column(String, nullable=False)
    versions = relationship("ModuleVersion", back_populates="module")

class ModuleVersion(Base):
    __tablename__ = 'module_versions'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True, index=True)
    version = Column(String, nullable=False)
    module_id = Column(Integer, ForeignKey('modules.id'), nullable=False)
    protocols = Column(JSON)
    source_zip = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    module = relationship("Module", back_populates="versions")