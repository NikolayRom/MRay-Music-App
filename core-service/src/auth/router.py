from fastapi import APIRouter, Request, Depends, HTTPException, status
from src.users.schemas import UserAuth, UserRead
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_async_session
from src.users.utils import get_user_by_username
from src.auth.utils import pwd_context
from src.models import User
from src.common.logger import logger
from src.auth.service import authenticate

router = APIRouter(prefix='/auth')

@router.post('/registration', response_model=UserRead)
async def register(
    request: Request,
    user: UserAuth,
    session: AsyncSession = Depends(get_async_session)
):
    if await get_user_by_username(user.username):
        logger.error(f'User with {user.username} already exists!')
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='User already exist')

    hashed_password = pwd_context.hash(user.password)

    new_user = User(
        username=user.username,
        hashed_password=hashed_password
    )

    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    logger.success(f'Successfull create of new user: {user.username}')

    return new_user

@router.post('/login', response_model=UserRead)
async def login(
    request: Request,
    user: UserAuth = Depends(authenticate),
    session: AsyncSession = Depends(get_async_session)
):
    pass