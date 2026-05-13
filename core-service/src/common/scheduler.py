from datetime import datetime, timedelta, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import delete
from src.models import RefreshToken
from src.database import async_session_maker
from src.common.logger import logger
from src.config import settings

scheduler = AsyncIOScheduler()

async def clean_up_expired_tokens():
    async with async_session_maker() as session:
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=settings.INACTIVE_REFRESH_TOKEN_LIFETIME_DAYS)
            result = await session.execute(delete(RefreshToken).where(RefreshToken.exp < cutoff_date))
            await session.commit()

            deleted_count = result.rowcount
            if deleted_count > 0:
                logger.success(f'Cleaned up {deleted_count} expired refresh tokens')
            else:
                logger.info(f'No expired refresh tokens to clean up')

        except Exception as e:
            logger.error(f'Failed to clean up expired refresh tokens: {e}')
            await session.rollback()

def setup_scheduler():
    scheduler.add_job(
        func=clean_up_expired_tokens,
        trigger=IntervalTrigger(hours=24),
        id='clean_up_expired_tokens',
        replace_existing=True
    )
    scheduler.start()
    logger.info(f'Scheduler started with clean up job')