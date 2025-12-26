from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import GameCatalog, User
from app.pydantic_models.outgoing.game_option import GameOption
from app.security import get_current_user

router = APIRouter()

@router.get("/catalog", response_model= List[GameOption])
async def catalog(db: AsyncSession = Depends(get_session), current_user: User = Depends(get_current_user)):
    query_result = await db.execute(select(GameCatalog).order_by(GameCatalog.created_at))
    game_catalog = query_result.scalars().all()
    return game_catalog
