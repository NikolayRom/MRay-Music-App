from src.config import settings
from fastapi import UploadFile, File, HTTPException, status, Form
from typing import List, Optional
from src.storage.client import s3_storage
from src.models import Album, Artist
from mutagen.id3 import ID3
from mutagen.mp3 import MP3
from io import BytesIO
from datetime import timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.tracks.utils import get_or_create_album, get_or_create_artist, get_id3_size
from src.common.s3_utils import *
from src.common.validators import *
from src.common.logger import logger
from src.tracks.schemas import TrackPost, TrackUpdate, TrackPatch

def check_file_size(file: UploadFile = File(...)):
    if file.size and file.size > settings.MINIO_MAX_FILE_SIZE:
        logger.error(f'File {file.filename} size is too large: {file.size} (max: {settings.MINIO_MAX_FILE_SIZE})')
        raise HTTPException(status_code=status.HTTP_413_CONTENT_TOO_LARGE, detail=f'File {file.filename} is too large')
    
def check_file_format(formats: List[str], file: UploadFile = File(...)):
    if file.filename.rsplit('.', 1)[1] not in formats:
        logger.error(f'Unsupported media type, expected {formats}')
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=f'Unsupported media type, expected {formats}')

def check_content_type_format(formats: List[str], file: UploadFile = File(...)):
    if file.content_type not in formats:
        logger.error(f'Unsupported content type format, expected {formats}')
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=f'Unsupported content type format, expected {formats}')

async def check_artist_and_album_id_for_track(session: AsyncSession, artist_id: Optional[int] = None, album_id: Optional[int] = None) -> None:
    if artist_id:
        check_object_exist(await session.get(Artist, artist_id))

    if album_id:
        check_object_exist(await session.get(Album, album_id))

    if album_id and not artist_id:
        logger.error(f'Album id {album_id} can\'t be selected without artist id')
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Album id can\'t be selected without artist id')

    if album_id and artist_id:
        result = await session.execute(select(Album).where(Album.artist_id == artist_id))
        album = result.scalar_one_or_none()
        if not album:
            logger.error(f'Album {album_id} with {artist_id} artist id doesn\'t exist')
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Album with {artist_id} artist id doesn\'t exist')

async def get_metadata_size(file: UploadFile = File(...)):
    header = await file.read(10)
    await file.seek(0)
    if header[:3] == b'ID3':
        return min(get_id3_size(header) + 1024*100, settings.MINIO_MAX_FILE_SIZE)
    else:
        logger.warning(f'ID3 tag not found, return default {1024*128} metadata size')
        return 1024 * 128
    
async def default_minio_data_upload(key: str, body, content_type: str):
    try:
        async with s3_storage.get_client() as s3:
            await s3.put_object(
                Bucket=s3_storage.bucket_name,
                Key=key,
                Body=body,
                ContentType=content_type,
            )
        logger.success('Successfull file uploading')
    except Exception as e:
        logger.error(f'Error: {e}, while trying to upload file')
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Error: {e}, while trying to upload file')

def get_track_image_key_from_metadata(key: str, content_type):
    image_ext = 'jpg' if content_type == 'image/jpeg' else 'png'
    return f'{settings.MINIO_COVER_ROOT}/{key}.{image_ext}'

async def get_track_image_key(key: str, buffer: BytesIO, file: UploadFile | None = None):
    if file:
        check_content_type_format(formats=["image/jpeg", "image/png", "image/jpg"], file=file)
        check_file_size(file=file)

        image_key = get_image_key_from_file(key=key, file=file)

        try:
            await streaming_minio_data_upload(key=image_key, content_type=file.content_type, file=file)
            logger.success(f'Successful mp3 cover uploading {file.filename} with {image_key} key')
        except Exception:
            logger.error(f'Error, while trying to upload {file.filename} cover with {image_key} key for mp3 track')
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Can\'t upload cover for mp3 track')

    else:

        image_key = None
        tags = ID3(buffer)
        pics = tags.getall('APIC')
        if pics:
            pic = pics[0]
            image_key = get_track_image_key_from_metadata(key=key, content_type=pic.mime)
            try:
                await default_minio_data_upload(key=image_key, body=pic.data, content_type=pic.mime)
                logger.success(f'Successful mp3 cover uploading from metadata with {image_key} key')
            except Exception:
                logger.error(f'Error, while trying to upload from metadata cover with {image_key} key for mp3 track')
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Can\'t upload cover for mp3 track')
        else:
            logger.info('Cover from metadata not found, return None')

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
    try:
        if artist_name:
            artist = await get_or_create_artist(session, str(artist_name))
            logger.success(f'Successful creation or get artist {artist}')
            if album_name:
                album = await get_or_create_album(session, str(album_name), artist.id)
                logger.success(f'Successful creation or get album {album}')

        artist_id = None if not artist_name else artist.id
        album_id = None if not album_name else album.id
        logger.info(f'Return {artist_id} artist and {album_id} album')
        return (artist_id, album_id)
    except Exception as e:
        logger.error(f'Error {e}, while trying get or create artist {artist_name} or album {album_name}')
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Error {e}, while trying get or create artist {artist_name} or album {album_name}')
    
def track_post_form(
    title: Optional[str] = Form(None),
    artist_id: Optional[int] = Form(None),
    album_id: Optional[int] = Form(None),
    genre: Optional[List[str]] = Form(None) 
) -> TrackPost:
    return TrackPost(title=title, artist_id=artist_id, album_id=album_id, genre=genre)

def track_update_form(
    title: str = Form(...),
    artist_id: int = Form(...),
    album_id: int = Form(...),
    genre: List[str] = Form(...)  
) -> TrackUpdate:
    return TrackUpdate(title=title, artist_id=artist_id, album_id=album_id, genre=genre)

def track_patch_form(
    title: Optional[str] = Form(None),
    artist_id: Optional[int] = Form(None),
    album_id: Optional[int] = Form(None),
    genre: Optional[List[str]] = Form(None)  
) -> TrackPatch:
    return TrackPatch(title=title, artist_id=artist_id, album_id=album_id, genre=genre)