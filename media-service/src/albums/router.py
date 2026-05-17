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
from src.common.logger import logger
from src.common.rbac import CurrentUser, get_current_superuser, get_current_user

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

    if not albums:
        logger.warning(f'Albums with selected parameters (limit:{limit}, cursor:{cursor}, search:{search}, artist_id:{artist_id} not found')

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
async def post_album(
    request: Request,
    album_data: AlbumPost = Depends(album_post_form),
    file: Optional[UploadFile] = None,
    session: AsyncSession = Depends(get_async_session),
    user: CurrentUser = Depends(get_current_superuser)
):
    name = album_data.name
    artist_id = album_data.artist_id

    check_object_exist(await session.get(Artist, artist_id))

    album = Album(
        name=name,
        image_key=None,
        artist_id=artist_id
    )
    logger.success(f'Successful creation of new album {album}')

    session.add(album)
    await session.commit()
    await session.refresh(album)
    logger.info(f'Save new album {album} by {artist_id} artist id with {album.id} id')

    if file:
        image_key = get_image_key_from_file(key=album.id, file=file)
        try:
            await streaming_minio_data_upload(key=image_key, content_type=file.content_type, file=file, is_public=True)
            album.image_key = image_key
            await session.commit()
            await session.refresh(album)
        except Exception:
            logger.error('Can\'t upload cover for album')
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Can\'t upload cover for album')
    
    return album

@router.put('/album/{id}', response_model=AlbumRead)
async def put_album(
    request: Request,
    id: int,
    album_data: AlbumUpdate = Depends(album_update_form),
    file: UploadFile = File(..., description='Cover for album'),
    session: AsyncSession = Depends(get_async_session),
    user: CurrentUser = Depends(get_current_superuser)
):
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
        await streaming_minio_data_upload(key=image_key, content_type=file.content_type, file=file, is_public=True)
        album.image_key = image_key
    except Exception:
        logger.error('Can\'t upload cover for album')
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Can\'t upload cover for album')
    
    logger.success(f'Successful update {album} album with {album.id} id')
    await session.commit()
    await session.refresh(album)
    logger.info(f'Save updated {album} album with {album.id} id')
    return album

@router.patch('/album/{id}', response_model=AlbumRead)
async def patch_album(
    request: Request,
    id: int,
    album_data: AlbumPatch = Depends(album_patch_form),
    file: Optional[UploadFile] = None,
    session: AsyncSession = Depends(get_async_session),
    user: CurrentUser = Depends(get_current_superuser)
):
    result = await session.execute(select(Album).where(Album.id == id).options(selectinload(Album.artist), selectinload(Album.tracks)))
    album = result.scalar_one_or_none()
    check_object_exist(album)
    
    if album_data.name:
        album.name = album_data.name
    if album_data.artist_id:
        check_object_exist(await session.get(Artist, album_data.artist_id))
        album.artist_id = album_data.artist_id

    if file:
        image_key = get_image_key_from_file(key=album.id, file=file)
        try:
            await streaming_minio_data_upload(key=image_key, content_type=file.content_type, file=file, is_public=True)
            album.image_key = image_key
        except Exception:
            logger.error('Can\'t upload cover for album')
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Can\'t upload cover for album')

    logger.success(f'Successful patch {album} album with {album.id} id')    
    await session.commit()
    await session.refresh(album)
    logger.info(f'Save updated {album} album with {album.id} id')
    return album

@router.delete('/album/{id}', response_model=AlbumRead)
async def delete_album(
    request: Request,
    id: int,
    session: AsyncSession = Depends(get_async_session),
    user: CurrentUser = Depends(get_current_superuser)
):
    result = await session.execute(select(Album).where(Album.id == id).options(selectinload(Album.tracks)))
    album = result.scalar_one_or_none()
    check_object_exist(album)

    tracks = album.tracks
    image_key = album.image_key

    if image_key:
        try:
            await default_minio_data_delete(key=image_key, is_public=True)
        except Exception:
            logger.error('Can\'t delete cover for album')
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Can\'t delete cover for album')

    if tracks:
        try:
            for track in tracks:
                if track.image_key:
                    await default_minio_data_delete(key=track.image_key, is_public=True)
                await default_minio_data_delete(key=track.s3_key)
        except Exception:
            logger.error('Can\'t delete tracks for artist')
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Can\'t delete tracks for artist')
        
    session.delete(album) 
    await session.commit()
    logger.success(f'Successful delete {album} album with {album.id} id')

    return album