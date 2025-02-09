from redis import Redis
from fastapi import HTTPException
import os
from typing import Optional
import time

class RateLimiter:
    def __init__(self):
        self.redis = Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            decode_responses=True
        )
        self.default_limit = 100  # requests
        self.default_window = 3600  # 1 hour in seconds

    async def check_rate_limit(self, key: str, limit: Optional[int] = None, window: Optional[int] = None) -> bool:
        try:
            current_limit = limit or self.default_limit
            current_window = window or self.default_window
            
            current = int(self.redis.get(key) or 0)
            if current >= current_limit:
                return False

            pipeline = self.redis.pipeline()
            pipeline.incr(key)
            pipeline.expire(key, current_window)
            pipeline.execute()
            
            return True
        except:
            # Fail open if Redis is down
            return True