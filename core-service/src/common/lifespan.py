from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.common.scheduler import setup_scheduler, scheduler
from src.common.logger import logger
from src.config import settings
from src.database import async_session_maker
from sqlalchemy import select
from src.models import User
from src.auth.utils import pwd_context
from src.processor.create_superuser import create_superuser

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f'Starting application')

    try:
        setup_scheduler()
    except Exception as e:
        logger.error(f'Failed to start scheduler: {e}')

    try:
        await create_superuser(
            username=settings.SUPERUSER_USERNAME,
            email=settings.SUPERUSER_EMAIL,
            password=settings.SUPERUSER_PASSWORD,
            permission=settings.SUPERUSER_AUTO_CREATE
        )
    except Exception as e:
        logger.error(f'Failed to auto create superuser: {e}')

    yield

    logger.info(f'Shutting down application')
    if scheduler.running:
        scheduler.shutdown()
        logger.info(f'Sheduler stopped')