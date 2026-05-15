from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.common.scheduler import setup_scheduler, scheduler
from src.common.logger import logger
from src.config import settings
from src.processor.create_superuser import create_superuser
from src.common.s3_utils import set_public_bucket_policy

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

    try:
        await set_public_bucket_policy(bucket_name=settings.MINIO_BUCKET_NAME_CORE)
    except Exception as e:
        logger.error(f'Failed to set PUBLIC policy for {settings.MINIO_BUCKET_NAME_CORE} bucket in MinIO: {e}')

    yield

    logger.info(f'Shutting down application')
    if scheduler.running:
        scheduler.shutdown()
        logger.info(f'Sheduler stopped')