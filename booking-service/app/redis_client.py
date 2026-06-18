import redis.asyncio as aioredis
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_pool = aioredis.from_url(REDIS_URL, decode_responses=True)


async def get_redis() -> aioredis.Redis:
    return redis_pool
