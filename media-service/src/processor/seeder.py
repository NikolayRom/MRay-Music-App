from mutagen.mp3 import MP3
from mutagen.id3 import ID3
import io
import asyncio
from datetime import timedelta
from sqlalchemy import select
from src.models import *
from src.database import async_session_maker
from src.storage.client import s3_storage
from src.config import settings
from src.tracks.utils import get_or_create_album, get_or_create_artist

async def seed_music():
    async with s3_storage.get_client() as s3:
        response = await s3.list_objects_v2(Bucket=s3_storage.bucket_name)
        if 'Contents' not in response:
            return
        
        async with async_session_maker() as session:
        
            for obj in response['Contents']:
                file_key = obj['Key']
                if not file_key.endswith('.mp3') or f'{settings.MINIO_COVER_ROOT}' in file_key:
                    continue

                existing_track = await session.execute(select(Track).where(Track.s3_key==file_key))
                if existing_track.scalar_one_or_none():
                    print(f'Track Already exist')
                    continue

                s3_obj = await s3.get_object(
                    Bucket=s3_storage.bucket_name,
                    Key=file_key,
                    Range='bytes=0-26214400'
                )

                raw_data = await s3_obj['Body'].read()
                buffer = io.BytesIO(raw_data)
                try:
                    audio = MP3(buffer)

                    title = str(audio.get('TIT2', file_key))
                    artist_name = audio.get('TPE1')
                    album_name = audio.get('TALB')
                    duration = timedelta(seconds=int(audio.info.length))
                    genres = audio.get('TCON')
                    if not genres:
                        genre = ['Unknown']
                    else:
                        genres = str(genres)
                        for sep in [',', '&']:
                            genres = genres.replace(sep, ' ')
                    
                        genre = [g for g in genres.split()]

                    image_key = None
                    tags = ID3(io.BytesIO(raw_data))
                    pics = tags.getall('APIC')
                    if pics:
                        pic = pics[0]
                        image_data = pic.data
                        image_ext = 'jpg' if pic.mime == 'image/jpeg' else 'png'
                        image_key = f'{settings.MINIO_COVER_ROOT}/{file_key.rsplit('.', 1)[0]}.{image_ext}'

                        await s3.put_object(
                            Bucket=s3_storage.bucket_name,
                            Key=image_key,
                            Body=image_data,
                            ContentType=pic.mime,
                        )

                except Exception as e:
                    print('Invalid tags')
                    continue
                
                if artist_name:
                    artist = await get_or_create_artist(session, str(artist_name))
                    if album_name:
                        album = await get_or_create_album(session, str(album_name), artist.id)

                artist_id = None if not artist_name else artist.id
                album_id = None if not album_name else album.id

                track = Track(
                    title=title,
                    s3_key=file_key,
                    image_key=image_key,
                    duration=duration,
                    artist_id=artist_id,
                    album_id=album_id,
                    genre=genre,
                )
                session.add(track)
                print('Successful track commit')

            await session.commit()
            print('End of initialize')

if __name__  == '__main__':
    asyncio.run(seed_music())

