from fastapi import APIRouter

from backend.app.pydantic_models.incoming.login_credentials import LoginCredentials

router = APIRouter()

@router.get("/login")
async def login(login_credentials: LoginCredentials):
    pass

@router.get("/register")
async def register():
    pass
