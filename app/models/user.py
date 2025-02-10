from sqlalchemy import Column, String, Boolean, DateTime
from datetime import datetime
from .base import Base

class DBUser(Base):
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}

    id = Column(String, primary_key=True)
    username = Column(String, unique=True)
    hashed_password = Column(String)
    role = Column(String)
    disabled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
