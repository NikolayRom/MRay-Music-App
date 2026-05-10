from mutagen.mp3 import MP3
import io
import asyncio
from sqlalchemy import select
from src.models import *
from src.database import async_session_maker
from src.storage.client import s3_storage
from src.config import settings
from src.tracks.service import *
from src.common.logger import logger

async def seed_music():
    async with s3_storage.get_client() as s3:
        response = await s3.list_objects_v2(Bucket=s3_storage.bucket_name)
        if 'Contents' not in response:
            logger.warning(f'SEEDER: No tracks in {s3_storage.bucket_name} from S3 storage are found')
            return
        
        async with async_session_maker() as session:
        
            for obj in response['Contents']:
                try:
                    file_key = obj['Key']
                    if not file_key.endswith('.mp3') or f'{settings.MINIO_COVER_ROOT}' in file_key:
                        logger.warning(f'SEEDER: Found {file_key}, expected .mp3 track, skip object')
                        continue

                    existing_track = await session.execute(select(Track).where(Track.s3_key==file_key))
                    if existing_track.scalar_one_or_none():
                        logger.warning(f'SEEDER: Track {existing_track} already exist')
                        continue

                    s3_obj = await s3.get_object(
                        Bucket=s3_storage.bucket_name,
                        Key=file_key,
                        Range='bytes=0-26214400'
                    )

                    raw_data = await s3_obj['Body'].read()
                    buffer = io.BytesIO(raw_data)
                    audio = MP3(buffer)
                    buffer.seek(0)
                    
                    artist_and_album_id = await get_track_artist_and_album_id(
                        artist_name=get_track_artist_name(audio=audio),
                        album_name=get_track_album_name(audio=audio),
                        session=session
                    )
                    artist_id = artist_and_album_id[0]
                    album_id = artist_and_album_id[1]

                    track = Track(
                        title=get_track_title(key=file_key, audio=audio, is_seeder=True),
                        s3_key=file_key,
                        image_key=await get_track_image_key(key=file_key, buffer=buffer),
                        duration=get_track_duration(audio=audio),
                        artist_id=artist_id,
                        album_id=album_id,
                        genre=get_track_genre(audio=audio, separators=[',', '&']),
                    )
                    logger.success(f'SEEDER: Successful creation of new {track} track')
                    session.add(track)
                    logger.info(f'SEEDER: Add new {track} track')
                except Exception as e:
                    logger.error(f'SEEDER: Error, while trying to download track: {e}')
                    continue

            await session.commit()
            logger.success(f'SEEDER: Successful end of initialize, save all tracks')

if __name__  == '__main__':
    asyncio.run(seed_music())

