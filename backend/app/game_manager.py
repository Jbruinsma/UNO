from typing import Dict, List, Optional


class GameManager:
    """
    Manages the Game Logic and Room State.
    Does NOT know about WebSockets. Only knows about User IDs.
    """

    def __init__(self):
        # Key: game_id, Value: Dict containing game state
        self.games: Dict[str, Dict] = {}

    def create_game(self, game_id: str, host_id: str):
        if game_id in self.games:
            raise Exception("Game ID collision. Try again.")

        self.games[game_id] = {
            "host_id": host_id,
            "state": "waiting",
            "players": [host_id],
            "deck": [],
            "discard_pile": []
        }
        return self.games[game_id]

    def join_game(self, game_id: str, user_id: str):
        game = self.games.get(game_id)
        if not game:
            raise Exception("Game does not exist.")

        if game["state"] != "waiting":
            raise Exception("Game has already started.")

        if user_id in game["players"]:
            return game

        game["players"].append(user_id)
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
            if user_id in game["players"]:
                if user_id == game["host_id"]:
                    game["host_id"] = game["players"][1] if len(game["players"]) > 1 else None
                game["players"].remove(user_id)

            # If empty, delete game
            if len(game["players"]) == 0:
                del self.games[game_id]
