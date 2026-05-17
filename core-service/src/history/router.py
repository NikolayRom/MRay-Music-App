from fastapi import APIRouter, Request, Depends, HTTPException, status, Response
from src.history.schemas import HistoryRead, HistoryAllRead, HistoryDelete, HistoryPost
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_async_session
from sqlalchemy import select
from src.models import UserHistory
from src.common.logger import logger
from src.common.rbac import get_current_user, CurrentUser
from datetime import datetime, timezone

router = APIRouter(prefix='/history')

@router.get('/', response_model=HistoryAllRead)
async def get_all_history(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):

    result = await session.execute(select(UserHistory).where(
        UserHistory.user_id == current_user.id
    ))
    history = result.scalars().all()

    return HistoryAllRead(
        items=history
    )

@router.get('/{track_id}', response_model=HistoryRead)
async def get_history(
    request: Request,
    track_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):

    result = await session.execute(select(UserHistory).where(
        UserHistory.track_id == track_id,
        UserHistory.user_id == current_user.id
    ))
    history = result.scalar_one_or_none()

    if not history:
        logger.warning(f'Track history ({track_id}) from user with {current_user.id} id not found')
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Track history ({track_id}) from user with {current_user.id} id not found')

    return history

@router.post('/', response_model=HistoryRead, status_code=status.HTTP_201_CREATED)
async def post_history(
    request: Request,
    history_data: HistoryPost,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    
    result = await session.execute(select(UserHistory).where(
        UserHistory.track_id == history_data.track_id,
        UserHistory.user_id == current_user.id
    ))
    history = result.scalar_one_or_none()

    if history:
        history.created_at = datetime.now(timezone.utc)
        await session.commit()
        await session.refresh(history)
        logger.info('Updated existing history timestamp')
    else:
        history = UserHistory(
            user_id=current_user.id,
            track_id=history_data.track_id
        )

        session.add(history)
        await session.commit()
        await session.refresh(history)
        logger.success(f'Successfully set track history ({history_data.track_id}) from user ({current_user.id})')

    return history

@router.delete('/')
async def delete_history(
    request: Request,
    history_data: HistoryDelete,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    
    result = await session.execute(select(UserHistory).where(
        UserHistory.track_id == history_data.track_id,
        UserHistory.user_id == current_user.id
    ))
    history = result.scalar_one_or_none()

    if not history:
        logger.warning(f'Track history ({history_data.track_id}) from user with {current_user.id} id not found')
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Track history ({history_data.track_id}) from user with {current_user.id} id not found')

    session.delete(history)
    await session.commit()
    logger.success(f'Successfully delete track history ({history_data.track_id}) from user ({current_user.id})')

    return Response(status_code=status.HTTP_204_NO_CONTENT)