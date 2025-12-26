import json
from typing import List, Dict

from app.dependencies import game_manager, connection_manager
from app.pydantic_models.game import Game
from app.pydantic_models.game_state import GameState

from sqlalchemy.future import select
from sqlalchemy.orm import selectinload


from app.db import async_session
from app.models import GameSession, GameSessionStatus

async def get_database_lobby_info():
    """
    Async query to fetch WAITING games from the DB.
    Uses selectinload to fetch the host user data efficiently.
    """
    async with async_session() as session:
        # Fetch games with status WAITING and eager load the host relationship
        query = (
            select(GameSession)
            .options(selectinload(GameSession.host))
            .where(GameSession.status == GameSessionStatus.WAITING)
        )
        result = await session.execute(query)
        active_sessions = result.scalars().all()

        return [
            {
                "game_id": s.room_code,
                # specific safe check in case host is somehow None
                "host_name": s.host.username if s.host else "Unknown",
                "player_count": s.current_players,
                "max_players": s.max_players,
                "buy_in": float(s.buy_in_amount),
                "is_active": True
            }
            for s in active_sessions
        ]


async def broadcast_lobby_state() -> None:
    """
    Sends the current list of available games to EVERYONE connected.
    Useful for updating the 'Join Game' screen for users not yet in a game.
    """

    lobby_data = await get_database_lobby_info()

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
