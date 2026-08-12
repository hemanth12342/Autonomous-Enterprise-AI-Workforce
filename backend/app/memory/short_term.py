"""
Redis short-term memory — agent state, task queues, caching, pub/sub.
"""
import json
from typing import Any, Optional
import redis.asyncio as aioredis
from app.config import settings

_redis: Optional[aioredis.Redis] = None


async def init_redis() -> None:
    global _redis
    _redis = aioredis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
        max_connections=20,
    )
    await _redis.ping()


async def close_redis() -> None:
    if _redis:
        await _redis.close()


def get_redis() -> aioredis.Redis:
    if _redis is None:
        raise RuntimeError("Redis not initialized. Call init_redis() first.")
    return _redis


# ─── Agent State ──────────────────────────────────────────────────────────────
async def set_agent_state(agent_type: str, project_id: str, state: dict, ttl: int = 3600) -> None:
    key = f"agent_state:{agent_type}:{project_id}"
    await get_redis().setex(key, ttl, json.dumps(state))


async def get_agent_state(agent_type: str, project_id: str) -> Optional[dict]:
    key = f"agent_state:{agent_type}:{project_id}"
    data = await get_redis().get(key)
    return json.loads(data) if data else None


async def delete_agent_state(agent_type: str, project_id: str) -> None:
    key = f"agent_state:{agent_type}:{project_id}"
    await get_redis().delete(key)


# ─── Task Queue ───────────────────────────────────────────────────────────────
async def enqueue_task(queue_name: str, task_data: dict) -> None:
    await get_redis().lpush(f"queue:{queue_name}", json.dumps(task_data))


async def dequeue_task(queue_name: str, timeout: int = 5) -> Optional[dict]:
    result = await get_redis().brpop(f"queue:{queue_name}", timeout=timeout)
    if result:
        _, data = result
        return json.loads(data)
    return None


# ─── Caching ──────────────────────────────────────────────────────────────────
async def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    await get_redis().setex(f"cache:{key}", ttl, json.dumps(value))


async def cache_get(key: str) -> Optional[Any]:
    data = await get_redis().get(f"cache:{key}")
    return json.loads(data) if data else None


async def cache_delete(key: str) -> None:
    await get_redis().delete(f"cache:{key}")


# ─── Distributed Locks ────────────────────────────────────────────────────────
async def acquire_lock(resource: str, ttl: int = 30) -> bool:
    result = await get_redis().set(f"lock:{resource}", "1", nx=True, ex=ttl)
    return result is True


async def release_lock(resource: str) -> None:
    await get_redis().delete(f"lock:{resource}")


# ─── Rate Limiting ────────────────────────────────────────────────────────────
async def check_rate_limit(identifier: str, limit: int, window: int) -> tuple[bool, int]:
    """Returns (is_allowed, remaining_requests)."""
    key = f"rate_limit:{identifier}"
    pipe = get_redis().pipeline()
    await pipe.incr(key)
    await pipe.expire(key, window)
    results = await pipe.execute()
    current = results[0]
    remaining = max(0, limit - current)
    return current <= limit, remaining


# ─── Real-time Events (Pub/Sub) ───────────────────────────────────────────────
async def publish_event(channel: str, event: dict) -> None:
    await get_redis().publish(channel, json.dumps(event))


async def get_project_channel(project_id: str) -> str:
    return f"project:{project_id}:events"


async def get_global_channel() -> str:
    return "global:events"


# ─── Session Storage ──────────────────────────────────────────────────────────
async def store_session(session_id: str, data: dict, ttl: int = 3600) -> None:
    await get_redis().setex(f"session:{session_id}", ttl, json.dumps(data))


async def get_session(session_id: str) -> Optional[dict]:
    data = await get_redis().get(f"session:{session_id}")
    return json.loads(data) if data else None


async def delete_session(session_id: str) -> None:
    await get_redis().delete(f"session:{session_id}")
