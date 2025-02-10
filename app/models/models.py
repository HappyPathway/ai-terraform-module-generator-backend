from sqlalchemy import Column, String, JSON, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class Module(Base):
    __tablename__ = "modules"

    id = Column(String, primary_key=True)
    namespace = Column(String, nullable=False)
    name = Column(String, nullable=False)
    provider = Column(String, nullable=False)
    version = Column(String, nullable=False)
    owner = Column(String)
    description = Column(Text)
    source_url = Column(String)
    published_at = Column(DateTime, default=datetime.utcnow)

class DBModuleVersion(Base):
    __tablename__ = "module_versions"

    id = Column(String, primary_key=True)
    module_id = Column(String, ForeignKey("modules.id"))
    version = Column(String, nullable=False)
    protocols = Column(JSON)
    source_zip = Column(String)
    documentation = Column(JSON)
    repository_url = Column(String)
    published_at = Column(DateTime, default=datetime.utcnow)

    module = relationship("Module", backref="versions")