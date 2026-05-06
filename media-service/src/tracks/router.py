from fastapi import APIRouter, HTTPException, status, Request, Depends, UploadFile, File
from fastapi.responses import StreamingResponse
from src.storage.client import s3_storage
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_async_session
from src.models import Track
from src.tracks.schemas import TrackRead, TrackUpdate, TrackPatch
from typing import List
from src.config import settings
from mutagen.mp3 import MP3
import io
from src.tracks.utils import gen_uuid, add_duration_seconds
from src.tracks.service import *

router = APIRouter()

@router.get('/', response_model=List[TrackRead])
async def get_all_tracks(request: Request, session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(Track).options(selectinload(Track.artist), selectinload(Track.album)))
    tracks = result.scalars().all()

    for track in tracks:
        add_duration_seconds(track)

    return tracks

@router.get('/{id}', response_model=TrackRead)
async def get_track(request: Request, id: int, session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(Track).where(Track.id==id).options(selectinload(Track.album), selectinload(Track.artist)))
    track = result.scalar_one_or_none()
    if not track:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    add_duration_seconds(track)
    return track

@router.post('/', response_model=TrackRead)
async def post_track(request: Request, file_track: UploadFile = File(..., description='upload mp3 track'), file_cover: UploadFile | None = None, session: AsyncSession = Depends(get_async_session)):
    
    check_file_size(file=file_track)
    check_file_format(formats=['mp3'], file=file_track)

    file_key = f'{gen_uuid()}_{file_track.filename.rsplit('.', 1)[0]}'

    try:
        
        try:
            read_size = get_metadata_size(file=file_track)
        except Exception:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Can\'t read metadata of mp3 file')
        try:
            streaming_minio_data_upload(key=file_key, content_type='audio/mpeg', file=file_track)
        except Exception:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Can\'t upload object from minio storage')
    
        metadata_content = await file_track.read(read_size)
        await file_track.seek(0)
        buffer = io.BytesIO(metadata_content)
        audio = MP3(buffer)

        try:
            artist_and_album_id = get_track_artist_and_album_id(
                artist_name=get_track_artist_name(audio=audio),
                album_name=get_track_album_name(audio=audio),
                session=session
            )
            artist_id = artist_and_album_id[0]
            album_id = artist_and_album_id[1]

            track = Track(
                title=get_track_title(key=file_key, audio=audio),
                s3_key=file_key,
                image_key=get_track_image_key(key=file_key, buffer=buffer, file=file_cover),
                duration=get_track_duration(audio=audio),
                artist_id=artist_id,
                album_id=album_id,
                genre=get_track_genre(audio=audio, separators=[',', '&']),
            )
        except:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Can\'t read metadata from mp3 file')

        session.add(track)
        print('Successful track commit')
        await session.commit()

        add_duration_seconds(track)
        return track

    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Can\'t upload this mp3 file')

@router.put('/{track_id}', response_model=TrackRead)
async def put_track(request: Request, track_id: int, track_data: TrackUpdate, file: UploadFile = File(..., description='upload cover for mp3 track'), session: AsyncSession = Depends(get_async_session)):
    track = await session.get(Track, track_id)

    if not track:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Track not found')
    
    if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail='Only jpeg, jpg and png formats available')

    try:

        check_file_size(file=file)

        image_ext = 'jpg' if file.content_type == 'image/jpeg' else 'png'
        image_key = f'{settings.MINIO_COVER_ROOT}/{track.s3_key}.{image_ext}'

        async with s3_storage.get_client() as s3:
            if track.image_key:
                await s3.delete_object(
                    Bucket=s3_storage.bucket_name,
                    Key=track.image_key,
                )
            
            await s3.put_object(
                Bucket=s3_storage.bucket_name,
                Key=image_key,
                Body=file.file,
                ContentType=file.content_type
            )

            track.image_key = image_key

    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Can\'t upload cover for mp3 track')

    try:
        track.title = track_data.title
        track.artist_id = track.artist_id if not track_data.artist_id else track_data.artist_id
        track.album_id = track.album_id if not track_data.album_id else track_data.album_id
        track.genre = track_data.genre
    
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid parameters for track')
    
    await session.commit()
    await session.refresh(track)

    add_duration_seconds(track)
    return track

@router.patch('/{track_id}', response_model=TrackRead)
async def patch_track(request: Request, track_id: int, track_data: TrackPatch, file: UploadFile | None = None, session: AsyncSession = Depends(get_async_session)):
    track = await session.get(Track, track_id)

    if not track:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Track not found')
    
    if file:

        if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
                raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail='Only jpeg, jpg and png formats available')

        try:

            check_file_size(file=file)

            image_ext = 'jpg' if file.content_type == 'image/jpeg' else 'png'
            image_key = f'{settings.MINIO_COVER_ROOT}/{track.s3_key}.{image_ext}'

            async with s3_storage.get_client() as s3:
                if track.image_key:
                    await s3.delete_object(
                        Bucket=s3_storage.bucket_name,
                        Key=track.image_key,
                    )
                
                await s3.put_object(
                    Bucket=s3_storage.bucket_name,
                    Key=image_key,
                    Body=file.file,
                    ContentType=file.content_type
                )

                track.image_key = image_key

        except Exception:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Can\'t upload cover for mp3 track')

    try:

        for key, value in track_data.model_dump(exclude_unset=True).items():
            setattr(track, key, value)
    
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid parameters for track')
    
    await session.commit()
    await session.refresh(track)

    add_duration_seconds(track)
    return track

@router.delete('/{track_id}', response_model=TrackRead)
async def delete_track(request: Request, track_id: int, session: AsyncSession = Depends(get_async_session)):
    track = await session.get(Track, track_id)

    if not track:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Track not found')
    
    async with s3_storage.get_client() as s3:

        if track.image_key:
            await s3.delete_object(
                Bucket=s3_storage.bucket_name,
                Key=track.image_key,
            )

        s3_obj = await s3.delete_object(
            Bucket=s3_storage.bucket_name,
            Key=track.s3_key,
        )
        await session.execute(delete(Track).where(Track.id==track_id))
    
    add_duration_seconds(track)
    return track

@router.get('/stream/{track_id}', response_class=StreamingResponse)
async def stream_from_minio(request: Request, track_id: int, session: AsyncSession = Depends(get_async_session)) -> StreamingResponse:
    range_header = request.headers.get("range")

    track = await session.get(Track, track_id)
    
    if not track:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Track not found')
 
    s3_client = await s3_storage.get_client().__aenter__()

    try:
        kwargs = {"Bucket": s3_storage.bucket_name, "Key": track.s3_key}
        if range_header:
            kwargs["Range"] = range_header

        s3_response = await s3_client.get_object(**kwargs)
        
        res_headers = {
            "Content-Type": s3_response.get("ContentType", "audio/mpeg"),
            "Accept-Ranges": "bytes",
            "Content-Length": str(s3_response["ContentLength"]),
        }
        
        if "ContentRange" in s3_response:
            res_headers["Content-Range"] = s3_response["ContentRange"]
        
        status_code = status.HTTP_206_PARTIAL_CONTENT if range_header else status.HTTP_200_OK

        async def body_iterator():
            try:
                async for chunk in s3_response["Body"]:
                    yield chunk
            finally:
                s3_response["Body"].close()
                await s3_client.__aexit__(None, None, None)

        return StreamingResponse(
            body_iterator(),
            status_code=status_code,
            headers=res_headers
        )

    except Exception as e:
        await s3_client.__aexit__(None, None, None)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Can\'t stream this mp3 file')