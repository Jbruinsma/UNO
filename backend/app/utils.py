import random


def create_deck():
    deck = []
    colors = ['R', 'B', 'G', 'Y']
    specials = ['S', 'R', 'D2']

    for color in colors:
        deck.append(f"{color}-0")

        for i in range(1, 10):
            deck.append(f"{color}-{i}")
            deck.append(f"{color}-{i}")

        for sp in specials:
            deck.append(f"{color}-{sp}")
            deck.append(f"{color}-{sp}")

    for _ in range(4):
        deck.append("W-Wild")
        deck.append("W-W4")

    random.shuffle(deck)
    return deck
