from typing import Dict, List
from fastapi import WebSocket
import asyncio


class ConnectionManager:
    """
    Manages the raw WebSocket connections.
    Acts as the 'Phone Book' mapping User IDs to WebSockets.
    """

    def __init__(self) -> None:
        # Map WebSocket -> User ID (For handling disconnects)
        self.active_connections: Dict[WebSocket, str] = {}

        # Map User ID -> WebSocket (For sending messages to specific people)
        self.user_connections: Dict[str, WebSocket] = {}

        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, user_id: str) -> None:
        await websocket.accept()
        async with self._lock:
            if user_id in self.user_connections:
                old_ws = self.user_connections[user_id]
                try:
                    await old_ws.close(code=1000, reason="Logged in elsewhere")
                    if old_ws in self.active_connections:
                        del self.active_connections[old_ws]
                except Exception:
                    pass

            self.active_connections[websocket] = user_id
            self.user_connections[user_id] = websocket

    async def disconnect(self, websocket: WebSocket) -> str | None:
        """Removes the connection and returns the user_id that left."""
        async with self._lock:
            user_id = self.active_connections.get(websocket)
            if user_id:
                del self.active_connections[websocket]
                if user_id in self.user_connections:
                    del self.user_connections[user_id]
            return user_id

    async def send_personal_message(self, message: str, user_id: str):
        """Send a message to a specific user by ID."""
        if user_id in self.user_connections:
            websocket = self.user_connections[user_id]
            try:
                await websocket.send_text(message)
            except Exception:
                await self.disconnect(websocket)

    async def broadcast(self, message: str) -> None:
        """Send to EVERYONE connected (Global Lobby Chat)."""
        async with self._lock:
            sockets = list(self.active_connections.keys())

        for ws in sockets:
            try:
                await ws.send_text(message)
            except Exception:
                await self.disconnect(ws)
