import threading
from typing import Any, Dict, Generator, Iterable, List, Optional, Union

from redis import Redis
from redis.exceptions import RedisError, ConnectionError

from app.core.config import settings
from app.core.logging import logger


RedisValue = Union[str, int, float, bytes]


class RedisClient:
    def __init__(
        self,
        url: str,
        *,
        decode_responses: bool = True,
        key_prefix: Optional[str] = None,
        health_check_interval: int = 0,
    ):
        self.url = url
        self.decode_responses = decode_responses
        self.key_prefix = key_prefix or settings.app_name
        self.health_check_interval = health_check_interval
        self._client: Optional[Redis] = None
        self._lock = threading.Lock()

    # --- Lifecycle ---
    def initialize(self) -> None:
        try:
            self._client = Redis.from_url(
                self.url,
                decode_responses=self.decode_responses,
                health_check_interval=self.health_check_interval,
            )
            # Try a ping to validate the connection (lazy connection otherwise)
            self._client.ping()
            logger.info("redis_connected", url=self._redacted_url())
        except (ConnectionError, RedisError) as exc:
            logger.error("redis_connect_error", error=str(exc), url=self._redacted_url())
            # Do not raise to keep app starting; operations will fail gracefully until redis is up

    def close(self) -> None:
        with self._lock:
            if self._client is not None:
                try:
                    self._client.close()
                except Exception:
                    pass
                finally:
                    self._client = None

    # --- Helpers ---
    def _namespaced(self, key: str) -> str:
        return f"{self.key_prefix}:{key}" if self.key_prefix else key

    def _ensure(self) -> Optional[Redis]:
        if self._client is None:
            try:
                self.initialize()
            except Exception:
                return None
        return self._client

    def _redacted_url(self) -> str:
        if "@" in self.url:
            # redact password-like content
            try:
                prefix, rest = self.url.split("://", 1)
                auth_and_host = rest.split("@", 1)
                if len(auth_and_host) == 2:
                    _auth, host = auth_and_host
                    return f"{prefix}://***:***@{host}"
            except Exception:
                pass
        return self.url

    # --- Basic KV operations ---
    def get(self, key: str) -> Optional[str]:
        client = self._ensure()
        if client is None:
            return None
        try:
            return client.get(self._namespaced(key))
        except RedisError as exc:
            logger.error("redis_get_error", key=key, error=str(exc))
            return None

    def set(
        self,
        key: str,
        value: RedisValue,
        *,
        ex: Optional[int] = None,
        px: Optional[int] = None,
        nx: bool = False,
        xx: bool = False,
    ) -> bool:
        client = self._ensure()
        if client is None:
            return False
        try:
            result = client.set(self._namespaced(key), value, ex=ex, px=px, nx=nx, xx=xx)
            return bool(result)
        except RedisError as exc:
            logger.error("redis_set_error", key=key, error=str(exc))
            return False

    def delete(self, *keys: str) -> int:
        client = self._ensure()
        if client is None or not keys:
            return 0
        try:
            namespaced = [self._namespaced(k) for k in keys]
            return int(client.delete(*namespaced))
        except RedisError as exc:
            logger.error("redis_delete_error", keys=list(keys), error=str(exc))
            return 0

    def exists(self, key: str) -> bool:
        client = self._ensure()
        if client is None:
            return False
        try:
            return client.exists(self._namespaced(key)) == 1
        except RedisError as exc:
            logger.error("redis_exists_error", key=key, error=str(exc))
            return False

    def expire(self, key: str, seconds: int) -> bool:
        client = self._ensure()
        if client is None:
            return False
        try:
            return bool(client.expire(self._namespaced(key), seconds))
        except RedisError as exc:
            logger.error("redis_expire_error", key=key, error=str(exc))
            return False

    def incr(self, key: str, amount: int = 1) -> Optional[int]:
        client = self._ensure()
        if client is None:
            return None
        try:
            return int(client.incr(self._namespaced(key), amount))
        except RedisError as exc:
            logger.error("redis_incr_error", key=key, error=str(exc))
            return None

    def mget(self, keys: Iterable[str]) -> List[Optional[str]]:
        client = self._ensure()
        if client is None:
            return []
        ks = list(keys)
        try:
            namespaced = [self._namespaced(k) for k in ks]
            return list(client.mget(namespaced))
        except RedisError as exc:
            logger.error("redis_mget_error", keys=ks, error=str(exc))
            return []

    # --- Search/scan ---
    def find(self, keyword: str, *, count: int = 100) -> List[str]:
        """Find keys containing the keyword using SCAN with MATCH *keyword*.

        Returns un-prefixed keys for convenience.
        """
        client = self._ensure()
        if client is None:
            return []
        pattern = f"*{keyword}*" if keyword else "*"
        full_pattern = self._namespaced(pattern) if self.key_prefix else pattern
        try:
            found: List[str] = []
            for key in client.scan_iter(full_pattern, count=count):
                if self.key_prefix and isinstance(key, str) and key.startswith(f"{self.key_prefix}:"):
                    found.append(key[len(self.key_prefix) + 1 :])
                else:
                    found.append(key if isinstance(key, str) else str(key))
            return found
        except RedisError as exc:
            logger.error("redis_find_error", keyword=keyword, error=str(exc))
            return []

    def keys(self, pattern: str, *, count: int = 100) -> List[str]:
        client = self._ensure()
        if client is None:
            return []
        full_pattern = self._namespaced(pattern) if self.key_prefix else pattern
        try:
            results: List[str] = []
            for key in client.scan_iter(full_pattern, count=count):
                if self.key_prefix and isinstance(key, str) and key.startswith(f"{self.key_prefix}:"):
                    results.append(key[len(self.key_prefix) + 1 :])
                else:
                    results.append(key if isinstance(key, str) else str(key))
            return results
        except RedisError as exc:
            logger.error("redis_keys_error", pattern=pattern, error=str(exc))
            return []

    # --- Health ---
    def ping(self) -> bool:
        client = self._ensure()
        if client is None:
            return False
        try:
            return bool(client.ping())
        except RedisError as exc:
            logger.error("redis_ping_error", error=str(exc))
            return False

    # --- Context helpers ---
    def pipeline(self):
        client = self._ensure()
        if client is None:
            raise RuntimeError("Redis is not initialized")
        return client.pipeline()


# Module-level singleton matching the pattern used by MQTT client
redis_client = RedisClient(
    url=settings.redis_url,
    decode_responses=True,
    key_prefix=settings.app_name,
)


def start() -> None:
    redis_client.initialize()


def stop() -> None:
    redis_client.close()


