from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from src.common.logger import logger
from src.database import get_async_session
from src.config import settings
from fastapi.security import OAuth2PasswordBearer
import jwt

from src.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/login')

def verify_access_token(
    token: str = Depends(oauth2_scheme)
) -> int:
    try:
        payload = jwt.decode(jwt=token, key=settings.JWT_SECRET_KEY, algorithms=settings.JWT_ALGORITHM)
        sub = payload.get('sub')

        if not sub:
            logger.warning(f'Not found "sub" in access token ({token})')

        sub = int(sub)
        return sub
    
    except jwt.ExpiredSignatureError as e:
        logger.error(f'Access token expired: {e}')
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Access token expired: {e}')
    except jwt.InvalidTokenError as e:
        logger.error(f'Invalid access token: {e}')
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Invalid access token: {e}')
    except Exception as e:
        logger.error(f'Error, while trying to verify access token: {e}')
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Error, while trying to verify access token: {e}')
    
async def get_current_user(
    user_id: int = Depends(verify_access_token),
    session: AsyncSession = Depends(get_async_session)
) -> User:
    result = await session.execute(select(User).where(User.id == user_id).options(
        selectinload(User.likes),
        selectinload(User.playlists)
    ))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        logger.error(f'User with {user_id} id not found')
        raise HTTPException(status_code=status.HTTP_401_NOT_FOUND, detail=f'User with {user_id} id not found')
    
    return user

async def get_current_superuser(
    user: User = Depends(get_current_user)
) -> User:
    if not user.is_superuser:
        logger.error(f'Access denied for {user.username} with {user.id} id')
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f'Access denied for {user.username} with {user.id} id')
    
    return user