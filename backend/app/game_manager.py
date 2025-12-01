import random
from typing import Dict, List, Optional

from pygments.lexers import q

from backend.app.utils import create_deck, SPECIAL_CARDS, WILD_CARDS, advance_turn_counter, retrieve_card_info, \
    REGULAR_CARDS


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
            "current_active_color": None,
            "direction": 1,          # 1 = clockwise, -1 = counterclockwise
            "event": None,
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

        game["current_player_index"] = advance_turn_counter(current_player_index, player_count, is_clockwise)

    def reverse_direction(self, game_id: str):
        game = self.games.get(game_id)
        if not game:
            raise Exception("Game does not exist.")

        game["direction"] *= -1

    def use_wild_card(self, color: Optional[str], game_id: str):
        game = self.games.get(game_id)
        if not game:
            raise Exception("Game does not exist.")

        if color is None:
            self.advance_turn(game_id)
            return game

        new_color, _ = retrieve_card_info(color)
        if new_color not in REGULAR_CARDS:
            self.advance_turn(game_id)
            return game

        game["current_active_color"] = new_color
        self.advance_turn(game_id)
        return game

    def set_event(self, game_id: str, event_type: str, player_id: Optional[str], affected_player_id: Optional[str] = None):
        game = self.games.get(game_id)
        if not game:
            raise Exception("Game does not exist.")

        game["event"] = {"type": event_type, "player_id": player_id, "affected_player_id": affected_player_id}

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
            first_card_color, first_card_value = retrieve_card_info(first_card)
            game["discard_pile"].append(first_card)
            game["current_active_color"] = first_card_color

        start_index = random.randint(0, len(player_ids) - 1)
        game["current_player_index"] = start_index

        return game

    def process_turn(self, player_id: str, game_id: str, action: Optional[str], card: Optional[str] = None, advance_turn: bool = True):
        game = self.games.get(game_id)
        if not game:
            raise Exception("Game does not exist.")

        players = game["players"]

        if not action: return game

        game["event"] = None

        if action == "draw_card_from_middle":
            current_player_id = players[game["current_player_index"]]
            if current_player_id != player_id: return game

            selected_card = game["deck"].pop()
            game["player_cards"][current_player_id].append(selected_card)

            if advance_turn: self.advance_turn(game_id)
            return game


        elif action == "play_card":
            current_player_id = players[game["current_player_index"]]
            if current_player_id != player_id or card is None: return game
            card_color, card_value = retrieve_card_info(card)
            top_card = game["discard_pile"][-1]
            _, top_card_value = retrieve_card_info(top_card)

            active_color = game.get("current_active_color")
            is_special_card = card_value in SPECIAL_CARDS or card[2:] in SPECIAL_CARDS
            is_wild_card = card in WILD_CARDS
            # Validation Logic:
            #  - Wilds are always playable
            #  - Matches Active Color (e.g., Red on Red)
            #  - Matches Value (e.g., 5 on 5, or Skip on Skip)
            if is_wild_card or card_color == active_color or card_value == top_card_value:
                game["discard_pile"].append(card)
                game["player_cards"][current_player_id].remove(card)

                if not is_wild_card:
                    game["current_active_color"] = card_color

                if is_special_card:

                    print("CARD: ", card)

                    if card_value == 'S':
                        self.advance_turn(game_id)
                        self.set_event(game_id, "skip", None, game["players"][game["current_player_index"]])

                    elif card_value == 'R':
                        self.reverse_direction(game_id)
                        self.set_event(game_id, "reverse", None)

                    elif card[2:] == 'D2':
                        print("playing draw2 card")
                        next_p_index = advance_turn_counter(
                            game["current_player_index"],
                            len(players),
                            game["direction"]
                        )
                        victim_id = game["players"][next_p_index]
                        self.set_event(game_id, "draw2", current_player_id, victim_id)
                        self.advance_turn(game_id)
                        return game

                elif is_wild_card:
                    # Trigger Frontend Modal to turn color
                    if 'Wild' in card and 'W4' not in card:
                        self.set_event(game_id, "wild_color_pick", current_player_id)
                        return game

                    elif 'W4' in card:
                        self.set_event(game_id, "wild_color_pick_draw4", current_player_id)
                        return game

                self.advance_turn(game_id)
            return game

        elif action == "change_color_with_wild":
            return self.use_wild_card(card, game_id)

        elif action == "change_color_with_wild_and_draw4":
            player_id = players[game["current_player_index"]]
            self.use_wild_card(card, game_id)
            self.set_event(game_id, "draw4", player_id, players[game["current_player_index"]])
            return game

        return game