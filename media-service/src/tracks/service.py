from src.config import settings
from fastapi import UploadFile, File, HTTPException, status, Depends
from typing import List
from src.tracks.utils import get_id3_size
from src.storage.client import s3_storage
from mutagen.id3 import ID3
from mutagen.mp3 import MP3
from io import BytesIO
from datetime import timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_async_session
from src.tracks.utils import get_or_create_album, get_or_create_artist

def check_object_exist(obj):
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Object not found')

def check_file_size(file: UploadFile = File(...)):
    if file.size and file.size > settings.MINIO_MAX_FILE_SIZE:
        raise HTTPException(status_code=status.HTTP_413_CONTENT_TOO_LARGE, detail=f'File {file.filename} is too large')
    
def check_file_format(formats: List[str], file: UploadFile = File(...)):
    if file.filename.rsplit('.', 1)[1] not in formats:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=f'Unsupported media type, expected {formats}')

def check_content_type_format(formats: List[str], file: UploadFile = File(...)):
    if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=f'Unsupported content type format, expected {formats}')

async def get_metadata_size(file: UploadFile = File(...)):
    header = await file.read(10)
    await file.seek(0)
    if header[:3] == b'ID3':
        return min(get_id3_size(header) + 1024*100, settings.MINIO_MAX_FILE_SIZE)
    else:
        return 1024 * 128
    
async def streaming_minio_data_upload(key: str, content_type: str, file: UploadFile = File(...)):
    async with s3_storage.get_client() as s3:
        return await s3.put_object(
            Bucket=s3_storage.bucket_name,
            Key=key,
            Body=file.file,
            ContentType=content_type
        )
    
async def default_minio_data_upload(key: str, body, content_type: str):
    async with s3_storage.get_client() as s3:
        await s3.put_object(
            Bucket=s3_storage.bucket_name,
            Key=key,
            Body=body,
            ContentType=content_type,
        )

async def default_minio_data_delete(key: str):
    async with s3_storage.get_client() as s3:
        await s3.delete_object(
            Bucket=s3_storage.bucket_name,
            Key=key,
        )

def get_track_image_key_from_file(key: str, file: UploadFile = File(...)):
    image_extension = 'jpg' if file.content_type == 'image/jpeg' else 'png'
    return f'{settings.MINIO_COVER_ROOT}/{key}.{image_extension}'

def get_track_image_key_from_metadata(key: str, content_type):
    image_ext = 'jpg' if content_type == 'image/jpeg' else 'png'
    return f'{settings.MINIO_COVER_ROOT}/{key}.{image_ext}'

async def get_track_image_key(key: str, buffer: BytesIO, file: UploadFile | None = None):
    if file:
        check_content_type_format(formats=["image/jpeg", "image/png", "image/jpg"], file=file)
        check_file_size(file=file)

        image_key = get_track_image_key_from_file(key=key, file=file)

        try:
            await streaming_minio_data_upload(key=image_key, content_type=file.content_type, file=file)
        except Exception:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Can\'t upload cover for mp3 track')

    else:

        image_key = None
        tags = ID3(buffer)
        pics = tags.getall('APIC')
        if pics:
            pic = pics[0]
            image_key = get_track_image_key_from_metadata(key=key, content_type=pic.mime)
            try:
                await default_minio_data_upload(key=image_key, body=pic.data, content_type=pic.meme)
            except Exception:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Can\'t upload cover for mp3 track')
    
    return image_key
    
def get_track_title(key: str, audio: MP3, is_seeder: bool = False):
    if is_seeder:
        return str(audio.get('TIT2', key))
    else:
        return str(audio.get('TIT2', key.split('_', 1)[1]))
    
def get_track_duration(audio: MP3):
    return timedelta(seconds=int(audio.info.length))

def get_track_genre(audio: MP3, separators: List[str]):
    genres = audio.get('TCON')
    if not genres:
        genre = ['Unknown']
    else:
        genres = str(genres)
        for sep in separators:
            genres = genres.replace(sep, ' ')
        genre = [g for g in genres.split()] 
    return genre

def get_track_artist_name(audio: MP3):
    return audio.get('TPE1')

def get_track_album_name(audio: MP3):
    return audio.get('TALB')

async def get_track_artist_and_album_id(session: AsyncSession, artist_name: str | None = None, album_name: str | None = None):
    if artist_name:
        artist = await get_or_create_artist(session, str(artist_name))
        if album_name:
            album = await get_or_create_album(session, str(album_name), artist.id)

    artist_id = None if not artist_name else artist.id
    album_id = None if not album_name else album.id
    return (artist_id, album_id)
