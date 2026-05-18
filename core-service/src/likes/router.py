from fastapi import APIRouter, Request, Depends, HTTPException, status, Response
from src.likes.schemas import LikeRead, LikesAllRead, LikeData
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_async_session
from sqlalchemy import select
from src.models import Like
from src.common.logger import logger
from src.common.rbac import get_current_user, CurrentUser

router = APIRouter(prefix='/likes')

@router.get('/', response_model=LikesAllRead)
async def get_all_likes(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):

    result = await session.execute(select(Like).where(Like.user_id == current_user.id))
    likes = result.scalars().all()

    return LikesAllRead(
        items=likes
    )

@router.get('/{track_id}', response_model=LikeRead)
async def get_like(
    request: Request,
    track_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):

    result = await session.execute(select(Like).where(
        Like.track_id == track_id,
        Like.user_id == current_user.id
    ))
    like = result.scalar_one_or_none()

    if not like:
        logger.warning(f'Like from user with {current_user.id} id to track with {track_id} id not found')
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Like from user with {current_user.id} id to track with {track_id} id not found')

    return like

@router.post('/', response_model=LikeRead, status_code=status.HTTP_201_CREATED)
async def toggle_like(
    request: Request,
    like_data: LikeData,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    
    result = await session.execute(select(Like).where(
        Like.track_id == like_data.track_id,
        Like.user_id == current_user.id
    ))
    like = result.scalar_one_or_none()

    if not like:
        like = Like(
            user_id=current_user.id,
            track_id=like_data.track_id
        )
        session.add(like)
        await session.commit()
        await session.refresh(like)
        logger.success(f'Successfully set like to track ({like_data.track_id}) from user ({current_user.id})')
        return like
    else:
        await session.delete(like)
        await session.commit()
        logger.success(f'Successfully delete like from user ({current_user.id}) to track ({like_data.track_id})')
        return Response(status_code=status.HTTP_204_NO_CONTENT)