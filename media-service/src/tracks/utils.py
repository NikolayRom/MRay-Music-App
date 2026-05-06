import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import select
from src.models import Artist, Album

def gen_uuid():
    return str(uuid.uuid4().hex)

def get_id3_size(header_bytes: bytes) -> int:
    size = (header_bytes[9] & 0x7f) | \
           ((header_bytes[8] & 0x7f) << 7) | \
           ((header_bytes[7] & 0x7f) << 14) | \
           ((header_bytes[6] & 0x7f) << 21)
    return size + 10

def add_duration_seconds(sql_model):
    setattr(sql_model, 'duration_seconds', int(sql_model.duration.total_seconds()))

async def get_or_create_artist(session: AsyncSession, name: str):
    result = await session.execute(select(Artist).where(Artist.name==name))
    artist = result.scalar_one_or_none()

    if not artist:
        artist = Artist(name=name)
        session.add(artist)
        await session.flush()
        print('Successful artist commit')
    return artist

async def get_or_create_album(session: AsyncSession, name: str, artist_id: int):
    result = await session.execute(select(Album).where(Album.name==name, Album.artist_id==artist_id))
    album = result.scalar_one_or_none()

    if not album:
        album = Album(name=name, artist_id=artist_id)
        session.add(album)
        await session.flush()
        print('Successful album commit')
    return album