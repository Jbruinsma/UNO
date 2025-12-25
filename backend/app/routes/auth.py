from fastapi import APIRouter

from backend.app.pydantic_models.incoming.login_credentials import LoginCredentials

router = APIRouter()

@router.post("/login")
async def login(login_credentials: LoginCredentials):
    print(login_credentials)
    return {}

@router.post("/register")
async def register():
    pass
