from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError


from app.models import User
from app.pydantic_models.incoming.login_credentials import LoginCredentials
from app.pydantic_models.incoming.registration_credentials import RegistrationCredentials


from app.db import get_session
from app.security import hash_password, verify_password, create_access_token
from app.utils import str_to_date_iso

router = APIRouter()


@router.post("/login")
async def login(login_credentials: LoginCredentials, db: AsyncSession = Depends(get_session)):
    existing_user_statement = select(User).where(User.username == login_credentials.username)
    result = await db.execute(existing_user_statement)
    existing_user = result.scalars().first()

    if not existing_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    unhashed_pw = verify_password(login_credentials.password, existing_user.password_hash)
    if not unhashed_pw:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(
        data={"sub": existing_user.username, "id": existing_user.user_id }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_role": existing_user.role
    }

@router.post("/register")
async def register(registration_credentials: RegistrationCredentials, db: AsyncSession = Depends(get_session)):
    existing_user_statement = select(User).where(
        or_(
            User.username == registration_credentials.username,
            User.email == registration_credentials.email
        )
    )
    result = await db.execute(existing_user_statement)
    existing_user = result.scalars().first()

    if existing_user:
        if existing_user.username == registration_credentials.username:
            detail_msg = "Username already taken."
        else:
            detail_msg = "Email already registered."

        raise HTTPException(status_code=400, detail=detail_msg)

    try:
        hashed_pw = hash_password(registration_credentials.password)

        new_user = User(
            username= registration_credentials.username,
            email= str(registration_credentials.email),
            birthday= str_to_date_iso(registration_credentials.birthday),
            password_hash= hashed_pw
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        return {
            "message": "User created successfully",
            "user_id": new_user.user_id,
        }

    except IntegrityError:
        # Catches race conditions
        await db.rollback()
        raise HTTPException(status_code=400, detail="User already exists.")

    except Exception as e:
        print(f"Registration Error: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error")