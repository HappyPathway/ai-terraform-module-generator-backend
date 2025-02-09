from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import registry

mapper_registry = registry()
Base = mapper_registry.generate_base()
