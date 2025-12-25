import uuid
import enum
from sqlalchemy import Column, String, BigInteger, DECIMAL, ForeignKey, TIMESTAMP, Date, Enum
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

from backend.app.db import Base


class TransactionType(enum.Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    GAME_BUY_IN = "GAME_BUY_IN"
    GAME_WIN = "GAME_WIN"
    GAME_PENALTY = "GAME_PENALTY"
    DAILY_REWARD = "DAILY_REWARD"


class GameStatus(enum.Enum):
    WAITING = "WAITING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"



class User(Base):
    __tablename__ = "users"

    # Generates a UUID automatically when you create a new User() object
    user_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    birthday = Column(Date, nullable=False)
    password_hash = Column(String(255), nullable=False)
    current_balance = Column(DECIMAL(15, 2), default=0.00)
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relationships
    transactions = relationship("WalletTransaction", back_populates="user")


class WalletTransaction(Base):
    __tablename__ = "wallet_transactions"

    transaction_id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("users.user_id"), nullable=False)
    amount = Column(DECIMAL(15, 2), nullable=False)
    transaction_type = Column(Enum(TransactionType), nullable=False)

    # FIXED: Matches the SQL CHAR(36) change
    reference_id = Column(String(36), nullable=True)

    description = Column(String(255), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

    user = relationship("User", back_populates="transactions")


class Game(Base):
    __tablename__ = "games"

    game_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    room_code = Column(String(10), unique=True, nullable=False)
    status = Column(Enum(GameStatus), default=GameStatus.WAITING)
    buy_in_amount = Column(DECIMAL(10, 2), nullable=False)
    pot_total = Column(DECIMAL(10, 2), default=0.00)

    # Optional link to the winner
    winner_user_id = Column(String(36), ForeignKey("users.user_id"), nullable=True)

    created_at = Column(TIMESTAMP, server_default=func.now())
    finished_at = Column(TIMESTAMP, nullable=True)

    winner = relationship("User")