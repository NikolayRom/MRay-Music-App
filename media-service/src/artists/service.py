from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models import Artist

async def check_unique_artist_name(name: str, session: AsyncSession) -> bool:
    result = await session.execute(select(Artist).where(Artist.name == name))
    if result.scalar_one_or_none():
        return False
    return True