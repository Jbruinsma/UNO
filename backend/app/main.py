import json
import random
import string
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from starlette.middleware.cors import CORSMiddleware

from .config import settings
from .connection_manager import ConnectionManager
from .db import engine, Base
from .game_manager import GameManager
from .pydantic_models.game import Game
from .pydantic_models.game_settings import GameSettings
from .pydantic_models.game_state import GameState



@asynccontextmanager
async def lifespan(app):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI()
connection_manager = ConnectionManager()
game_manager = GameManager()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from .routes.auth import router as auth_router
from .routes.dashboard import router as dashboard_router
from .routes.user import router as user_router
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
app.include_router(user_router, prefix="/users", tags=["user"])

@app.get("/health")
async def health() -> Dict[str, Any]:
    return { "status": "ok", "database": settings.DB_NAME }

def generate_game_id(length: int =4) -> str:
    """
    Generate a random 4-letter room ID (e.g., 'ABCD')
    """

    return ''.join(random.choices(string.ascii_uppercase, k=length))


async def broadcast_lobby_state() -> None:
    """
    Sends the current list of available games to EVERYONE connected.
    Useful for updating the 'Join Game' screen for users not yet in a game.
    """

    lobby_data: List[Dict] = game_manager.get_lobby_info()
    message = {
        "event": "lobby_update",
        "games": lobby_data
    }
    await connection_manager.broadcast(json.dumps(message))


async def broadcast_to_room(game_id: str, message: Dict) -> None:
    """
    Helper to send a message ONLY to players in a specific room.
    """

    player_ids = game_manager.get_player_ids(game_id)
    json_msg = json.dumps(message)

    for player_id in player_ids:
        await connection_manager.send_personal_message(json_msg, player_id)


@app.get("/")
async def root() -> Dict[str, str]:
    """
    Basic health check endpoint.
    """

    return {"message": "UNO WebSocket server is running."}


@app.websocket("/ws/{client_id}/{client_display_name}")
async def websocket_endpoint(websocket: WebSocket, client_id: str, client_display_name: str) -> None:
    """
    Main WebSocket endpoint. Handles all incoming messages from clients and handles game logic.
    """

    await connection_manager.connect(websocket, client_id, client_display_name)

    await connection_manager.send_personal_message(json.dumps({
        "event": "lobby_update",
        "games": game_manager.get_lobby_info()
    }), client_id)

    current_game_id: Optional[str] = None

    try:
        await connection_manager.send_personal_message(json.dumps({
            "event": "system",
            "message": f"Welcome {client_display_name}. Connection Established."
        }), client_id)

        while True:
            data = await websocket.receive_text()

            try:
                payload = json.loads(data)
                action: str = payload.get("action")
                extra: Dict = payload.get("extra")

                if action == "status_check":
                    await broadcast_lobby_state()

                elif action == "create_game":
                    new_game_id: str = generate_game_id()
                    while game_manager.get_game(new_game_id):
                        new_game_id = generate_game_id()

                    game_manager.create_game(new_game_id, client_id, client_display_name)
                    current_game_id = new_game_id

                    game_state: Optional[Game] = game_manager.get_game(new_game_id)
                    if not game_state:
                        raise Exception("Failed to retrieve game state after creation.")

                    response = {
                        "event": "game_created",
                        "game_id": new_game_id,
                        "creator": client_id,
                        "players": game_state.players,
                        "player_names": game_state.player_names,
                        "message": f"Room {new_game_id} created."
                    }
                    await broadcast_to_room(new_game_id, response)

                elif action == "save_game_settings":
                    if current_game_id:
                        settings: Dict = extra.get("settings")
                        game_state: Optional[Game] = game_manager.update_game_settings(current_game_id, settings)
                        print(game_state)
                        if game_state is not None:
                            response = {
                                "event": "game_settings_saved",
                                "settings": game_state.game_settings.model_dump()
                            }
                            await broadcast_to_room(current_game_id, response)
                            print("SETTINGS SENT")

                elif action == "join_game":
                    target_id: str = payload.get("game_id", "").upper()

                    if not target_id:
                        raise Exception("Invalid game ID.")

                    game_state: Optional[Game] = game_manager.join_game(target_id, client_id, client_display_name)
                    if game_state:
                        current_game_id = target_id

                        response = {
                            "event": "player_joined",
                            "game_id": target_id,
                            "host_id": game_state.host_id,
                            "players": game_state.players,
                            "player_names": game_state.player_names,
                            "new_player_id": client_id,
                            "new_player_name": client_display_name,
                            "message": f"{client_display_name} has joined the game!",
                            "player_states": game_state.player_states
                        }
                        await broadcast_to_room(target_id, response)

                elif action == "leave_game":
                    if current_game_id:
                        game_manager.remove_player(current_game_id, client_id)

                        await broadcast_to_room(current_game_id, {
                            "event": "player_left",
                            "player_id": client_id,
                            "player_name": client_display_name,
                            "message": f"{client_display_name} left the game."
                        })
                        current_game_id = None

                elif action == "start_game":
                    if current_game_id:
                        game_state: Optional[Game] = game_manager.start_game(current_game_id)
                        if game_state:
                            await send_game_update(game_state, current_game_id, "game_started")

                elif action == "end_game":
                    if current_game_id:
                        game_manager.end_game(current_game_id)

                elif action == "back_to_lobby":
                    if current_game_id:
                        game_state: Optional[Game] = game_manager.set_player_back_to_lobby(current_game_id, client_id)
                        if game_state:
                            await broadcast_to_room(current_game_id, {
                                "event": "player_back_to_lobby",
                                "player_states": game_state.player_states
                            })

                elif action == "process_turn":
                    if current_game_id:
                        turn_action: Optional[str] = extra.get("action") if extra else None
                        card: Optional[str] = extra.get("card") if extra else None
                        advance_turn: bool = extra.get("advance_turn", True)

                        game_state: Optional[Game] = game_manager.process_turn(client_id, current_game_id, turn_action, card, advance_turn)
                        if game_state:
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
            except Exception as e:
                await connection_manager.send_personal_message(json.dumps({
                    "event": "error",
                    "message": str(e)
                }), client_id)

    except WebSocketDisconnect:
        user_left_id: Optional[str] = await connection_manager.disconnect(websocket)

        if current_game_id and user_left_id:
            game_manager.remove_player(current_game_id, user_left_id)

            await broadcast_to_room(current_game_id, {
                "event": "player_left",
                "player_id": user_left_id,
                "player_name": client_display_name,
                "message": f"{client_display_name} disconnected unexpectedly."
            })


async def send_game_update(game_state: Game, current_game_id: str, event: str = "game_update") -> None:
    """
    Sends a game update to all players in the current game.
    """

    players: List[str] = game_state.players
    player_cards: Dict[str, List[str]] = game_state.player_cards

    assert game_state.current_player_index is not None
    current_player_index: int = game_state.current_player_index
    current_player_id: str = players[current_player_index]

    for player_id in players:
        game_update_json = GameState(
            event=event,
            game_id=current_game_id,
            current_active_color=game_state.current_active_color,
            direction=game_state.direction,
            top_card=game_state.discard_pile[-1] if game_state.discard_pile else None,
            current_player=current_player_id,
            hand=player_cards.get(player_id, []),
            card_counts={
                other_player_id: len(player_cards[other_player_id])
                for other_player_id in players
                if other_player_id != player_id
            },
            game_event=game_state.event,
            player_states=game_state.player_states
        )

        await connection_manager.send_personal_message(
            game_update_json.model_dump_json(),
            player_id
        )
