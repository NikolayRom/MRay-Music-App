from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.common.logger import logger
from src.config import settings
from src.common.s3_utils import set_public_bucket_policy

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f'Starting application')

    try:
        await set_public_bucket_policy(bucket_name=settings.MINIO_BUCKET_NAME_MEDIA_ASSETS)
    except Exception as e:
        logger.error(f'Failed to set PUBLIC policy for {settings.MINIO_BUCKET_NAME_MEDIA_ASSETS} bucket in MinIO: {e}')

    yield

    logger.info(f'Shutting down application')