from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from .config import settings
from .db import engine, Base

@asynccontextmanager
async def lifespan(app):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from .routes.auth import router as auth_router
from .routes.dashboard import router as dashboard_router
from .routes.user import router as user_router

from .routes.games.solo.solo_endpoint import router as solo_router
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
app.include_router(user_router, prefix="/users", tags=["user"])

app.include_router(solo_router, prefix="/games/SOLO", tags=["SOLO"])

@app.get("/health")
async def health() -> Dict[str, Any]:
    return { "status": "ok", "database": settings.DB_NAME }

@app.get("/")
async def root() -> Dict[str, str]:
    """
    Basic health check endpoint.
    """

    return {"message": "UNO WebSocket server is running."}
