from fastapi import APIRouter, HTTPException, status, Request, Depends, UploadFile, File
from src.users.schemas import UserRead
from sqlalchemy.ext.asyncio import AsyncSession
from src.common.logger import logger
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from src.common.rbac import get_current_user
from src.database import get_async_session
from src.models import User
from src.users.schemas import UserProfilePatch, UserProfileUpdate
from src.users.service import user_profile_patch_form, user_profile_update_form
from typing import Optional
from src.auth.service import authenticate
from src.common.rbac import CurrentUser
from src.users.utils import get_user_by_email, get_user_by_username
from src.auth.utils import pwd_context
from src.common.image_utils import get_image_key, gen_uuid

router = APIRouter(prefix='/user')

@router.get('/profile', response_model=UserRead)
async def get_profile(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(select(User).where(User.id == current_user.id).options(
        selectinload(User.likes),
        selectinload(User.playlists),
        selectinload(User.history)
    ))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        logger.error(f'User with {current_user.id} id not found')
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'User with {current_user.id} id not found')
    return user

@router.put('/profile', response_model=UserRead)
async def update_profile(
    request: Request,
    user: User = Depends(authenticate),
    user_data: UserProfileUpdate = Depends(user_profile_update_form),
    avatar: UploadFile = File(..., description='Avatar for user'),
    session: AsyncSession = Depends(get_async_session) 
) -> User:

    usr = await get_user_by_username(username=user_data.new_username, session=session) 
    if usr and usr.id != user.id:
        logger.error(f'User with {user_data.new_username} username already exists!')
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f'User with {user_data.new_username} username already exists!')
    
    usr = await get_user_by_email(email=user_data.new_email, session=session)
    if usr and usr.id != user.id:
        logger.error(f'User with {user_data.new_email} email already exists!')
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f'User with {user_data.new_email} email already exists!')

    if user_data.new_password != user_data.new_password2:
        logger.error(f'Invalid password2 for user {user.username}')
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f'Invalid password2 for user {user.username}')
    
    try:
        avatar_key = await get_image_key(key=gen_uuid()+'_'+str(user.id), file=avatar)
    except Exception as e:
        logger.error(f'Failed upload user avatar: {e}')
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=f'Failed upload user avatar: {e}')
    
    try:
        user.username = user_data.new_username
        user.email = user_data.new_email
        user.hashed_password = pwd_context.hash(user_data.new_password)
        user.image_key = avatar_key

        await session.commit()
        await session.refresh(user)
        logger.success(f'Successful update for {user.username} profile')

        return user

    except Exception as e:
        logger.error(f'Failed to update user profile: {e}')
        raise HTTPException(status_code=status.HTTP_500, detail=f'Failed to update user profile: {e}')
    
@router.patch('/profile', response_model=UserRead)
async def patch_profile(
    request: Request,
    user: User = Depends(authenticate),
    user_data: UserProfilePatch = Depends(user_profile_patch_form),
    avatar: Optional[UploadFile] = None,
    session: AsyncSession = Depends(get_async_session)
) -> User:
    
    if user_data.new_username:
        usr = await get_user_by_username(username=user_data.new_username, session=session) 
        if usr and usr.id != user.id:
            logger.error(f'User with {user_data.new_username} username already exists!')
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f'User with {user_data.new_username} username already exists!')
    
    if user_data.new_email:
        usr = await get_user_by_email(email=user_data.new_email, session=session)
        if usr and usr.id != user.id:
            logger.error(f'User with {user_data.new_email} email already exists!')
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f'User with {user_data.new_email} email already exists!')

    if user_data.new_password and not user_data.new_password2 or not user_data.new_password and user_data.new_password2:
        logger.error(f'New password has 2 required fields, but 1 given')
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f'New password has 2 required fields, but 1 given')

    if user_data.new_password and user_data.new_password2 and user_data.new_password != user_data.new_password2:
        logger.error(f'Invalid password2 for user {user.username}')
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f'Invalid password2 for user {user.username}')
    
    try:
        if avatar:
            avatar_key = get_image_key(key=gen_uuid()+'_'+str(user.id), file=avatar)
    except Exception as e:
        logger.error(f'Failed upload user avatar: {e}')
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=f'Failed upload user avatar: {e}')
    
    try:
        if user_data.new_username:
            user.username = user_data.new_username
        if user_data.new_email:
            user.email = user_data.new_email
        if user_data.new_password:
            user.hashed_password = pwd_context.hash(user_data.new_password)
        if avatar:
            user.image_key = avatar_key

        await session.commit()
        await session.refresh(user)
        logger.success(f'Successful update for {user.username} profile')

        return user

    except Exception as e:
        logger.error(f'Failed to update user profile: {e}')
        raise HTTPException(status_code=status.HTTP_500, detail=f'Failed to update user profile: {e}')