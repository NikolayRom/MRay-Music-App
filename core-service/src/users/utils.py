from sqlalchemy.ext.asyncio import AsyncSession
from src.models import User
from sqlalchemy import select
from src.common.logger import logger
from sqlalchemy.orm import selectinload

async def get_user_by_username(username: str, session: AsyncSession) -> User | None:
    result = await session.execute(select(User).where(User.username == username).options(
        selectinload(User.likes),
        selectinload(User.playlists),
        selectinload(User.history)
    ))
    user = result.scalar_one_or_none()

    if not user:
        logger.warning(f'User with {username} username not found')

    return user

async def get_user_by_email(email: str, session: AsyncSession) -> User | None:
    
    result = await session.execute(select(User).where(User.email == email).options(
        selectinload(User.likes),
        selectinload(User.playlists),
        selectinload(User.history)
    ))    
    user = result.scalar_one_or_none()

    if not user:
        logger.warning(f'User with {email} email not found')

    return user