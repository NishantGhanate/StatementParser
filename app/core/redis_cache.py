"""
Handles redis related operations

> source .env
> python ./app/core/redis_handler.py
"""

import json
import logging
import threading
from urllib.parse import urlparse, urlunparse

import redis

from app.config.settings import settings

logger = logging.getLogger("app")


def _force_db(url: str, db: int) -> str:
    """Replace the path with /{db} while keeping scheme/host/port/user/pass/query."""
    p = urlparse(url)
    return urlunparse((p.scheme, p.netloc, f"/{db}", p.params, p.query, p.fragment))


class RedisCache(redis.Redis):
    """
    Singleton Redis client (inherits redis.Redis) with helpers for RediSearch/JSON.
    """

    _instance = None
    _lock = threading.Lock()
    _initialized = False

    def __new__(cls, *args, **kwargs):
        # double-checked locking
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        *,
        url: str | None = None,
        db: int | None = None,
        decode_responses: bool = True,
        **kwargs,
    ):
        """
        Initialize ONCE. You can give a full URL or host/port/… in kwargs.
        If url is provided, we build a connection_pool from it (optionally forcing db).
        """
        if self._initialized:
            logger.debug("Reusing redis instance")
            return

        # Build connection pool in a robust way
        if url:
            if db is not None:
                url = _force_db(url, db)

            base = redis.from_url(url, decode_responses=decode_responses)
            pool = base.connection_pool
            super().__init__(connection_pool=pool, decode_responses=decode_responses)
        else:
            # fallback to kwargs such as host, port, password, db …
            super().__init__(decode_responses=decode_responses, **kwargs)

        self._initialized = True
        logger.info(
            "RedisCache connected: url=%s db=%s",
            url or kwargs,
            self.connection_pool.connection_kwargs.get("db", 0),
        )

    def set_cache(self, key, data, expiration_seconds=3600):
        """
        Sets a key with a serialized value and an optional expiration time.

        Args:
            key (str): The cache key.
            data: The Python object to store. It will be serialized to JSON.
            expiration_seconds (int): The cache expiration time in seconds.
        """
        try:
            serialized_data = json.dumps(data)
            self.setex(key, expiration_seconds, serialized_data)
            logger.debug(f"Cache set for key: {key}")
        except redis.RedisError as e:
            logger.error(f"Error setting cache for key '{key}': {e}")
        except Exception:
            logger.exception(f"Failed Set cache for {key} : {data}")

    # To prevent override from parent
    def get_kache(self, key: str):
        """Get and JSON-deserialize if possible."""
        val = self.get(key)
        if val is None:
            return None
        try:
            return json.loads(val.encode("utf-8"))
        except json.JSONDecodeError as jde:
            logger.error(f"Decode failed for key: {key} : {val}, error: {jde}")
            return val

    def clear_cache(self, key: str):
        """
        delete specific key cache
        """
        self.delete(key)

    def clear_all_cache(self):
        """
        clear the cache from connected db-0
        """
        self.flushdb()

    @classmethod
    def from_env(cls, *, force_db0: bool = True):
        """
        Create the singleton using REDIS_URL/REDIS_SEARCH_URL from env.
        If force_db0=True, we coerce the DB to 0 (required for FT/JSON).
        """
        raw = settings.REDIS_URL or "redis://localhost:6379/0"
        db = (
            0
            if force_db0
            else (redis.from_url(raw).connection_pool.connection_kwargs.get("db", 0))
        )
        return cls(url=raw, db=db)


redis_cache = RedisCache.from_env(force_db0=False)


if __name__ == "__main__":

    def get_user_data(user_id):
        """
        Simulates a heavy operation (e.g., a database query) to fetch user data.
        """
        print(f"Fetching user data from the database for user: {user_id}...")
        return {"id": user_id, "name": f"User {user_id}", "role": "member"}

    def main():
        """
        Main function to demonstrate caching.
        """
        # Create an instance of the cache utility class.
        # The Singleton pattern ensures this is a single, reusable object.
        cache = RedisCache.from_env(force_db0=False)

        user_id = 123
        cache_key = f"user:{user_id}"

        # 1. First fetch: No cache exists, so it will hit the database
        user = cache.get_kache(cache_key)
        if user:
            print(f"Cache hit for user {user_id}: {user}")
        else:
            print(f"Cache miss for user {user_id}. Fetching from database...")
            user = get_user_data(user_id)
            cache.set_cache(
                cache_key, user, expiration_seconds=60
            )  # Cache for 60 seconds
            print(f"Fetched and cached user: {user}")

        print("-" * 20)

        # 2. Second fetch: Now the cache exists and will be used
        user = cache.get_kache(cache_key)
        if user:
            print(f"Cache hit for user {user_id}: {user}")
        else:
            print(f"Cache miss for user {user_id}. Fetching from database...")
            user = get_user_data(user_id)
            cache.set_cache(cache_key, user)
            print(f"Fetched and cached user: {user}")

        print("-" * 20)

        # 3. Clear the cache for the specific key
        cache.clear_cache(cache_key)
        user = cache.get_kache(cache_key)
        if user:
            print(f"Cache hit for user {user_id}: {user}")
        else:
            print(f"Cache miss for user {user_id}. Key was cleared.")

        # Example of clearing ALL cache (use with caution)
        # cache.clear_all_cache()

    main()



