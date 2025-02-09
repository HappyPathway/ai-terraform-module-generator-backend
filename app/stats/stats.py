from redis import Redis
import json
from typing import Dict, Any, Optional
import os

class StatsTracker:
    def __init__(self):
        self.redis = Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            decode_responses=True
        )
        
    async def track_download(self, module_id: str) -> bool:
        try:
            self.redis.hincrby(f"module:{module_id}:stats", "downloads", 1)
            return True
        except:
            return False

    async def get_stats(self, module_id: str) -> Optional[Dict[str, Any]]:
        try:
            stats = self.redis.hgetall(f"module:{module_id}:stats")
            if not stats:
                return {"downloads": 0}
            return {
                "downloads": int(stats.get("downloads", 0))
            }
        except:
            return {"downloads": 0}