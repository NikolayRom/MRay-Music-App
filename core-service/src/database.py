from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from src.config import settings
from src.common.logger import logger

engine = create_async_engine(url=settings.POSTGRES_URL_CORE)

async_session_maker = async_sessionmaker(engine)

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        logger.info(f'Get async session: {session.info}')
        yield session