from pydantic import BaseModel, ConfigDict
from enum import Enum

from pydantic.alias_generators import to_camel


class CatalogStatus(str, Enum):
    ACTIVE = "ACTIVE"
    MAINTENANCE = "MAINTENANCE"
    COMING_SOON = "COMING_SOON"

class GameOption(BaseModel):
    game_type_id: str
    display_name: str
    description: str
    status: CatalogStatus
    image_asset: str
    frontend_route: str
    min_players: int
    max_players: int

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True
    )