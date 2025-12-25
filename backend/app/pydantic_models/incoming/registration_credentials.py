from datetime import date
from pydantic import BaseModel, field_validator, model_validator, EmailStr

from backend.app.utils import str_to_date_iso


class RegistrationCredentials(BaseModel):
    username: str
    password: str
    email: EmailStr
    birthday: str

    @field_validator('username')
    def username_length(cls, v):
        if 2 < len(v) < 37:
            return v
        raise ValueError("Username must be between 3 and 36 characters long.")

    @field_validator('username')
    def username_no_characters(cls, v):
        if '@' not in v and '.' not in v:
            return v
        raise ValueError("Username must not contain '@' or '.' characters.")

    @model_validator(mode= 'after')
    def username_email_valid(self):
        if self.username == self.email:
            raise ValueError("Username and email cannot be the same.")
        return self

    @field_validator('birthday')
    def birthday_validations(cls, v):
        birthday_iso = str_to_date_iso(v)

        if birthday_iso:
            today = date.today()
            age = today.year - birthday_iso.year - (
                    (today.month, today.day) < (birthday_iso.month, birthday_iso.day)
            )

            if age < 18:
                raise ValueError("You must be at least 18 years old to register.")
        else:
            raise ValueError("Invalid date format. Please use YYYY-MM-DD.")
        return v