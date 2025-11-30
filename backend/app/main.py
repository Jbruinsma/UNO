from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from .manager import ConnectionManager

app = FastAPI()
manager = ConnectionManager()


@app.get("/")
async def root():
    return {"message": "UNO WebSocket server is running."}


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint that receives messages from a client and broadcasts them to other clients."""
    await manager.connect(websocket)
    try:
        # Optionally notify others that a client joined
        await manager.broadcast(f"Client {client_id} joined")
        while True:
            data = await websocket.receive_text()
            message = f"{client_id}: {data}"
            # Broadcast to all other connected clients
            await manager.broadcast_others(message, websocket)
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
        await manager.broadcast(f"Client {client_id} left")

