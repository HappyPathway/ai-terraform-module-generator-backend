from .cache import CacheService, get_redis_client

def get_cache_service():
    redis_client = get_redis_client()
    return CacheService(redis_client=redis_client)

__all__ = ['CacheService', 'get_cache_service', 'get_redis_client']