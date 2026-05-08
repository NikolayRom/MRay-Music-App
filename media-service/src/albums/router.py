from fastapi import APIRouter, Request, Depends, Query, UploadFile, File, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_async_session
from src.models import Artist, Album
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from src.config import settings
from typing import Optional
from src.albums.schemas import *
from src.albums.service import *
from src.albums.utils import *
from src.common.s3_utils import *
from src.common.validators import *

router = APIRouter()

@router.get('/albums', response_model=AlbumsAllRead)
async def get_all_albums(
    request: Request,
    search: Optional[str] = Query(None, min_length=2, description="Search by name. Special characters (e.g., &) must be URL-encoded. Example: 'Rock%20%26%20Roll'"),
    artist_id: Optional[int] = None,
    limit: int = Query(settings.DEFAULT_GET_SIZE, ge=1, le=settings.MAX_GET_SIZE),
    cursor: Optional[int] = Query(None, description='Last album id'),
    session: AsyncSession = Depends(get_async_session)
):
    query = select(Album).options(selectinload(Album.artist), selectinload(Album.tracks))
    if cursor:
        query = query.where(Album.id > cursor)

    if search:
        query = query.where(Album.name.ilike(f'%{search}%'))

    if artist_id:
        query = query.where(Album.artist_id == artist_id)

    query = query.order_by(Album.id).limit(limit+1)
    result = await session.execute(query)
    albums = result.scalars().all()

    has_more = len(albums) > limit
    if has_more:
        albums = albums[:-1]

    next_cursor = albums[-1].id if albums and has_more else None

    return AlbumsAllRead(
        items=albums,
        has_more=has_more,
        next_cursor=next_cursor,
        limit=limit
    )

@router.get('/album/{id}', response_model=AlbumRead)
async def get_album(request: Request, id: int, session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(Album).where(Album.id == id).options(selectinload(Album.artist), selectinload(Album.tracks)))
    album = result.scalar_one_or_none()
    check_object_exist(album)
    return album

@router.post('/album', response_model=AlbumRead)
async def post_album(request: Request, album_data: AlbumPost, file: Optional[UploadFile] = None, session: AsyncSession = Depends(get_async_session)):
    name = album_data.name
    artist_id = album_data.artist_id

    check_object_exist(await session.get(Artist, artist_id))

    album = Album(
        name=name,
        image_key=None,
        artist_id=artist_id
    )

    session.add(album)
    await session.commit()
    await session.refresh(album)

    if file:
        image_key = get_image_key_from_file(key=album.id, file=file)
        try:
            await streaming_minio_data_upload(key=image_key, content_type=file.content_type, file=file)
            album.image_key = image_key
            await session.commit()
            await session.refresh(album)
        except Exception:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Can\'t upload cover for album')
    
    return album

@router.put('/album/{id}', response_model=AlbumRead)
async def put_album(request: Request, album_data: AlbumUpdate, id: int, file: UploadFile = File(..., description='Cover for album'), session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(Album).where(Album.id == id).options(selectinload(Album.artist), selectinload(Album.tracks)))
    album = result.scalar_one_or_none()
    check_object_exist(album)
    
    name = album_data.name
    artist_id = album_data.artist_id
    check_object_exist(await session.get(Artist, artist_id))
    album.name = name
    album.artist_id = artist_id
    
    image_key = get_image_key_from_file(key=album.id, file=file)
    try:
        await streaming_minio_data_upload(key=image_key, content_type=file.content_type, file=file)
        album.image_key = image_key
    except Exception:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Can\'t upload cover for album')
    
    await session.commit()
    await session.refresh(album)
    return album

@router.patch('/album/{id}', response_model=AlbumRead)
async def patch_album(request: Request, id: int, album_data: Optional[AlbumPatch] = None, file: Optional[UploadFile] = None, session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(Album).where(Album.id == id).options(selectinload(Album.artist), selectinload(Album.tracks)))
    album = result.scalar_one_or_none()
    check_object_exist(album)
    
    if album_data:
        if album_data.name:
            album.name = album_data.name
        if album_data.artist_id:
            check_object_exist(await session.get(Artist, album_data.artist_id))
            album.artist_id = album_data.artist_id

    if file:
        image_key = get_image_key_from_file(key=album.id, file=file)
        try:
            await streaming_minio_data_upload(key=image_key, content_type=file.content_type, file=file)
            album.image_key = image_key
        except Exception:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Can\'t upload cover for album')
    
    await session.commit()
    await session.refresh(album)
    return album

@router.delete('/album/{id}', response_model=AlbumRead)
async def delete_album(request: Request, id: int, session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(Album).where(Album.id == id).options(selectinload(Album.tracks)))
    album = result.scalar_one_or_none()
    check_object_exist(album)

    tracks = album.tracks
    image_key = album.image_key

    if image_key:
        try:
            default_minio_data_delete(key=image_key)
        except Exception:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Can\'t delete cover for album')

    if tracks:
        try:
            for track in tracks:
                if track.image_key:
                    await default_minio_data_delete(key=track.image_key)
                await default_minio_data_delete(key=track.s3_key)
        except Exception:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Can\'t delete tracks for artist')
        
    await session.delete(album) 
    await session.commit()

    return album