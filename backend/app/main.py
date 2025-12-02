import json
import random
import string
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from .connection_manager import ConnectionManager
from .game_manager import GameManager

app = FastAPI()
connection_manager = ConnectionManager()
game_manager = GameManager()


def generate_game_id(length=4):
    """
    Generate a random 4-letter room ID (e.g., 'ABCD')
    """

    return ''.join(random.choices(string.ascii_uppercase, k=length))


async def broadcast_lobby_state():
    """
    Sends the current list of available games to EVERYONE connected.
    Useful for updating the 'Join Game' screen for users not yet in a game.
    """

    lobby_data = game_manager.get_lobby_info()
    message = {
        "event": "lobby_update",
        "games": lobby_data
    }
    await connection_manager.broadcast(json.dumps(message))


async def broadcast_to_room(game_id: str, message: dict):
    """
    Helper to send a message ONLY to players in a specific room.
    """

    player_ids = game_manager.get_player_ids(game_id)
    json_msg = json.dumps(message)

    for player_id in player_ids:
        await connection_manager.send_personal_message(json_msg, player_id)


@app.get("/")
async def root():
    """
    Basic health check endpoint.
    """

    return {"message": "UNO WebSocket server is running."}


@app.websocket("/ws/{client_id}/{client_display_name}")
async def websocket_endpoint(websocket: WebSocket, client_id: str, client_display_name: str):
    """
    Main WebSocket endpoint. Handles all incoming messages from clients and handles game logic.
    """

    await connection_manager.connect(websocket, client_id, client_display_name)

    await connection_manager.send_personal_message(json.dumps({
        "event": "lobby_update",
        "games": game_manager.get_lobby_info()
    }), client_id)

    current_game_id = None

    try:
        await connection_manager.send_personal_message(json.dumps({
            "event": "system",
            "message": f"Welcome {client_display_name}. Connection Established."
        }), client_id)

        while True:
            data = await websocket.receive_text()

            try:
                payload = json.loads(data)
                action = payload.get("action")
                extra = payload.get("extra")

                if action == "status_check":
                    await broadcast_lobby_state()

                elif action == "create_game":
                    new_game_id = generate_game_id()
                    while game_manager.get_game(new_game_id):
                        new_game_id = generate_game_id()

                    game_manager.create_game(new_game_id, client_id, client_display_name)
                    current_game_id = new_game_id

                    game_state = game_manager.get_game(new_game_id)

                    response = {
                        "event": "game_created",
                        "game_id": new_game_id,
                        "creator": client_id,
                        "players": game_state["players"],
                        "player_names": game_state["player_names"],
                        "message": f"Room {new_game_id} created."
                    }
                    await broadcast_to_room(new_game_id, response)
                    await broadcast_lobby_state()

                elif action == "join_game":
                    target_id = payload.get("game_id", "").upper()

                    try:
                        game_state = game_manager.join_game(target_id, client_id, client_display_name)
                        current_game_id = target_id

                        response = {
                            "event": "player_joined",
                            "game_id": target_id,
                            "host_id": game_state["host_id"],
                            "players": game_state["players"],
                            "player_names": game_state["player_names"],
                            "new_player_id": client_id,
                            "new_player_name": client_display_name,
                            "message": f"{client_display_name} has joined the game!",
                            "player_states": game_state["player_states"]
                        }
                        await broadcast_to_room(target_id, response)
                        await broadcast_lobby_state()

                    except Exception as e:
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
                            "player_id": client_id,
                            "player_name": client_display_name,
                            "message": f"{client_display_name} left the game."
                        })

                        await broadcast_lobby_state()
                        current_game_id = None

                elif action == "start_game":
                    if current_game_id:
                        game_state = game_manager.start_game(current_game_id)
                        await send_game_update(game_state, current_game_id, "game_started")

                elif action == "end_game":
                    if current_game_id:
                        game_manager.end_game(current_game_id)

                elif action == "back_to_lobby":
                    if current_game_id:
                        game_state = game_manager.set_player_back_to_lobby(current_game_id, client_id)
                        await broadcast_to_room(current_game_id, {
                            "event": "player_back_to_lobby",
                            "player_states": game_state["player_states"]
                        })

                elif action == "process_turn":
                    if current_game_id:
                        turn_action: Optional[str] = extra.get("action") if extra else None
                        card: Optional[str] = extra.get("card") if extra else None
                        advance_turn: bool = extra.get("advance_turn", True)

                        game_state = game_manager.process_turn(client_id, current_game_id, turn_action, card,
                                                               advance_turn)
                        await send_game_update(game_state, current_game_id)

                else:
                    if current_game_id:
                        await broadcast_to_room(current_game_id, {
                            "event": "message",
                            "sender_id": client_id,
                            "sender_name": client_display_name,
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
        user_left_id = await connection_manager.disconnect(websocket)

        if current_game_id and user_left_id:
            game_manager.remove_player(current_game_id, user_left_id)

            await broadcast_to_room(current_game_id, {
                "event": "player_left",
                "player_id": user_left_id,
                "player_name": client_display_name,
                "message": f"{client_display_name} disconnected unexpectedly."
            })
            await broadcast_lobby_state()


async def send_game_update(game_state: dict, current_game_id: str, event: str = "game_update"):
    """
    Sends a game update to all players in the current game.
    """

    players = game_state["players"]
    player_cards = game_state["player_cards"]

    current_player_index = game_state["current_player_index"]
    current_player_id = players[current_player_index]

    for player_id in players:
        msg = {
            "event": event,
            "game_id": current_game_id,
            "current_active_color": game_state["current_active_color"],
            "direction": game_state["direction"],
            "top_card": game_state["discard_pile"][-1] if game_state["discard_pile"] else None,
            "current_player": current_player_id,
            "hand": player_cards.get(player_id, []),
            "card_counts": {
                other_player_id: len(player_cards[other_player_id])
                for other_player_id in players
                if other_player_id != player_id
            },
            "game_event": game_state["event"],
            "player_states": game_state["player_states"]
        }

        await connection_manager.send_personal_message(
            json.dumps(msg),
            player_id
        )
