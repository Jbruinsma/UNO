from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db import get_session
from backend.app.models import User
from backend.app.pydantic_models.outgoing.user_profile import UserProfile
from backend.app.security import get_current_user

router = APIRouter()

@router.get("/me", response_model= UserProfile)
async def get_profile(current_user: User = Depends(get_current_user)):
    return current_user
