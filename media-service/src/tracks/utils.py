import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.models import Artist, Album
from src.common.logger import logger

def get_id3_size(header_bytes: bytes) -> int:
    size = (header_bytes[9] & 0x7f) | \
           ((header_bytes[8] & 0x7f) << 7) | \
           ((header_bytes[7] & 0x7f) << 14) | \
           ((header_bytes[6] & 0x7f) << 21)
    logger.info(f'Get id3 metadata size, return {size + 10}')
    return size + 10

async def get_or_create_artist(session: AsyncSession, name: str):
    result = await session.execute(select(Artist).where(Artist.name==name))
    artist = result.scalar_one_or_none()

    if not artist:
        artist = Artist(name=name)
        session.add(artist)
        await session.flush()
        logger.info(f'Create and save artist {artist} with {artist.id} id')
    else:
        logger.info(f'Get artist {artist} with {artist.id} id')
    return artist

async def get_or_create_album(session: AsyncSession, name: str, artist_id: int):
    result = await session.execute(select(Album).where(Album.name==name, Album.artist_id==artist_id))
    album = result.scalar_one_or_none()

    if not album:
        album = Album(name=name, artist_id=artist_id)
        session.add(album)
        await session.flush()
        logger.info(f'Create and save album {album} with {album.id} id')
    else:
        logger.info(f'Get album {album} with {album.id} id')
    return album