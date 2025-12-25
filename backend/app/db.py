from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

from .config import settings

Base = declarative_base()

# Async engine using aiomysql
engine = create_async_engine(settings.database_url, echo=False, future=True)

# Session factory
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

# Dependency for FastAPI endpoints
async def get_session():
    async with async_session() as session:
        yield session
