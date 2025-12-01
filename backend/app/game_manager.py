import random
from typing import Dict, List, Optional

from backend.app.utils import create_deck, SPECIAL_CARDS, WILD_CARDS


class GameManager:
    """
    Manages the Game Logic and Room State.
    Does NOT know about WebSockets. Only knows about User IDs.
    """

    def __init__(self):
        # Key: game_id, Value: Dict containing game state
        self.games: Dict[str, Dict] = {}

    def create_game(self, game_id: str, host_id: str, host_name: str):
        if game_id in self.games:
            raise Exception("Game ID collision. Try again.")

        self.games[game_id] = {
            "host_id": host_id,
            "state": "waiting",
            "players": [host_id],
            "player_names": {
                host_id: host_name
            },
            "current_player_index": None,
            "direction": 1,          # 1 = clockwise, -1 = counterclockwise

            "deck": [],
            "discard_pile": [],
            "player_cards": {}
        }
        return self.games[game_id]

    def advance_turn(self, game_id: str):
        game = self.games.get(game_id)
        if not game:
            raise Exception("Game does not exist.")

        is_clockwise = game["direction"] == 1

        current_player_index = game["current_player_index"]
        players = game["players"]
        player_count = len(players)

        if is_clockwise:
            game["current_player_index"] = 0 if current_player_index == player_count - 1 else current_player_index + 1
        else:
            game["current_player_index"] = player_count - 1 if current_player_index == 0 else current_player_index - 1

    def reverse_direction(self, game_id: str):
        game = self.games.get(game_id)
        if not game:
            raise Exception("Game does not exist.")

        game["direction"] *= -1

    def join_game(self, game_id: str, user_id: str, user_name: str):
        game = self.games.get(game_id)
        if not game:
            raise Exception("Game does not exist.")

        if game["state"] != "waiting":
            raise Exception("Game has already started.")

        if user_id in game["players"]:
            return game

        game["players"].append(user_id)
        game["player_names"][user_id] = user_name
        game["player_cards"][user_id] = []
        return game

    def get_game(self, game_id: str):
        return self.games.get(game_id)

    def get_player_ids(self, game_id: str) -> List[str]:
        """Helper to get all user_ids in a room."""
        game = self.games.get(game_id)
        return game["players"] if game else []

    def remove_player(self, game_id: str, user_id: str):
        """Handle player leaving a room."""
        if game_id in self.games:
            game = self.games[game_id]

            # Remove name mapping
            if "player_names" in game and user_id in game["player_names"]:
                del game["player_names"][user_id]

            # Remove from logic list
            if user_id in game["players"]:
                if user_id == game["host_id"]:
                    game["host_id"] = game["players"][1] if len(game["players"]) > 1 else None
                game["players"].remove(user_id)

            if len(game["players"]) == 0:
                del self.games[game_id]

    def start_game(self, game_id: str):
        game = self.games.get(game_id)
        if not game:
            raise Exception("Game does not exist.")

        player_ids = game["players"]

        if len(player_ids) < 2:
            raise Exception("Not enough players to start game.")

        game["state"] = "playing"
        game["deck"] = create_deck()

        for player_id in player_ids:
            game["player_cards"][player_id] = []

            for _ in range(7):
                if len(game["deck"]) > 0:
                    card = game["deck"].pop()
                    game["player_cards"][player_id].append(card)

        if len(game["deck"]) > 0:
            first_card = game["deck"].pop()
            game["discard_pile"].append(first_card)

        start_index = random.randint(0, len(player_ids) - 1)
        game["current_player_index"] = start_index

        return game

    def process_turn(self, player_id: str, game_id: str, action: Optional[str], card: Optional[str] = None):
        game = self.games.get(game_id)
        if not game:
            raise Exception("Game does not exist.")

        players = game["players"]

        if not action: return game

        if action == "draw_card_from_middle":
            current_player_id = players[game["current_player_index"]]
            if current_player_id != player_id: return game

            selected_card = game["deck"].pop()
            game["player_cards"][current_player_id].append(selected_card)

            self.advance_turn(game_id)
            return game

        elif action == "play_card":
            current_player_id = players[game["current_player_index"]]
            if current_player_id != player_id or card is None: return game

            is_special_card = card in SPECIAL_CARDS
            is_wild_card = card in WILD_CARDS

            card_color = card[0]
            card_value = card[-1]

            top_card = game["discard_pile"][-1]
            top_card_color = top_card[0]
            top_card_value = top_card[-1]

            # Validate card color or number to prevent frontend manipulation cheating
            if is_wild_card or (is_special_card and top_card_color == card_color) or (not is_special_card and (top_card_value == card_value or top_card_color == card_color)):
                game["discard_pile"].append(card)
                game["player_cards"][current_player_id].remove(card)

                if is_special_card:
                    if card == 'S':
                        # Special card: Skip
                        print("Skipping turn...")
                        for i in range(2): self.advance_turn(game_id)
                    elif card == 'R':
                        print("Reversing direction...")
                        # Special card: Reverse
                        self.reverse_direction(game_id)
                    elif card == 'D2':
                        # Special card: Draw 2
                        pass
                elif is_wild_card:
                    if card == 'W-Wild':
                        # Wild card: Pick a new color
                        pass
                    elif card == 'W-W4':
                        # Wild card: Pick a new color and draw 4
                        pass

                self.advance_turn(game_id)
            return game
