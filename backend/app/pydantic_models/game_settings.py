from enum import Enum
from pydantic import BaseModel, Field, field_validator


class StackingMode(str, Enum):
    """Defines how players can stack draw cards."""

    OFF = "off"  # No stacking allowed
    STANDARD = "standard"  # +2 on +2 only
    AGGRESSIVE = "aggressive"  # +2 on +4, +4 on +2, etc.


class AFKBehavior(str, Enum):
    """What happens when the timer runs out?"""

    DRAW_AND_SKIP = "draw_skip"  # Auto-draw penalty and next turn
    AUTO_PLAY = "skip"  # Player skips their turn


class GameSettings(BaseModel):
    # Time Limit (with validation)
    turn_timeout_seconds: int = Field(
        default=30,
        ge=5,
        le=120,
        description="Time in seconds per turn. Min 5, Max 120."
    )

    # Stacking Rules
    stacking_mode: StackingMode = Field(
        default=StackingMode.STANDARD,
        description="Rules regarding stacking Draw 2s and Draw 4s."
    )

    # AFK / Penalty Logic
    afk_behavior: AFKBehavior = Field(
        default=AFKBehavior.DRAW_AND_SKIP,
        description="Action taken when timer expires."
    )

    max_afk_strikes: int = Field(
        default=3,
        ge=0,
        description="How many times a player can time out before being kicked (0 = infinite)."
    )

    kick_after_max_strikes: bool = Field(
        default=True,
        description="Whether to kick the player after they reach the maximum number of strikes."
    )
