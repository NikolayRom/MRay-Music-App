from fastapi import APIRouter, HTTPException, status, Request, Depends, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from src.storage.client import s3_storage
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_async_session
from src.models import Track
from src.tracks.schemas import TrackRead, TrackPost, TrackUpdate, TrackPatch, TracksAllRead
from typing import List, Optional
from mutagen.mp3 import MP3
import io
from src.tracks.utils import gen_uuid
from src.tracks.service import *
from src.common.s3_utils import *
from src.common.validators import *
from src.common.logger import logger

router = APIRouter()

@router.get('/tracks', response_model=TracksAllRead)
async def get_all_tracks(
    request: Request,
    search: Optional[str] = Query(None, min_length=2, description="Search by title. Special characters (e.g., &) must be URL-encoded. Example: 'Rock%20%26%20Roll'"),
    genre: Optional[List[str]] = Query(None),
    artist_id: Optional[int] = None,
    album_id: Optional[int] = None,
    limit: int = Query(settings.DEFAULT_GET_SIZE, ge=1, le=settings.MAX_GET_SIZE),
    cursor: Optional[int] = Query(None, description='Last track id'),
    session: AsyncSession = Depends(get_async_session)
):

    query = select(Track).options(selectinload(Track.artist), selectinload(Track.album))
    if cursor:
        query = query.where(Track.id > cursor)

    if search:
        query = query.where(Track.title.ilike(f'%{search}%'))

    if artist_id:
        query = query.where(Track.artist_id == artist_id)
    if album_id:
        query = query.where(Track.album_id == album_id)

    if genre:
        query = query.where(Track.genre.op('&&')(genre))

    query = query.order_by(Track.id).limit(limit+1)

    result = await session.execute(query)
    tracks = result.scalars().all()

    if not tracks:
        logger.warning(f'Tracks with selected parameters (limit:{limit}, cursor:{cursor}, search:{search}, artist_id:{artist_id}, album_id:{album_id}, genre:{genre}) not found')

    has_more = len(tracks) > limit
    if has_more:
        tracks = tracks[:-1]

    next_cursor = tracks[-1].id if tracks and has_more else None

    return TracksAllRead(
        items=tracks,
        has_more=has_more,
        next_cursor=next_cursor,
        limit=limit
    )

@router.get('/track/{id}', response_model=TrackRead)
async def get_track(request: Request, id: int, session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(Track).where(Track.id==id).options(selectinload(Track.album), selectinload(Track.artist)))
    track = result.scalar_one_or_none()
    check_object_exist(track)
    return track

@router.post('/track', response_model=TrackRead)
async def post_track(
    request: Request,
    track_data: TrackPost = Depends(track_post_form), 
    file_track: UploadFile = File(..., description='upload mp3 track'),
    file_cover: Optional[UploadFile] = None,
    session: AsyncSession = Depends(get_async_session)
):
    
    check_file_size(file=file_track)
    check_file_format(formats=['mp3'], file=file_track)

    await check_artist_and_album_id_for_track(artist_id=track_data.artist_id, album_id=track_data.album_id, session=session)

    file_key = f'{gen_uuid()}_{file_track.filename.rsplit('.', 1)[0]}'

    try:
        
        try:
            read_size = await get_metadata_size(file=file_track)
        except Exception as e:
            logger.error(f'Can\'t read metadata of mp3 file: {e}')
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Can\'t read metadata of mp3 file: {e}')
        try:
            await streaming_minio_data_upload(key=file_key, content_type='audio/mpeg', file=file_track)
        except Exception as e:
            logger.error(f'Can\'t upload object from minio storage: {e}')
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Can\'t upload object from minio storage: {e}')
    
        metadata_content = await file_track.read(read_size)
        await file_track.seek(0)
        buffer = io.BytesIO(metadata_content)
        audio = MP3(buffer)

        try:
            artist_and_album_id = await get_track_artist_and_album_id(
                artist_name=get_track_artist_name(audio=audio) if not track_data.artist_id else None,
                album_name=get_track_album_name(audio=audio) if not track_data.album_id else None,
                session=session
            )

            track = Track(
                title=get_track_title(key=file_key, audio=audio) if not track_data.title else track_data.title,
                s3_key=file_key,
                image_key=await get_track_image_key(key=file_key, buffer=buffer, file=file_cover),
                duration=get_track_duration(audio=audio),
                artist_id=artist_and_album_id[0] if not track_data.artist_id else track_data.artist_id,
                album_id=artist_and_album_id[1] if not track_data.album_id else track_data.album_id,
                genre=get_track_genre(audio=audio, separators=[',', '&']) if not track_data.genre else track_data.genre,
            )
            logger.success(f'Successful creation of new track: {track}')
        except Exception as e:
            logger.error(f'Can\'t read metadata from mp3 file: {e}')
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Can\'t read metadata from mp3 file: {e}')

        session.add(track)
        logger.success(f'Successful track commit')
        await session.commit()
        await session.refresh(track, ['artist', 'album'])
        logger.info(f'Save new track with {track.id} id')

        return track

    except Exception as e:
        logger.error(f'Can\'t upload this mp3 file: {e}')
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Can\'t upload this mp3 file: {e}')

