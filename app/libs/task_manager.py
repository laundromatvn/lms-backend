import json
import threading
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Protocol, runtime_checkable

from app.core.logging import logger


TaskDict = Dict[str, Any]


ALLOWED_STATUS = {
    "new",
    "in_progress",
    "finished",
    "failed",
}

TIMEOUT = 3600 * 24 # 1 day


@runtime_checkable
class TaskStorage(Protocol):
    def create(self, task: TaskDict, timeout: int = TIMEOUT) -> None: ...

    def get(self, task_id: str) -> Optional[TaskDict]: ...

    def update(self, task_id: str, updates: TaskDict) -> Optional[TaskDict]: ...

    def delete(self, task_id: str) -> bool: ...


class InMemoryTaskStorage:
    def __init__(self) -> None:
        self._tasks: Dict[str, TaskDict] = {}
        self._lock = threading.Lock()

    def create(self, task: TaskDict, timeout: int = TIMEOUT) -> None:
        with self._lock:
            # store task alongside its expiry timestamp
            expires_at: Optional[datetime] = None
            if timeout and timeout > 0:
                expires_at = datetime.now(timezone.utc).timestamp() + timeout
            stored = dict(task)
            stored["_expires_at_ts"] = expires_at
            self._tasks[task["id"]] = stored

    def get(self, task_id: str) -> Optional[TaskDict]:
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return None
            # check expiry
            expires_at = task.get("_expires_at_ts")
            if isinstance(expires_at, (int, float)):
                if datetime.now(timezone.utc).timestamp() > float(expires_at):
                    # expired, delete and return None
                    self._tasks.pop(task_id, None)
                    return None
            # Return a shallow copy to avoid external mutation
            copied = dict(task)
            copied.pop("_expires_at_ts", None)
            return copied

    def update(self, task_id: str, updates: TaskDict) -> Optional[TaskDict]:
        with self._lock:
            existing = self._tasks.get(task_id)
            if existing is None:
                return None
            # handle potential expiry on update fetch
            expires_at = existing.get("_expires_at_ts")
            if isinstance(expires_at, (int, float)) and datetime.now(timezone.utc).timestamp() > float(expires_at):
                self._tasks.pop(task_id, None)
                return None
            # Merge updates into existing task
            new_task = dict(existing)
            if "data" in updates and isinstance(updates["data"], dict):
                merged_data = dict(existing.get("data") or {})
                merged_data.update(updates["data"])  # shallow merge
                new_task["data"] = merged_data
                updates = dict(updates)
                updates.pop("data", None)
            new_task.update(updates)
            # refresh expiry to default timeout on update
            new_task["_expires_at_ts"] = datetime.now(timezone.utc).timestamp() + TIMEOUT
            self._tasks[task_id] = new_task
            result = dict(new_task)
            result.pop("_expires_at_ts", None)
            return result

    def delete(self, task_id: str) -> bool:
        with self._lock:
            return self._tasks.pop(task_id, None) is not None


class RedisTaskStorage:
    def __init__(self, *, prefix: str = "task") -> None:
        # Lazy import to avoid hard dependency when Redis isn't configured
        from app.libs.redis import redis_client

        self._redis = redis_client
        self._prefix = prefix

    def _key(self, task_id: str) -> str:
        return f"{self._prefix}:{task_id}"

    def _serialize(self, task: TaskDict) -> str:
        payload = dict(task)
        for ts_field in ("created_at", "updated_at"):
            value = payload.get(ts_field)
            if isinstance(value, datetime):
                payload[ts_field] = value.astimezone(timezone.utc).isoformat()
        return json.dumps(payload)

    def _deserialize(self, raw: Optional[str]) -> Optional[TaskDict]:
        if not raw:
            return None
        try:
            data = json.loads(raw)
        except Exception:
            return None
        for ts_field in ("created_at", "updated_at"):
            value = data.get(ts_field)
            if isinstance(value, str):
                try:
                    data[ts_field] = datetime.fromisoformat(value)
                except Exception:
                    pass
        return data

    def create(self, task: TaskDict, timeout: int = TIMEOUT) -> None:
        key = self._key(task["id"])
        payload = self._serialize(task)
        # set with expiration
        ok = self._redis.set(key, payload, ex=timeout)
        if not ok:
            logger.warning("task_redis_create_failed", task_id=task["id"])

    def get(self, task_id: str) -> Optional[TaskDict]:
        key = self._key(task_id)
        logger.info("task_redis_get", key=key)
        raw = self._redis.get(key)
        return self._deserialize(raw)

    def update(self, task_id: str, updates: TaskDict) -> Optional[TaskDict]:
        key = self._key(task_id)
        existing = self.get(task_id)
        if existing is None:
            return None
        new_task = dict(existing)
        if "data" in updates and isinstance(updates["data"], dict):
            merged_data = dict(existing.get("data") or {})
            merged_data.update(updates["data"])  # shallow merge
            new_task["data"] = merged_data
            updates = dict(updates)
            updates.pop("data", None)
        new_task.update(updates)
        # update value and refresh TTL
        ok = self._redis.set(key, self._serialize(new_task), ex=TIMEOUT)
        if not ok:
            logger.warning("task_redis_update_failed", task_id=task_id)
        return new_task

    def delete(self, task_id: str) -> bool:
        key = self._key(task_id)
        return self._redis.delete(key) > 0


class TaskManager:
    def __init__(self, storage: TaskStorage) -> None:
        self._storage = storage

    def set_storage(self, storage: TaskStorage) -> None:
        self._storage = storage

    def create(self, data: Dict[str, Any] = None) -> TaskDict:
        now = datetime.now(timezone.utc)
        task: TaskDict = {
            "id": uuid.uuid4().hex,
            "created_at": now,
            "updated_at": now,
            "status": "new",
            "data": dict(data or {}),
        }
        self._storage.create(task)
        return task

    def get(self, task_id: str) -> Optional[TaskDict]:
        return self._storage.get(task_id)

    def update(
        self,
        task_id: str,
        *,
        status: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Optional[TaskDict]:
        updates: TaskDict = {"updated_at": datetime.now(timezone.utc)}
        if status is not None:
            if status not in ALLOWED_STATUS:
                raise ValueError(f"Invalid status: {status}. Allowed: {sorted(ALLOWED_STATUS)}")
            updates["status"] = status
        if data is not None:
            updates["data"] = dict(data)
        return self._storage.update(task_id, updates)

    def delete(self, task_id: str) -> bool:
        return self._storage.delete(task_id)


def _select_default_storage() -> TaskStorage:
    # Prefer Redis if usable; fall back to in-memory
    try:
        from app.libs.redis import redis_client

        if redis_client.ping():
            logger.info("task_storage_redis_enabled")
            return RedisTaskStorage(prefix="task")
    except Exception:
        pass
    logger.info("task_storage_memory_enabled")
    return InMemoryTaskStorage()


task_manager = TaskManager(storage=_select_default_storage())
