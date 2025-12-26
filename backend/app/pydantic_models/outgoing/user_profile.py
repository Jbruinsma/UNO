from pydantic import BaseModel, ConfigDict, EmailStr
from pydantic.alias_generators import to_camel
from datetime import date, datetime
from decimal import Decimal


class UserProfile(BaseModel):
    user_id: str
    username: str
    email: EmailStr
    birthday: date
    current_balance: Decimal
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True
    )