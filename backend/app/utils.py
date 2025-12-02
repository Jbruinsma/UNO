import random
from typing import Tuple, List

SPECIAL_CARDS: List[str] = ['S', 'R', 'D2']
WILD_CARDS: List[str] = ['W-Wild', 'W-W4']
REGULAR_CARDS: List[str] = ['R', 'B', 'G', 'Y']

def create_deck() -> List[str]:
    """
    Creates a shuffled deck of cards
    """

    deck: List[str] = []

    for color in REGULAR_CARDS:
        deck.append(f"{color}-0")

        for i in range(1, 10):
            deck.append(f"{color}-{i}")
            deck.append(f"{color}-{i}")

        for sp in SPECIAL_CARDS:
            deck.append(f"{color}-{sp}")
            deck.append(f"{color}-{sp}")

    for _ in range(4):
        deck.append("W-Wild")
        deck.append("W-W4")

    random.shuffle(deck)
    return deck

def advance_turn_counter(current_player_index: int, player_count: int, is_clockwise: bool) -> int:
    """
    Advances the turn counter based on the current direction of play.
    """

    if is_clockwise:
        return 0 if current_player_index == player_count - 1 else current_player_index + 1
    else:
        return player_count - 1 if current_player_index == 0 else current_player_index - 1


def retrieve_card_info(card: str) -> Tuple[str, str]:
    """
    Retrieves the color and number of a card.
    """

    return card[0], card[-1]