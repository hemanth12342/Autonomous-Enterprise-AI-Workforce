"""
WebSocket API — real-time event streaming to the dashboard.
"""
import json
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.memory.short_term import get_redis

router = APIRouter()


class ConnectionManager:
    """Manages active WebSocket connections."""

    def __init__(self):
        self.active: dict[str, list[WebSocket]] = {}  # project_id → [connections]
        self.global_connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket, project_id: str | None = None) -> None:
        await ws.accept()
        if project_id:
            self.active.setdefault(project_id, []).append(ws)
        else:
            self.global_connections.append(ws)

    def disconnect(self, ws: WebSocket, project_id: str | None = None) -> None:
        if project_id and project_id in self.active:
            self.active[project_id] = [c for c in self.active[project_id] if c != ws]
        elif ws in self.global_connections:
            self.global_connections.remove(ws)

    async def broadcast_to_project(self, project_id: str, message: dict) -> None:
        conns = self.active.get(project_id, [])
        dead = []
        for ws in conns:
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                dead.append(ws)
        for ws in dead:
            conns.remove(ws)

    async def broadcast_global(self, message: dict) -> None:
        dead = []
        for ws in self.global_connections:
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.global_connections.remove(ws)


manager = ConnectionManager()


@router.websocket("/project/{project_id}")
async def project_websocket(ws: WebSocket, project_id: str):
    """WebSocket endpoint for project-specific real-time events."""
    await manager.connect(ws, project_id)
    try:
        # Subscribe to Redis pub/sub channel
        redis = get_redis()
        pubsub = redis.pubsub()
        await pubsub.subscribe(f"project:{project_id}:events")

        # Send connection ack
        await ws.send_text(json.dumps({
            "event_type": "connected",
            "project_id": project_id,
            "message": "Connected to AI Workforce event stream",
        }))

        # Listen for events
        while True:
            try:
                message = await asyncio.wait_for(pubsub.get_message(ignore_subscribe_messages=True), timeout=1.0)
                if message and message["type"] == "message":
                    data = json.loads(message["data"])
                    await ws.send_text(json.dumps(data))
            except asyncio.TimeoutError:
                # Send keepalive ping
                await ws.send_text(json.dumps({"event_type": "ping"}))
            except WebSocketDisconnect:
                break

    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(ws, project_id)
        await pubsub.unsubscribe(f"project:{project_id}:events")


@router.websocket("/global")
async def global_websocket(ws: WebSocket):
    """WebSocket endpoint for global events (all projects)."""
    await manager.connect(ws, None)
    try:
        redis = get_redis()
        pubsub = redis.pubsub()
        await pubsub.subscribe("global:events")

        await ws.send_text(json.dumps({
            "event_type": "connected",
            "message": "Connected to global AI Workforce event stream",
        }))

        while True:
            try:
                message = await asyncio.wait_for(pubsub.get_message(ignore_subscribe_messages=True), timeout=1.0)
                if message and message["type"] == "message":
                    data = json.loads(message["data"])
                    await ws.send_text(json.dumps(data))
            except asyncio.TimeoutError:
                await ws.send_text(json.dumps({"event_type": "ping"}))
            except WebSocketDisconnect:
                break

    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(ws, None)
