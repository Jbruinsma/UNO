from pathlib import Path
from dotenv import load_dotenv
import os

# Load .env from the backend/ directory if present so environment variables are available
env_path = Path(__file__).resolve().parents[1] / '.env'
if env_path.exists():
    load_dotenv(env_path)

from pydantic import BaseModel, Field, ValidationError


class Settings(BaseModel):
    DB_USER: str = Field(...)
    DB_PASS: str = Field(...)
    DB_HOST: str = Field("127.0.0.1")
    DB_PORT: int = Field(3306)
    DB_NAME: str = Field(...)

    @property
    def database_url(self) -> str:
        return f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"


try:
    settings = Settings(
        DB_USER=os.getenv("DB_USER"),
        DB_PASS=os.getenv("DB_PASSWORD"),
        DB_HOST=os.getenv("DB_HOST", "127.0.0.1"),
        DB_PORT=int(os.getenv("DB_PORT", 3306)),
        DB_NAME=os.getenv("DB_NAME"),
    )
except ValidationError as e:
    raise RuntimeError(f"Invalid environment configuration: {e}")
