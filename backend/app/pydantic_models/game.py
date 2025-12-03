from typing import List, Dict, Optional

from pydantic import BaseModel


class Game(BaseModel):
    host_id: str
    state: str
    players: List[str]
    player_names: Dict[str, str]
    player_states: Dict[str, str]
    current_player_index: Optional[int] = None
    current_active_color: Optional[str] = None
    direction: int
    event: Optional[Dict[str, Optional[str]]] = None
    deck: List[str] = []
    discard_pile: List[str] = []
    player_cards: Dict[str, List[str]] = {}
