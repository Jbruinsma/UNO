from typing import Dict, List
from fastapi import WebSocket
import asyncio


class ConnectionManager:
    """Manage active WebSocket connections."""

    def __init__(self) -> None:
        self.active_connections: Dict[WebSocket, str] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, user: str) -> None:
        """Accept and register a new websocket connection."""
        await websocket.accept()

        async with self._lock:
            for ws, connected_user in list(self.active_connections.items()):
                if connected_user == user:
                    await ws.close(code=1000, reason="Duplicate login")
                    if ws in self.active_connections:
                        del self.active_connections[ws]

            # Register the new connection
            self.active_connections[websocket] = user

    async def disconnect(self, websocket: WebSocket) -> None:
        """Unregister a websocket connection if present."""
        async with self._lock:
            if websocket in self.active_connections:
                del self.active_connections[websocket]

    async def broadcast(self, message: str) -> None:
        """Send a text message to all currently connected clients."""
        async with self._lock:
            active_websockets = list(self.active_connections.keys())

        for ws in active_websockets:
            try:
                await ws.send_text(message)
            except Exception:
                await self.disconnect(ws)

    async def broadcast_others(self, message: str, sender: WebSocket) -> None:
        """Send a message to all clients except the sender."""
        async with self._lock:
            targets = [ws for ws in self.active_connections.keys() if ws != sender]

        for ws in targets:
            try:
                await ws.send_text(message)
            except Exception:
                await self.disconnect(ws)
