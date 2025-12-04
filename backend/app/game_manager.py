import random
from typing import Dict, List, Optional, Set

from backend.app.pydantic_models.game import Game
from backend.app.pydantic_models.game_settings import GameSettings, StackingMode, AFKBehavior
# Assuming these imports exist in your project structure
from backend.app.utils import create_deck, SPECIAL_CARDS, WILD_CARDS, advance_turn_counter, retrieve_card_info, \
    REGULAR_CARDS


class GameManager:
    """
    Manages the Game Logic and Room State.
    Does NOT know about WebSockets. Only knows about User IDs.
    """

    def __init__(self) -> None:
        """
        Initializes the GameManager with an empty dictionary of games.
        """

        self.games: Dict[str, Game] = {}

    def create_game(self, game_id: str, host_id: str, host_name: str) -> Game:
        """
        Creates a new game and adds it to the manager.
        """

        if game_id in self.games:
            raise Exception("Game ID collision. Try again.")

        self.games[game_id] = Game(
            host_id= host_id,
            game_settings= GameSettings(),
            state= "waiting",
            players= [host_id],
            player_names= {
                host_id: host_name
            },
            player_states= {
                host_id: "ready"
            },
            current_player_index= None,
            current_active_color= None,
            direction= 1,  # 1 = clockwise, -1 = counterclockwise
            event= None,
            deck= [],
            discard_pile= [],
            player_cards= {}
        )
        return self.games[game_id]

    def get_lobby_info(self) -> List[Dict]:
        """
        Returns a summary of all games for the lobby browser.
        """

        lobby_data = []
        for game_lobby_id, game_state in self.games.items():
            lobby_data.append({
                "game_id": game_lobby_id,
                "host_name": game_state.player_names.get(game_state.host_id, "Unknown"),
                "player_count": len(game_state.players),
                "state": game_state.state
            })
        return lobby_data

    def update_game_settings(self, game_id: str, game_settings: Dict) -> Optional[Game]:
        game: Optional[Game] = self.games.get(game_id)
        if not game:
            return None

        should_forfeit = game_settings.get("forfeitAfterSkips", True)
        strikes = 3 if should_forfeit else 0

        try:
            s_mode = StackingMode(game_settings.get("stackingMode", "off").lower())
            a_behavior = AFKBehavior(game_settings.get("afkBehavior", "draw_skip").lower())

            game.game_settings = GameSettings(
                turn_timeout_seconds=game_settings.get("turnTimer", 30),
                stacking_mode= s_mode,
                afk_behavior= a_behavior,
                max_afk_strikes= strikes,
                kick_after_max_strikes= should_forfeit
            )

            return game

        except ValueError as e:
            print(f"Invalid setting provided: {e}")
            return None
        except Exception as e:
            print(f"General error updating settings: {e}")
            return None

    def reset_game(self, game_id: str) -> Game:
        """
        Resets a game to its initial state.
        """

        game = self.games.get(game_id)
        if not game:
            raise Exception("Game ID collision. Try again.")

        game.state = "waiting"
        game.current_player_index = None
        game.current_active_color = None
        game.direction = 1
        game.event = None
        game.deck = []
        game.discard_pile = []
        game.player_cards = {}

        return game

    def end_game(self, game_id: str) -> None:
        """
        Ends a game and removes it from the manager.
        """

        self.reset_game(game_id)

    def set_player_back_to_lobby(self, game_id: str, user_id: str) -> Optional[Game]:
        """
        Sets a player back to the lobby after they've left.
        """

        game = self.games.get(game_id)
        if game:
            game.player_states[user_id] = "ready"
            return game
        return None

    def advance_turn(self, game_id: str) -> None:
        """
        Advances the turn counter and resets the active color.
        """

        game: Optional[Game] = self.games.get(game_id)
        if not game: return

        is_clockwise: bool = game.direction == 1

        assert game.current_player_index is not None
        current_player_index: int = game.current_player_index

        players: List[str] = game.players
        player_count: int = len(players)

        game.current_player_index = advance_turn_counter(current_player_index, player_count, is_clockwise)

    def reverse_direction(self, game_id: str) -> None:
        """
        Reverses the direction of the game; clockwise (1) -> counterclockwise (-1), counterclockwise (-1) -> clockwise (1).
        """

        game: Optional[Game] = self.games.get(game_id)
        if game:
            game.direction *= -1

    def use_wild_card(self, color: Optional[str], game_id: str) -> Optional[Game]:
        """
        Changes the active color to the color specified by the wild card.
        """

        game: Optional[Game] = self.games.get(game_id)
        if not game: return None

        if color is None:
            self.advance_turn(game_id)
            return game

        new_color, _ = retrieve_card_info(color)
        if new_color not in REGULAR_CARDS:
            self.advance_turn(game_id)
            return game

        game.current_active_color = new_color
        self.advance_turn(game_id)
        return game

    def set_event(self, game_id: str, event_type: str, player_id: Optional[str],
                  affected_player_id: Optional[str] = None):
        """
        Sets the event for the frontend to display.
        """

        game = self.games.get(game_id)
        if game:
            game.event = {"type": event_type, "player_id": player_id, "affected_player_id": affected_player_id}

    def join_game(self, game_id: str, user_id: str, user_name: str) -> Game:
        """
        Adds a player to a game.
        """

        game: Optional[Game] = self.games.get(game_id)
        if not game:
            raise Exception("Game does not exist.")

        if game.state != "waiting":
            raise Exception("Game has already started.")

        players: List[str] = game.players
        player_count: int = len(players)

        if player_count >= 10:
            raise Exception("Game is full. Try again later.")

        if user_id not in players:
            game.players.append(user_id)
            game.player_names[user_id] = user_name
            game.player_states[user_id] = "ready"
            game.player_cards[user_id] = []

        return game

    def get_game(self, game_id: str) -> Optional[Game]:
        """
        Returns the game state for the frontend.
        """

        return self.games.get(game_id)

    def get_player_ids(self, game_id: str) -> List[str]:
        """
        Returns a list of player IDs in the game.
        """

        game: Optional[Game] = self.games.get(game_id)
        return game.players if game else []

    def remove_player(self, game_id: str, user_id: str) -> None:
        """
        Removes a player from a game.
        """

        if game_id in self.games:
            game: Game = self.games[game_id]
            players: List[str] = game.players

            if "player_names" in game.model_fields_set and user_id in game.player_names:
                del game.player_names[user_id]

            if user_id in players:
                game.players.remove(user_id)
                del game.player_states[user_id]

                if user_id == game.host_id and len(game.players) > 0:
                    game.host_id = game.players[0]

            if len(game.players) == 0:
                del self.games[game_id]

    def start_game(self, game_id: str) -> Game:
        """
        Starts the game if all players are ready.
        """

        game: Optional[Game] = self.games.get(game_id)
        if not game: raise Exception("Game does not exist.")

        player_ids: List[str] = game.players
        if len(player_ids) < 2:
            raise Exception("Not enough players to start game.")

        player_states: Set[str] = set(game.player_states.values())
        if "playing" in player_states:
            return game

        game.state = "playing"
        for player_id in player_ids:
            game.player_states[player_id] = "playing"

        game.deck = create_deck()

        for player_id in player_ids:
            game.player_cards[player_id] = []
            for _ in range(7):
                if len(game.deck) > 0:
                    game.player_cards[player_id].append(game.deck.pop())

        if len(game.deck) > 0:
            first_card: str = game.deck.pop()
            first_card_color, _ = retrieve_card_info(first_card)
            game.discard_pile.append(first_card)
            game.current_active_color = first_card_color if first_card_color in REGULAR_CARDS else random.choice(
                list(REGULAR_CARDS))

        start_index: int = random.randint(0, len(player_ids) - 1)
        game.current_player_index = start_index

        return game

    def process_turn(self, player_id: str, game_id: str, action: Optional[str], card: Optional[str] = None,
                     advance_turn: bool = True) -> Optional[Game]:
        """
        Processes a player's turn based on the action taken.
        """

        game: Optional[Game] = self.games.get(game_id)
        if not game: raise Exception("Game does not exist.")

        players: List[str] = game.players
        if not action: return game

        if game.current_player_index is None: return game
        current_player_index: int = game.current_player_index

        game.event = None

        if action == "draw_card_from_middle":
            current_player_id = players[current_player_index]
            if current_player_id != player_id: return game

            selected_card = game.deck.pop()
            game.player_cards[current_player_id].append(selected_card)

            self.set_event(game_id, "draw_card", current_player_id)

            if advance_turn: self.advance_turn(game_id)
            return game

        elif action == "play_card":
            current_player_id = players[current_player_index]

            if (
                    current_player_id != player_id
                    or card is None
                    or card not in game.player_cards[current_player_id]
            ): return game

            card_color, card_value = retrieve_card_info(card)
            top_card = game.discard_pile[-1]
            _, top_card_value = retrieve_card_info(top_card)

            active_color = game.current_active_color
            is_special_card = card_value in SPECIAL_CARDS or card[2:] in SPECIAL_CARDS
            is_wild_card = card in WILD_CARDS

            if is_wild_card or card_color == active_color or card_value == top_card_value:
                game.discard_pile.append(card)
                game.player_cards[current_player_id].remove(card)

                self.set_event(game_id, "play_card", current_player_id)

                if len(game.player_cards[current_player_id]) == 0:
                    self.set_event(game_id, "win", current_player_id)
                    return game

                if not is_wild_card:
                    game.current_active_color = card_color

                if is_special_card:
                    if card_value == 'S':
                        self.advance_turn(game_id)
                        self.set_event(game_id, "skip", None, game.players[game.current_player_index])
                    elif card_value == 'R':
                        self.reverse_direction(game_id)
                        self.set_event(game_id, "reverse", None)
                    elif card[2:] == 'D2':
                        next_p_index = advance_turn_counter(
                            game.current_player_index,
                            len(players),
                            game.direction == 1
                        )
                        victim_id = players[next_p_index]

                        for _ in range(2):
                            if len(game.deck) > 0:
                                game.player_cards[victim_id].append(game.deck.pop())

                        self.set_event(game_id, "draw2", current_player_id, victim_id)
                        self.advance_turn(game_id)
                        return game

                elif is_wild_card:
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
            player_id_initiator = players[game.current_player_index]
            self.use_wild_card(card, game_id)
            victim_id = players[game.current_player_index]

            for _ in range(4):
                if len(game.deck) > 0:
                    game.player_cards[victim_id].append(game.deck.pop())

            self.set_event(game_id, "draw4", player_id_initiator, victim_id)
            return game

        return game