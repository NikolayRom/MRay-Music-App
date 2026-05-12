from fastapi import HTTPException, status, Depends
from src.auth.utils import pwd_context, create_access_token, create_refresh_token, check_token_expired, check_token_inactive, clear_all_refresh_tokens
from src.users.schemas import UserAuth, UserRead
from src.users.utils import get_user_by_username
from src.common.logger import logger
from src.models import RefreshToken
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_async_session
from src.config import settings
import jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/login')

async def authenticate(credentials: UserAuth) -> UserRead:
    user = await get_user_by_username(credentials.username)
    
    if not user:
        logger.error(f'User with {credentials.username} username not found')
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')
    
    if not pwd_context.verify(credentials.password, user.hashed_password):
        logger.error(f'Incorrect password for {credentials.username}')
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Incorrect password')
    
    return user

def create_tokens(user_id: int) -> tuple[str, RefreshToken]:
    return (
        create_access_token(user_id=user_id),
        create_refresh_token(user_id=user_id)
    )

def verify_access_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(jwt=token, key=settings.JWT_SECRET_KEY, algorithms=settings.JWT_ALGORITHM)
        return payload.get('sub')
    
    except jwt.ExpiredSignatureError as e:
        logger.error(f'Access token expired: {e}')
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Access token expired: {e}')
    except jwt.InvalidTokenError as e:
        logger.error(f'Invalid access token: {e}')
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Invalid access token: {e}')
    except Exception as e:
        logger.error(f'Error, while trying to verify access token: {e}')
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Error, while trying to verify access token: {e}')
    
async def verify_refresh_token(token: RefreshToken = Depends(oauth2_scheme), session: AsyncSession = Depends(get_async_session)) -> RefreshToken:
    try:
        if check_token_expired(token):
            raise jwt.ExpiredSignatureError()
        if check_token_inactive(token):
            raise jwt.InvalidIssuerError()
        
        return token
    
    except jwt.ExpiredSignatureError as e:
        logger.error(f'Refresh token expired: {e}')
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Refresh token expired: {e}')
    except jwt.InvalidIssuerError as e:
        logger.error(f'Refresh token is inactive. Suspicion of refresh token theft: clear all refresh tokens of user ({token.user_id})')
        await clear_all_refresh_tokens(user_id=token.user_id, session=session)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Refresh token is inactive. Suspicion of refresh token theft: clear all refresh tokens of user ({token.user_id})')        