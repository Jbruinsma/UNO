from typing import Optional, List, Dict

from pydantic import BaseModel


class GameState(BaseModel):
    """
    Formats data for the frontend
    """

    event: Optional[str] = None
    game_id: Optional[str] = None
    current_active_color: Optional[str] = None
    direction: int = 1
    top_card: Optional[str] = None
    current_player: Optional[str] = None
    hand: List[str] = []
    card_counts: Dict[str, int] = {}
    game_event: Optional[Dict[str, Optional[str]]] = None
    player_states: Dict[str, str] = {}
