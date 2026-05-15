from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.common.logger import logger
from src.database import get_async_session
from src.config import settings
from fastapi.security import OAuth2PasswordBearer
import jwt
from pydantic import BaseModel

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/login')

def parse_bool(value: any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ('true', '1', 'yes', 'on')
    if isinstance(value, int):
        return value != 0
    return False

class CurrentUser(BaseModel):
    id: int
    is_superuser: bool

def verify_access_token(
    token: str = Depends(oauth2_scheme)
) -> CurrentUser:
    try:
        payload = jwt.decode(jwt=token, key=settings.JWT_SECRET_KEY, algorithms=settings.JWT_ALGORITHM)
        sub = payload.get('sub')

        if not sub:
            logger.error(f'Invalid token ({token}): "sub" field not found')
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f'Invalid token ({token}): "is_superuser" field not found')

        is_superuser = payload.get('is_superuser', False)

        sub = int(sub)
        is_superuser = parse_bool(is_superuser)
        current_user = CurrentUser(
            id=sub,
            is_superuser=is_superuser
        )
        return current_user
    
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
    current_user: CurrentUser = Depends(verify_access_token),
    session: AsyncSession = Depends(get_async_session)
) -> CurrentUser:
   
    return current_user

async def get_current_superuser(
    current_user: CurrentUser = Depends(get_current_user)
) -> CurrentUser:
    if not current_user.is_superuser:
        logger.error(f'Access denied for {current_user.id} user')
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f'Access denied for {current_user.id} user')
    
    return current_user