from fastapi import APIRouter, Request, Depends, HTTPException, status
from src.users.schemas import UserRead, UserRegister, UserRegisterRead
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_async_session
from src.users.utils import get_user_by_username, get_user_by_email
from src.auth.utils import pwd_context, get_refresh_token_from_db, set_inactive_refresh_token, send_reset_password_email, clear_all_refresh_tokens
from src.models import User
from src.common.logger import logger
from src.auth.service import authenticate, create_tokens, verify_refresh_token
from src.auth.schemas import TokenPairResponse, RefreshTokenRequest
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone, timedelta
from src.config import settings
import jwt

router = APIRouter(prefix='/auth')

@router.post('/registration', response_model=UserRegisterRead)
async def register(
    request: Request,
    user: UserRegister,
    session: AsyncSession = Depends(get_async_session)
):
    if await get_user_by_username(user.username, session=session):
        logger.error(f'User with {user.username} username already exists!')
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f'User with {user.username} username already exists!')

    if await get_user_by_email(email=user.email, session=session):
        logger.error(f'User with {user.email} email already exists!')
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f'User with {user.email} email already exists!')

    hashed_password = pwd_context.hash(user.password)

    new_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )

    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    logger.success(f'Successfull create of new user: {user.username}')

    return new_user

@router.post('/login', response_model=TokenPairResponse)
async def login(
    request: Request,
    user: User = Depends(authenticate),
    session: AsyncSession = Depends(get_async_session)
):
    access_token, refresh_token = await create_tokens(user=user, session=session)

    return TokenPairResponse(access_token=access_token, refresh_token=refresh_token)

@router.post('/refresh', response_model=TokenPairResponse)
async def refresh(
        request: Request,
        token_data: str = Depends(verify_refresh_token),
        session: AsyncSession = Depends(get_async_session)
):
    token = RefreshTokenRequest(refresh_token=token_data)
    refresh_token_db = await get_refresh_token_from_db(token=token, session=session)
    user_id = refresh_token_db.user_id
    user = await session.get(User, user_id)
    if not user or not user.is_active:
        logger.error(f'User {user_id} not found!')
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'User {user_id} not found!')
    access_token, refresh_token = await create_tokens(user=user, session=session)
    return TokenPairResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )

@router.post('/logout')
async def logout(
    request: Request,
    token_data: str = Depends(verify_refresh_token),
    session: AsyncSession = Depends(get_async_session)
) -> None:
    token = RefreshTokenRequest(refresh_token=token_data)
    refresh_token = await get_refresh_token_from_db(token=token, session=session)

    if not refresh_token:
        logger.error(f'Refresh token not found')
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Refresh token not found')
    
    await set_inactive_refresh_token(refresh_token=refresh_token, session=session)

@router.post('/password/forgot')
async def forgot_password(
    email: str,
    session: AsyncSession = Depends(get_async_session)
):
    user = await get_user_by_email(email=email, session=session)

    if user:
        reset_token = jwt.encode(
            payload={
                'sub': str(user.id),
                'is_superuser': str(user.is_superuser),
                'exp': datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_RESET_TOKEN_EXPIRE_MINUTES)
            },
            key=settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
        send_reset_password_email(email_to=user.email, token=reset_token)

    return {'message': 'Send reset link to email'}

@router.post('/password/reset')
async def reset_password(
    token: str,
    new_password: str,
    session: AsyncSession = Depends(get_async_session)
):
    try:
        payload = jwt.decode(token, key=settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id = int(payload.get('sub'))

        user = await session.get(User, user_id)

        if not user or not user.is_active:
            logger.error(f'User with {user_id} not found')
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'User with {user_id} not found')
        
        user.hashed_password = pwd_context.hash(new_password)
        await clear_all_refresh_tokens(user_id=user_id, session=session)

        await session.commit()
        await session.refresh(user)
        logger.success(f'Password updated successfully for {user.username}')

        return {'message': 'Password updated successfully'}
    
    except jwt.ExpiredSignatureError as e:
        logger.error(f'Reset token expired: {e}')
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Reset token expired: {e}')
    except jwt.InvalidTokenError as e:
        logger.error(f'Invalid reset token: {e}')
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Invalid reset token: {e}')
    except Exception as e:
        logger.error(f'Error, while trying to verify reset token: {e}')
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f'Error, while trying to verify reset token: {e}')