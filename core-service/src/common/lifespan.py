from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.common.scheduler import setup_scheduler, scheduler
from src.common.logger import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f'Starting application')

    try:
        setup_scheduler()
    except Exception as e:
        logger.error(f'Failed to start scheduler: {e}')

    yield

    logger.info(f'Shutting down application')
    if scheduler.running:
        scheduler.shutdown()
        logger.info(f'Sheduler stopped')