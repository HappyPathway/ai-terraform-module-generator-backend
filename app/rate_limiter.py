from redis import Redis
import os

class RateLimiter:
    def __init__(self, redis_client=None):
        self.redis = redis_client or Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            decode_responses=True
        )
        self.window = 60  # 1 minute window
        self.max_requests = 100  # requests per window

    async def check_rate_limit(self, key: str) -> bool:
        current = self.redis.incr(f"rate_limit:{key}")
        if current == 1:
            self.redis.expire(f"rate_limit:{key}", self.window)
        return current <= self.max_requests

def get_rate_limiter():
    return RateLimiter()