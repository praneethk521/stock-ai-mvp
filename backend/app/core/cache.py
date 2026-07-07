import hashlib
import json
from typing import Any

import redis
import structlog


logger = structlog.get_logger(__name__)


class JsonCache:
    def __init__(self, redis_url: str, namespace: str = 'stock-ai') -> None:
        self.namespace = namespace
        self.client = redis.Redis.from_url(redis_url, socket_connect_timeout=1, socket_timeout=1)

    def get(self, key: str) -> dict[str, Any] | None:
        try:
            value = self.client.get(self._key(key))
        except redis.RedisError as exc:
            logger.warning('cache_get_failed', error=str(exc))
            return None
        if not value:
            return None
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            logger.warning('cache_decode_failed')
            return None

    def set(self, key: str, value: dict[str, Any], ttl_seconds: int) -> None:
        if ttl_seconds <= 0:
            return
        try:
            self.client.setex(self._key(key), ttl_seconds, json.dumps(value))
        except (TypeError, redis.RedisError) as exc:
            logger.warning('cache_set_failed', error=str(exc))

    def ping(self) -> bool:
        try:
            return bool(self.client.ping())
        except redis.RedisError:
            return False

    def _key(self, key: str) -> str:
        digest = hashlib.sha256(key.encode('utf-8')).hexdigest()
        return f'{self.namespace}:provider:{digest}'
