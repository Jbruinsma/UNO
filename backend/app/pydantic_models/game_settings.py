from enum import Enum
from pydantic import BaseModel, Field, field_validator


# --- 1. Define the Choices (Enums) ---

class StackingMode(str, Enum):
    """Defines how players can stack draw cards."""

    OFF = "off"  # No stacking allowed
    STANDARD = "standard"  # +2 on +2 only
    AGGRESSIVE = "aggressive"  # +2 on +4, +4 on +2, etc.


class AFKBehavior(str, Enum):
    """What happens when the timer runs out?"""

    DRAW_AND_SKIP = "draw_skip"  # Auto-draw penalty and next turn
    AUTO_PLAY = "auto_play"  # Bot plays a random valid card
    FORFEIT = "forfeit"  # Player is removed from the game


# --- 2. The Settings Model ---

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

    # --- 3. Optional: Custom Validation Logic ---
    @field_validator('turn_timeout_seconds')
    @classmethod
    def check_sensible_timer(cls, v: int) -> int:
        # Example: Prevent super short timers if AFK behavior is 'FORFEIT'
        # to prevent accidental kicks due to lag.
        if v < 10:
            print(f"Warning: {v}s is a very fast timer for online play due to latency.")
        return v


# --- 4. Usage Example ---

# A. Creating settings from a user (e.g., from a JSON payload)
try:
    frontend_data = {
        "turn_timeout_seconds": 15,
        "stacking_mode": "aggressive",
        "afk_behavior": "draw_skip",
        "max_afk_strikes": 2
    }

    match_settings = GameSettings(**frontend_data)

    print(f"Game Setup: Timer is {match_settings.turn_timeout_seconds}s")
    print(f"Stacking is: {match_settings.stacking_mode.value}")

except Exception as e:
    print(f"Invalid settings: {e}")

# B. Exporting back to JSON (for saving to DB or sending to clients)
# print(match_settings.model_dump_json())