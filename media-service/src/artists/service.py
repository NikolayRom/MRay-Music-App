from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models import Artist
from src.common.logger import logger
from src.artists.schemas import ArtistPatch, ArtistPost, ArtistUpdate
from fastapi import Form
from typing import Optional

async def check_unique_artist_name(name: str, session: AsyncSession) -> bool:
    result = await session.execute(select(Artist).where(Artist.name == name))
    if result.scalar_one_or_none():
        logger.warning(f'Artist with {name} name already exist')
        return False
    return True

def artist_post_form(
    name: str = Form(...) 
) -> ArtistPost:
    return ArtistPost(name=name)

def artist_update_form(
    name: str = Form(...)
) -> ArtistUpdate:
    return ArtistUpdate(name=name)

def artist_patch_form(
    name: Optional[str] = Form(None)  
) -> ArtistPatch:
    return ArtistPatch(name=name)