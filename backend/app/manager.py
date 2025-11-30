from typing import List
from fastapi import WebSocket
import asyncio

class ConnectionManager:
    """Manage active WebSocket connections.

    - active_connections: list of connected WebSocket objects
    - connect: accept and store a websocket
    - disconnect: remove a websocket
    - broadcast: send a message to all connected clients
    """

    def __init__(self) -> None:
        self.active_connections: List[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and register a new websocket connection."""
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        """Unregister a websocket connection if present."""
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)

    async def broadcast(self, message: str) -> None:
        """Send a text message to all currently connected clients."""
        async with self._lock:
            connections = list(self.active_connections)

        for connection in connections:
            try:
                await connection.send_text(message)
            except Exception:
                # If sending fails, ensure the connection is removed
                try:
                    await self.disconnect(connection)
                except Exception:
                    pass

    async def broadcast_others(self, message: str, sender: WebSocket) -> None:
        """Send a message to all clients except the sender."""
        async with self._lock:
            connections = [c for c in self.active_connections if c is not sender]

        for connection in connections:
            try:
                await connection.send_text(message)
            except Exception:
                try:
                    await self.disconnect(connection)
                except Exception:
                    pass

