from fastapi import APIRouter, Request, Depends, HTTPException, status
from src.users.schemas import UserRead, UserRegister
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_async_session
from src.users.utils import get_user_by_username, get_user_by_email
from src.auth.utils import pwd_context, get_refresh_token_from_db, set_inactive_refresh_token
from src.models import User
from src.common.logger import logger
from src.auth.service import authenticate, create_tokens, verify_refresh_token
from src.auth.schemas import TokenPairResponse, RefreshTokenRequest
from sqlalchemy import select
from sqlalchemy.orm import selectinload

router = APIRouter(prefix='/auth')

@router.post('/registration', response_model=UserRead)
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
    access_token, refresh_token = await create_tokens(user_id=user.id, session=session)

    return TokenPairResponse(access_token=access_token, refresh_token=refresh_token)

router.post('/refresh', response_model=TokenPairResponse)
async def refresh(
        request: Request,
        token_data: str = Depends(verify_refresh_token),
        session: AsyncSession = Depends(get_async_session)
):
    token = RefreshTokenRequest(refresh_token=token_data)
    refresh_token_db = await get_refresh_token_from_db(token=token, session=session)
    user_id = refresh_token_db.user_id
    access_token, refresh_token = await create_tokens(user_id=user_id, session=session)
    return TokenPairResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )

router.post('/logout')
async def logout(
    request: Request,
    token_data: str = Depends(verify_refresh_token),
    session: AsyncSession = Depends(get_async_session)
):
    token = RefreshTokenRequest(refresh_token=token_data)
    refresh_token = await get_refresh_token_from_db(token=token, session=session)

    if not refresh_token:
        logger.error(f'Refresh token not found')
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Refresh token not found')
    
    await set_inactive_refresh_token(refresh_token=refresh_token, session=session)
