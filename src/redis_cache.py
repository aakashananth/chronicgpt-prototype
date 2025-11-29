"""Redis cache client module for caching pipeline results."""

import json
from typing import Any, Dict, List, Optional

import redis
from redis.exceptions import RedisError, TimeoutError

from .config import config


class RedisCacheClient:
    """Client for interacting with Azure Cache for Redis."""

    def __init__(self, redis_config=None):
        """Initialize the Redis cache client.

        Args:
            redis_config: Optional RedisConfig instance. If not provided,
                uses the global config from src.config.
        """
        if redis_config is None:
            redis_config = config.redis

        self.host = redis_config.host
        self.port = redis_config.port
        self.password = redis_config.password
        self.ssl = redis_config.ssl
        self._redis_client = None

    def _get_redis_client(self) -> Optional[redis.Redis]:
        """Get or create the Redis client.

        Returns:
            Redis client instance, or None if Redis is not configured.
        """
        if not self.host or not self.password:
            return None

        if self._redis_client is None:
            try:
                # Azure Redis Cache connection parameters with shorter timeouts
                self._redis_client = redis.Redis(
                    host=self.host,
                    port=self.port,
                    password=self.password,
                    ssl=self.ssl,
                    ssl_cert_reqs=None,
                    decode_responses=True,
                    socket_connect_timeout=3,  # Reduced from 10 to 3 seconds
                    socket_timeout=3,  # Reduced from 10 to 3 seconds
                    retry_on_timeout=False,  # Don't retry on timeout
                    health_check_interval=30,  # Check connection health every 30s
                )
                # Test connection with a very short timeout
                # Use a separate connection for ping to avoid blocking
                try:
                    self._redis_client.ping()
                except (TimeoutError, redis.ConnectionError, redis.TimeoutError):
                    # If ping fails, mark client as None so we don't use it
                    self._redis_client = None
                    raise
            except (TimeoutError, redis.TimeoutError) as e:
                print(f"Warning: Redis connection timeout: {e}")
                print(f"  Host: {self.host}, Port: {self.port}")
                print(f"  This usually means:")
                print(
                    f"    1. Firewall blocking connection (check Azure Redis firewall rules)"
                )
                print(f"    2. Network connectivity issue")
                print(f"    3. Wrong host/port")
                self._redis_client = None
            except redis.ConnectionError as e:
                print(f"Warning: Redis connection failed: {e}")
                print(f"  Host: {self.host}, Port: {self.port}, SSL: {self.ssl}")
                self._redis_client = None
            except redis.AuthenticationError as e:
                print(f"Warning: Redis authentication failed: {e}")
                print(f"  Check your REDIS_ACCESS_KEY in .env (this is the Primary/Secondary key from Azure Redis Cache)")
                self._redis_client = None
            except Exception as e:
                print(f"Warning: Redis error: {type(e).__name__}: {e}")
                self._redis_client = None

        return self._redis_client

    def cache_pipeline_result(
        self, result: Dict[str, Any], cache_key: str = "latest_pipeline_result"
    ) -> bool:
        """Cache the complete pipeline result.

        Args:
            result: Dictionary containing pipeline results (enriched, recent_anomalies,
                explanation, parquet_path, blob_path).
            cache_key: Key to use for caching (default: "latest_pipeline_result").

        Returns:
            True if cached successfully, False otherwise.
        """
        redis_client = self._get_redis_client()
        if redis_client is None:
            return False

        try:
            # Convert DataFrame to dict for JSON serialization
            cache_data = result.copy()
            if "enriched" in cache_data:
                # Store enriched DataFrame as JSON (simplified)
                cache_data["enriched"] = "DataFrame cached separately"

            # Store as JSON string with timeout handling
            redis_client.setex(
                cache_key, 86400, json.dumps(cache_data, default=str)
            )  # 24 hour TTL

            # Cache individual components (these will fail gracefully if Redis is down)
            if "recent_anomalies" in result:
                self._cache_value("cached_anomalies", result["recent_anomalies"])
            if "explanation" in result:
                self._cache_value("cached_explanation", result["explanation"])
            if "blob_path" in result:
                self._cache_value("cached_blob_path", result["blob_path"])

            return True
        except (RedisError, TimeoutError, redis.TimeoutError, redis.ConnectionError, json.JSONEncodeError) as e:
            # Mark client as None so we don't retry with a bad connection
            self._redis_client = None
            print(f"Warning: Failed to cache pipeline result: {e}")
            return False

    def get_cached_metrics(
        self, cache_key: str = "latest_pipeline_result"
    ) -> Optional[Dict[str, Any]]:
        """Get cached metrics data.

        Args:
            cache_key: Key used for caching (default: "latest_pipeline_result").

        Returns:
            Cached metrics dictionary, or None if not found or Redis unavailable.
        """
        redis_client = self._get_redis_client()
        if redis_client is None:
            return None

        try:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
            return None
        except (RedisError, TimeoutError, redis.TimeoutError, redis.ConnectionError, json.JSONDecodeError):
            # Mark client as None so we don't retry with a bad connection
            self._redis_client = None
            return None

    def get_cached_anomalies(self) -> Optional[List[Dict[str, Any]]]:
        """Get cached anomalies list.

        Returns:
            Cached anomalies list, or None if not found or Redis unavailable.
        """
        return self._get_cached_value("cached_anomalies")

    def get_cached_explanation(self) -> Optional[str]:
        """Get cached LLM explanation.

        Returns:
            Cached explanation string, or None if not found or Redis unavailable.
        """
        return self._get_cached_value("cached_explanation")

    def get_cached_blob_path(self) -> Optional[str]:
        """Get cached Azure Blob Storage path.

        Returns:
            Cached blob path string, or None if not found or Redis unavailable.
        """
        return self._get_cached_value("cached_blob_path")

    def _cache_value(self, key: str, value: Any, ttl: int = 86400) -> bool:
        """Internal helper to cache a value.

        Args:
            key: Cache key.
            value: Value to cache.
            ttl: Time to live in seconds (default: 86400 = 24 hours).

        Returns:
            True if cached successfully, False otherwise.
        """
        redis_client = self._get_redis_client()
        if redis_client is None:
            return False

        try:
            if isinstance(value, (dict, list)):
                redis_client.setex(key, ttl, json.dumps(value, default=str))
            else:
                redis_client.setex(key, ttl, str(value))
            return True
        except (RedisError, TimeoutError, redis.TimeoutError, redis.ConnectionError, json.JSONEncodeError):
            # Mark client as None so we don't retry with a bad connection
            self._redis_client = None
            return False

    def _get_cached_value(self, key: str) -> Optional[Any]:
        """Internal helper to get a cached value.

        Args:
            key: Cache key.

        Returns:
            Cached value, or None if not found or Redis unavailable.
        """
        redis_client = self._get_redis_client()
        if redis_client is None:
            return None

        try:
            cached_value = redis_client.get(key)
            if cached_value is None:
                return None

            # Try to parse as JSON, fallback to string
            try:
                return json.loads(cached_value)
            except json.JSONDecodeError:
                return cached_value
        except (RedisError, TimeoutError, redis.TimeoutError, redis.ConnectionError):
            # Mark client as None so we don't retry with a bad connection
            self._redis_client = None
            return None
