from pydantic import BaseModel, field_validator


class LoginCredentials(BaseModel):
    username: str
    password: str

    @field_validator('username')
    def username_length(cls, v):
        if 2 < len(v) < 37:
            return v
        raise ValueError("Username must be between 3 and 36 characters long.")