@router.put('/track/{track_id}', response_model=TrackRead)
async def put_track(
    request: Request,
    track_id: int,
    track_data: TrackUpdate = Depends(track_update_form),
    file: UploadFile = File(..., description='upload cover for mp3 track'),
    session: AsyncSession = Depends(get_async_session)
):
    track = await session.get(Track, track_id)
    check_object_exist(track)
    check_content_type_format(formats=["image/jpeg", "image/png", "image/jpg"], file=file)
    
    await check_artist_and_album_id_for_track(artist_id=track_data.artist_id, album_id=track_data.album_id, session=session)

    try:

        check_file_size(file=file)
        image_key = get_image_key_from_file(key=track.s3_key, file=file)

        if track.image_key:
            await default_minio_data_delete(key=track.image_key)
            
        await streaming_minio_data_upload(key=image_key, content_type=file.content_type, file=file)
        track.image_key = image_key

    except Exception:
        logger.error('Can\'t upload cover for mp3 track')
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Can\'t upload cover for mp3 track')

    try:
        track.title = track_data.title
        track.artist_id = track_data.artist_id
        track.album_id = track_data.album_id
        track.genre = track_data.genre
        logger.success(f'Successful update for track {track} with {track.id} id')
    except Exception:
        logger.error('Invalid parameters for track')
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid parameters for track')
    
    await session.commit()
    await session.refresh(track, ['artist', 'album'])
    logger.info(f'Save updated track {track} with {track.id} id')
    return track

@router.patch('/track/{track_id}', response_model=TrackRead)
async def patch_track(
    request: Request,
    track_id: int,
    track_data: TrackPatch = Depends(track_patch_form),
    file: UploadFile | None = None,
    session: AsyncSession = Depends(get_async_session)
):
    track = await session.get(Track, track_id)
    check_object_exist(track)
    await check_artist_and_album_id_for_track(session=session, artist_id=track_data.artist_id, album_id=track_data.album_id)
    if file:

        check_content_type_format(formats=["image/jpeg", "image/png", "image/jpg"], file=file)
        try:

            check_file_size(file=file)
            image_key = get_image_key_from_file(key=track.s3_key, file=file)

            if track.image_key:
                await default_minio_data_delete(key=track.image_key)
                
            await streaming_minio_data_upload(key=image_key, content_type=file.content_type, file=file)
            track.image_key = image_key

        except Exception:
            logger.error('Can\'t upload cover for mp3 track')
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Can\'t upload cover for mp3 track')

    try:

        for key, value in track_data.model_dump(exclude_unset=True, exclude_none=True).items():
            setattr(track, key, value)
        logger.success(f'Successful patch for track {track} with {track.id} id')
    except Exception:
        logger.error('Invalid parameters for track')
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid parameters for track')
    
    await session.commit()
    await session.refresh(track, ['artist', 'album'])
    logger.info(f'Save updated track {track} with {track.id} id')
    return track

@router.delete('/track/{track_id}', response_model=TrackRead)
async def delete_track(request: Request, track_id: int, session: AsyncSession = Depends(get_async_session)):
    track = await session.get(Track, track_id)

    check_object_exist(track)
    if track.image_key:
        await default_minio_data_delete(key=track.image_key)
    await default_minio_data_delete(key=track.s3_key)
    await session.delete(track)
    await session.commit()
    logger.success(f'Successful delete track {track} with {track.id} id')
    return track

@router.get('/stream/{track_id}', response_class=StreamingResponse)
async def stream_from_minio(request: Request, track_id: int, session: AsyncSession = Depends(get_async_session)) -> StreamingResponse:
    range_header = request.headers.get("range")
    track = await session.get(Track, track_id)
    check_object_exist(track)
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
                logger.success(f'Successful streaming end of track {track_id}')
            finally:
                s3_response["Body"].close()
                await s3_client.__aexit__(None, None, None)
                logger.info(f'End streaming track {track_id}')

        return StreamingResponse(
            body_iterator(),
            status_code=status_code,
            headers=res_headers
        )

    except Exception as e:
        await s3_client.__aexit__(None, None, None)
        logger.error(f'Can\'t stream this mp3 file {track_id}')
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Can\'t stream this mp3 file')