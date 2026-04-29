import redis
from core.config import settings

_client = None


def get_redis():
    global _client
    if _client is None:
        _client = redis.from_url(settings.REDIS_URL)
    return _client
