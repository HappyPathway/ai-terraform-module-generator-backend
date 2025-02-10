from sqlalchemy.orm import Session
from typing import List, Optional
from ..models import Module

class SearchService:
    @staticmethod
    async def search_modules(
        db: Session,
        query: str = "",
        provider: Optional[str] = None,
        namespace: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[Module]:
        filter_conditions = []
        if query:
            filter_conditions.append(Module.name.ilike(f"%{query}%"))
        if provider:
            filter_conditions.append(Module.provider == provider)
        if namespace:
            filter_conditions.append(Module.namespace == namespace)
        
        return db.query(Module).filter(*filter_conditions).offset(offset).limit(limit).all()