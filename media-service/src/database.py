from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from config import settings
from fastapi import FastAPI
from contextlib import asynccontextmanager
from models import Base

engine = create_async_engine(url=settings.POSTGRES_URL)

async_session_maker = async_sessionmaker(engine)

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session

@asynccontextmanager
async def lifespan(app: FastAPI):
    #Redis, MinIO, etc.
    yield