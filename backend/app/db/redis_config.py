import fnmatch
import json
import os
import time
from typing import Any

import redis.asyncio as redis
from dotenv import load_dotenv

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "3"))
REDIS_BACKEND = os.getenv("REDIS_BACKEND", "auto").lower()

redis_client = None


class MemoryRedis:
    def __init__(self):
        self._data: dict[str, tuple[str, float | None]] = {}

    def _cleanup(self):
        now = time.time()
        expired = [
            key
            for key, (_, expires_at) in self._data.items()
            if expires_at is not None and expires_at <= now
        ]
        for key in expired:
            self._data.pop(key, None)

    async def ping(self):
        self._cleanup()
        return True

    async def get(self, key: str):
        self._cleanup()
        item = self._data.get(key)
        return item[0] if item else None

    async def set(self, key: str, value: Any, ex: int | None = None):
        expires_at = time.time() + ex if ex else None
        self._data[key] = (str(value), expires_at)
        return True

    async def setex(self, key: str, seconds: int, value: Any):
        return await self.set(key, value, ex=seconds)

    async def incr(self, key: str):
        self._cleanup()
        current, expires_at = self._data.get(key, ("0", None))
        next_value = int(current) + 1
        self._data[key] = (str(next_value), expires_at)
        return next_value

    async def keys(self, pattern: str):
        self._cleanup()
        return [key for key in self._data if fnmatch.fnmatch(key, pattern)]

    async def delete(self, key: str):
        existed = key in self._data
        self._data.pop(key, None)
        return 1 if existed else 0

    async def aclose(self):
        return None


memory_redis_client = MemoryRedis()


async def connect_redis():
    global redis_client
    if redis_client is not None:
        return redis_client

    if REDIS_BACKEND == "memory":
        redis_client = memory_redis_client
        return redis_client

    try:
        candidate = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True,
        )
        await candidate.ping()
        redis_client = candidate
    except Exception:
        redis_client = memory_redis_client

    return redis_client


async def close_redis():
    global redis_client
    if redis_client:
        await redis_client.aclose()
        redis_client = None


async def check_redis_connection() -> bool:
    try:
        client = await connect_redis()
        await client.ping()
        return True
    except Exception as e:
        print(f"Redis connection failed: {e}")
        return False


async def get_redis_cache_str(key: str) -> str | None:
    try:
        client = await connect_redis()
        return await client.get(key)
    except Exception as e:
        print(f"Failed to read redis string cache: {e}")
        return None


async def get_redis_cache_json(key: str) -> dict | None:
    try:
        client = await connect_redis()
        data = await client.get(key)
        if data:
            return json.loads(data)
        return None
    except Exception as e:
        print(f"Failed to read redis json cache: {e}")
        return None


async def set_redis_cache(key: str, value: Any, expire: int = 3600) -> bool:
    try:
        client = await connect_redis()
        if isinstance(value, str):
            await client.set(key, value, ex=expire)
        elif isinstance(value, (dict, list)):
            await client.set(key, json.dumps(value, ensure_ascii=False), ex=expire)
        else:
            await client.set(key, str(value), ex=expire)
        return True
    except Exception as e:
        print(f"Failed to write redis cache: {e}")
        return False
