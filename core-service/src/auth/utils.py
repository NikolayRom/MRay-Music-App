from passlib.context import CryptContext
import hashlib
import secrets
from src.auth.schemas import AccessTokenCreate
from datetime import datetime, timedelta, timezone
import jwt
from src.config import settings
from src.models import RefreshToken
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete

pwd_context = CryptContext(schemes=["bcrypt"])

def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

def gen_token() -> str:
    return secrets.token_urlsafe(64)

def check_token_expired(token: RefreshToken) -> bool:
    return token.exp < datetime.now(timezone.utc)

def check_token_inactive(token: RefreshToken) -> bool:
    return not token.is_active

def create_access_token(user_id: int) -> str:
    return jwt.encode(
        payload=AccessTokenCreate.create(user_id).model_dump(),
        key=settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )

def create_refresh_token(user_id: int) -> RefreshToken:
    return RefreshToken(
        user_id=user_id,
        hashed_token=hash_token(gen_token()),
        exp=datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    )

async def clear_all_refresh_tokens(user_id: int, session: AsyncSession) -> None:
    await session.execute(delete(RefreshToken).where(RefreshToken.user_id == user_id))
    await session.commit()