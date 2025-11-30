import json
import random
import string
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from .connection_manager import ConnectionManager
from .game_manager import GameManager

app = FastAPI()
connection_manager = ConnectionManager()
game_manager = GameManager()


def generate_game_id(length=4):
    """Generate a random 4-letter room ID (e.g., 'ABCD')"""
    return ''.join(random.choices(string.ascii_uppercase, k=length))


async def broadcast_to_room(game_id: str, message: dict):
    """
    Helper to send a message ONLY to players in a specific room.
    1. Gets player IDs from GameManager.
    2. Sends message via ConnectionManager.
    """
    player_ids = game_manager.get_player_ids(game_id)
    json_msg = json.dumps(message)

    for player_id in player_ids:
        await connection_manager.send_personal_message(json_msg, player_id)


@app.get("/")
async def root():
    return {"message": "UNO WebSocket server is running."}


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    Handles the WebSocket connection.
    1. Connects the user.
    2. Listens for JSON messages.
    3. Routes actions (create_game, join_game, leave_game, chat).
    """
    await connection_manager.connect(websocket, client_id)

    # Track which game this user is currently in so we can handle disconnects
    current_game_id = None

    try:
        # Send a welcome message to the connecting user
        await connection_manager.send_personal_message(json.dumps({
            "event": "system",
            "message": f"Welcome {client_id}. Connection Established."
        }), client_id)

        while True:
            # 1. Wait for incoming text
            data = await websocket.receive_text()

            try:
                # 2. Parse JSON
                payload = json.loads(data)
                action = payload.get("action")

                # --- ACTION HANDLERS ---

                if action == "create_game":
                    # Generate a unique ID
                    new_game_id = generate_game_id()
                    # Retry if ID collision happens
                    while game_manager.get_game(new_game_id):
                        new_game_id = generate_game_id()

                    # Create the game in the logic manager
                    # NOTE: This calls create_game, NOT add_game
                    game_manager.create_game(new_game_id, client_id)
                    current_game_id = new_game_id

                    response = {
                        "event": "game_created",
                        "game_id": new_game_id,
                        "creator": client_id,
                        "players": [client_id],
                        "message": f"Room {new_game_id} created."
                    }
                    # Notify the room (currently just the creator)
                    await broadcast_to_room(new_game_id, response)

                elif action == "join_game":
                    target_id = payload.get("game_id", "").upper()

                    try:
                        # Attempt to join via GameManager
                        game_state = game_manager.join_game(target_id, client_id)
                        current_game_id = target_id

                        # Notify everyone in that room
                        response = {
                            "event": "player_joined",
                            "game_id": target_id,
                            "players": game_state["players"],
                            "new_player": client_id,
                            "message": f"{client_id} has joined the game!"
                        }
                        await broadcast_to_room(target_id, response)

                    except Exception as e:
                        # Send error ONLY to the user who failed to join
                        error_response = {
                            "event": "error",
                            "message": str(e)
                        }
                        await connection_manager.send_personal_message(json.dumps(error_response), client_id)

                elif action == "leave_game":
                    if current_game_id:
                        game_manager.remove_player(current_game_id, client_id)
                        await broadcast_to_room(current_game_id, {
                            "event": "player_left",
                            "player": client_id,
                            "message": f"{client_id} left the game."
                        })
                        current_game_id = None

                else:
                    # Chat / Debug Fallback
                    # If in a game, broadcast to room. If not, echo back.
                    if current_game_id:
                        await broadcast_to_room(current_game_id, {
                            "event": "message",
                            "sender": client_id,
                            "text": str(payload)
                        })
                    else:
                        await connection_manager.send_personal_message(json.dumps({
                            "event": "echo",
                            "text": "You are not in a game yet."
                        }), client_id)

            except json.JSONDecodeError:
                pass

    except WebSocketDisconnect:
        # Handle unexpected disconnect (closing tab)
        user_left = await connection_manager.disconnect(websocket)

        # If they were in a game, remove them from game logic too
        if current_game_id and user_left:
            game_manager.remove_player(current_game_id, user_left)
            await broadcast_to_room(current_game_id, {
                "event": "player_left",
                "player": user_left,
                "message": f"{user_left} disconnected unexpectedly."
            })