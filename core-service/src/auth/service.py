from fastapi import HTTPException, status, Depends
from src.auth.utils import pwd_context, create_access_token, create_refresh_token, check_token_expired, check_token_inactive, clear_all_refresh_tokens, hash_token, set_inactive_refresh_token, get_refresh_token_from_db
from src.users.schemas import UserAuth
from src.users.utils import get_user_by_username
from src.common.logger import logger
from src.models import User
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from src.database import get_async_session
from src.config import settings
from src.auth.schemas import RefreshTokenRequest
import jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/login')

async def authenticate(credentials: UserAuth, session: AsyncSession = Depends(get_async_session)) -> User:
    user = await get_user_by_username(username=credentials.username, session=session)
    
    if not user:
        logger.error(f'User with {credentials.username} username not found')
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')
    
    if not pwd_context.verify(credentials.password, user.hashed_password):
        logger.error(f'Incorrect password for {credentials.username}')
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Incorrect password')
    
    return user

async def create_tokens(user: User, session: AsyncSession) -> tuple[str, RefreshTokenRequest]:
    
    access_token = create_access_token(user=user)

    user_id = user.id

    refresh_token, refresh_token_db = create_refresh_token(user_id=user_id)

    session.add(refresh_token_db)
    await session.commit()
    await session.refresh(refresh_token_db)
    logger.success(f'Create new tokens for user ({user_id})')

    return (
        access_token,
        refresh_token
    )
    
async def verify_refresh_token(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_async_session)
) -> RefreshTokenRequest:
    try:
        token_data = await get_refresh_token_from_db(token=token, session=session)
        if not token_data:
            raise jwt.DecodeError()
        if check_token_inactive(token_data):
            raise jwt.InvalidIssuerError()
        if check_token_expired(token_data):
            raise jwt.ExpiredSignatureError()
        
        return token
    
    except jwt.DecodeError as e:
        logger.error(f'Refresh token not found: {e}')
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Refresh token not found: {e}')
    except jwt.InvalidIssuerError as e:
        logger.critical(f'Refresh token is inactive. Suspicion of refresh token theft: clear all refresh tokens of user ({token.user_id})')
        await clear_all_refresh_tokens(user_id=token.user_id, session=session)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Refresh token is inactive. Suspicion of refresh token theft: clear all refresh tokens of user ({token.user_id})')      
    except jwt.ExpiredSignatureError as e:
        logger.error(f'Refresh token expired: {e}')
        await set_inactive_refresh_token(refresh_token=token_data, session=session)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Refresh token expired: {e}')
    except Exception as e:
        logger.error(f'Erorr, while trying to verify refresh token: {e}')
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Erorr, while trying to verify refresh token: {e}')