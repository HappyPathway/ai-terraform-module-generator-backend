from redis import Redis
import json
from typing import Optional, Any
import os

def get_redis_client(host=None, port=None):
    return Redis(
        host=host or os.getenv("REDIS_HOST", "localhost"),
        port=int(port or os.getenv("REDIS_PORT", 6379)),
        decode_responses=True
    )

class CacheService:
    def __init__(self, redis_client=None):
        self.redis = redis_client or get_redis_client()
        self.ttl = 3600  # 1 hour cache

    async def get(self, key: str) -> Optional[Any]:
        try:
            data = self.redis.get(key)
            return json.loads(data) if data else None
        except:
            return None

    async def set(self, key: str, value: Any) -> bool:
        try:
            self.redis.setex(key, self.ttl, json.dumps(value))
            return True
        except:
            return False

    async def invalidate(self, key: str) -> bool:
        try:
            self.redis.delete(key)
            return True
        except:
            return False
