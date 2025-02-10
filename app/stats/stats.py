from redis import Redis
import json
from typing import Dict, Any, Optional
import os
from sqlalchemy.orm import Session
import redis
from sqlalchemy import func
from ..models.models import Module, ModuleVersion

class StatsTracker:
    def __init__(self, redis_client=None):
        self.redis = redis_client or Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            decode_responses=True
        )

    async def track_download(self, module_id: str) -> bool:
        try:
            return bool(self.redis.hincrby(f"stats:downloads:{module_id}", "count", 1))
        except:
            return False

    async def get_stats(self, module_id: str) -> dict:
        try:
            stats = self.redis.hgetall(f"stats:downloads:{module_id}")
            return {"downloads": int(stats.get("count", 0))}
        except:
            return {"downloads": 0}

    @staticmethod
    async def get_module_stats(db: Session, module_id: str) -> dict:
        """Get download and version statistics for a module"""
        module = db.query(Module).filter(Module.id == module_id).first()
        if not module:
            return {}
            
        versions = db.query(ModuleVersion).filter(
            ModuleVersion.module_id == module_id
        ).count()

        return {
            "downloads": 0,  # Implement download tracking in future
            "versions": versions,
            "published_at": module.published_at.isoformat() if module.published_at else None
        }
        
    @staticmethod
    async def record_download(db: Session, module_id: str) -> None:
        """Record a module download - stub for future implementation"""
        pass

def get_stats_tracker():
    return StatsTracker()