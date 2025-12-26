import json
from typing import Optional, Dict

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.future import select


from app.security import verify_token
from app.db import async_session
from app.models import GameSession, GameSessionStatus, User

from app.dependencies import connection_manager, game_manager
from app.pydantic_models.game import Game
from app.utils import generate_game_id
from app.websocket_utils import (
    broadcast_lobby_state,
    broadcast_to_room,
    send_game_update,
    get_database_lobby_info
)

router = APIRouter()  # /games/SOLO/


async def get_current_user_ws(token: str) -> Optional[User]:
    """
    Validates the JWT token and returns the user object.
    """
    try:
        payload = verify_token(token)  # Your existing JWT decode function
        username = payload.get("sub")
        if not username:
            return None

        async with async_session() as session:
            result = await session.execute(select(User).where(User.username == username))
            user = result.scalar_one_or_none()
            return user
    except Exception as e:
        print(f"Auth Error: {e}")
        return None


@router.websocket("/ws")
async def websocket_endpoint(
        websocket: WebSocket,
        token: str = Query(...)
) -> None:
    """
    Authenticated WebSocket endpoint for SOLO game lobby and gameplay.
    """

    # Authenticate before accepting
    user = await get_current_user_ws(token)

    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    client_id = str(user.user_id)
    client_display_name = user.username

    # Accept Connection
    await connection_manager.connect(websocket, client_id, client_display_name)

    # Send Initial Lobby State
    initial_lobby_data = await get_database_lobby_info()
    await connection_manager.send_personal_message(json.dumps({
        "event": "lobby_update",
        "games": initial_lobby_data
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
                    max_players: int = extra.get("max_players", 10)
                    buy_in_fee: float = extra.get("buy_in", 1.00)

                    new_game_id: str = generate_game_id()
                    while game_manager.get_game(new_game_id):
                        new_game_id = generate_game_id()

                    game_manager.create_game(new_game_id, client_id, client_display_name)
                    current_game_id = new_game_id

                    async with async_session() as session:
                        try:
                            new_session = GameSession(
                                game_type_id= "SOLO",
                                room_code= new_game_id,
                                host_user_id= client_id,
                                status= GameSessionStatus.WAITING,
                                current_players= 1,
                                max_players= max_players,
                                buy_in_amount= buy_in_fee
                            )
                            session.add(new_session)
                            await session.commit()
                        except Exception as e:
                            await session.rollback()
                            print(f"DB Error creating game: {e}")

                    await broadcast_lobby_state()

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

                        if game_state is not None:
                            response = {
                                "event": "game_settings_saved",
                                "settings": game_state.game_settings.model_dump()
                            }
                            await broadcast_to_room(current_game_id, response)

                elif action == "join_game":
                    target_id: str = payload.get("game_id", "").upper()

                    if not target_id:
                        raise Exception("Invalid game ID.")

                    game_state: Optional[Game] = game_manager.join_game(target_id, client_id, client_display_name)
                    if game_state:
                        current_game_id = target_id

                        async with async_session() as session:
                            try:
                                result = await session.execute(
                                    select(GameSession).where(GameSession.room_code == target_id)
                                )
                                session_row = result.scalar_one_or_none()

                                if session_row:
                                    session_row.current_players += 1
                                    if session_row.current_players >= session_row.max_players:
                                        session_row.status = GameSessionStatus.IN_PROGRESS
                                    await session.commit()
                            except Exception as e:
                                await session.rollback()
                                print(f"DB Error joining game: {e}")

                        await broadcast_lobby_state()

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
                        await leave_lobby(current_game_id, client_id, client_display_name)
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

                        game_state: Optional[Game] = game_manager.process_turn(client_id, current_game_id, turn_action,
                                                                               card, advance_turn)
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
            await leave_lobby(current_game_id, user_left_id, client_display_name)


async def leave_lobby(current_game_id: str, client_id: str, client_display_name: str):
    game_manager.remove_player(current_game_id, client_id)

    async with async_session() as session:
        try:
            result = await session.execute(
                select(GameSession).where(GameSession.room_code == current_game_id)
            )
            session_row = result.scalar_one_or_none()

            if session_row:
                session_row.current_players -= 1
                if session_row.current_players <= 0:
                    session_row.status = GameSessionStatus.CANCELLED
                await session.commit()
        except Exception as e:
            print(f"DB Error leaving game: {e}")

    await broadcast_to_room(current_game_id, {
        "event": "player_left",
        "player_id": client_id,
        "player_name": client_display_name,
        "message": f"{client_display_name} left the game."
    })

    await broadcast_lobby_state()