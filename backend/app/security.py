import os
from datetime import datetime, timedelta

import jwt
from passlib.context import CryptContext

# Create a "context" that specifies we want to use bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """
    Takes a plain text password and returns a hashed string.
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Checks if a plain password matches the hash.
    Used during Login.
    """
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes= int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30)))
    to_encode.update({"exp": expire})

    # Create the encoded JWT
    encoded_jwt = jwt.encode(to_encode, os.getenv("SECRET_KEY"), algorithm= os.getenv("ALGORITHM"))
    return encoded_jwt