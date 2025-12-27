import uuid
import enum
from sqlalchemy import Column, String, BigInteger, DECIMAL, ForeignKey, TIMESTAMP, Date, Enum, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db import Base



class TransactionType(enum.Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    GAME_BUY_IN = "GAME_BUY_IN"
    GAME_WIN = "GAME_WIN"
    GAME_REFUND = "GAME_REFUND"
    DAILY_REWARD = "DAILY_REWARD"


class GameSessionStatus(enum.Enum):
    WAITING = "WAITING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class CatalogStatus(enum.Enum):
    ACTIVE = "ACTIVE"
    MAINTENANCE = "MAINTENANCE"
    COMING_SOON = "COMING_SOON"


class UserRole(enum.Enum):
    USER = "USER"
    ADMIN = "ADMIN"


class UserStatus(enum.Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    DEACTIVATED = "DEACTIVATED"

class SessionType(enum.Enum):
    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"

class User(Base):
    __tablename__ = "users"

    user_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    birthday = Column(Date, nullable=False)
    password_hash = Column(String(255), nullable=False)
    current_balance = Column(DECIMAL(15, 2), default=0.00)
    role = Column(Enum(UserRole), default=UserRole.USER)
    status = Column(Enum(UserStatus), default=UserStatus.ACTIVE)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    transactions = relationship("WalletTransaction", back_populates="user")
    hosted_games = relationship("GameSession", foreign_keys="GameSession.host_user_id", back_populates="host")


class GameCatalog(Base):
    __tablename__ = "game_catalog"

    game_type_id = Column(String(20), primary_key=True)
    display_name = Column(String(50), nullable=False)
    description = Column(String(255), nullable=False)
    status = Column(Enum(CatalogStatus), default=CatalogStatus.COMING_SOON)
    image_asset = Column(String(50), nullable=False)
    frontend_route = Column(String(50), nullable=False)
    min_players = Column(Integer, default=2)
    max_players = Column(Integer, default=10)
    created_at = Column(TIMESTAMP, server_default=func.now())

    sessions = relationship("GameSession", back_populates="game_type")


class GameSession(Base):
    __tablename__ = "game_sessions"

    session_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    game_type_id = Column(String(20), ForeignKey("game_catalog.game_type_id"), nullable=False)
    room_code = Column(String(10), unique=True, nullable=False)
    host_user_id = Column(String(36), ForeignKey("users.user_id"), nullable=False)
    room_type = Column(Enum(SessionType), default=SessionType.PUBLIC)
    status = Column(Enum(GameSessionStatus), default=GameSessionStatus.WAITING)
    current_players = Column(Integer, default=1)
    max_players = Column(Integer, nullable=False, default=10)
    buy_in_amount = Column(DECIMAL(10, 2), nullable=False, default=0.00)
    pot_total = Column(DECIMAL(10, 2), default=0.00)
    round_number = Column(Integer, default=0)
    created_at = Column(TIMESTAMP, server_default=func.now())
    finished_at = Column(TIMESTAMP, nullable=True)

    game_type = relationship("GameCatalog", back_populates="sessions")
    host = relationship("User", foreign_keys=[host_user_id], back_populates="hosted_games")


class WalletTransaction(Base):
    __tablename__ = "wallet_transactions"

    transaction_id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("users.user_id"), nullable=False)
    amount = Column(DECIMAL(15, 2), nullable=False)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    reference_id = Column(String(36), nullable=True)
    description = Column(String(255), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

    user = relationship("User", back_populates="transactions")