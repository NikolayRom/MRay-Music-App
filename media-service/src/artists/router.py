from fastapi import APIRouter, Request, Depends, Query, UploadFile, File, HTTPException, status, Response
from src.artists.schemas import ArtistRead, ArtistsAllRead, ArtistPost, ArtistUpdate, ArtistPatch
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_async_session
from src.models import Artist
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from src.config import settings
from typing import Optional
from src.artists.service import *
from src.artists.utils import *
from src.common.s3_utils import *
from src.common.validators import *
from src.common.logger import logger
from src.common.rbac import CurrentUser, get_current_superuser, get_current_user
from src.schemas.common import ArtistShortRead
from src.common.image_utils import get_file_full, get_file_key

router = APIRouter()

@router.get('/artists', response_model=ArtistsAllRead)
async def get_all_artists(
    request: Request,
    search: Optional[str] = Query(None, min_length=2, description="Search by name. Special characters (e.g., &) must be URL-encoded. Example: 'Rock%20%26%20Roll'"),
    limit: int = Query(settings.DEFAULT_GET_SIZE, ge=1, le=settings.MAX_GET_SIZE),
    cursor: Optional[int] = Query(None, description='Last artist id'),
    session: AsyncSession = Depends(get_async_session)
):
    query = select(Artist).options(selectinload(Artist.albums), selectinload(Artist.tracks))
    if cursor:
        query = query.where(Artist.id > cursor)

    if search:
        query = query.where(Artist.name.ilike(f'%{search}%'))

    query = query.order_by(Artist.id).limit(limit+1)
    result = await session.execute(query)
    artists = result.scalars().all()

    if not artists:
        logger.warning(f'Artists with selected parameters (limit:{limit}, cursor:{cursor}, search:{search} not found')

    has_more = len(artists) > limit
    if has_more:
        artists = artists[:-1]

    next_cursor = artists[-1].id if artists and has_more else None

    return ArtistsAllRead(
        items=artists,
        has_more=has_more,
        next_cursor=next_cursor,
        limit=limit
    )  

@router.get('/artist/{id}', response_model=ArtistRead)
async def get_artist(request: Request, id: int, session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(Artist).where(Artist.id == id).options(selectinload(Artist.albums), selectinload(Artist.tracks)))
    artist = result.scalar_one_or_none()
    check_object_exist(artist)
    return artist

@router.post('/artist', response_model=ArtistShortRead)
async def post_artist(
    request: Request,
    artist_obj: ArtistPost = Depends(artist_post_form),
    file: Optional[UploadFile] = None,
    session: AsyncSession = Depends(get_async_session),
    user: CurrentUser = Depends(get_current_superuser)
):
    name = artist_obj.name
    if not await check_unique_artist_name(name=name, session=session):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f'Artist with {name} name already exist')
    
    artist = Artist(
        name=name,
        image_key=None
    )
    logger.success(f'Successful creation of new artist {artist}')

    session.add(artist)
    await session.commit()
    await session.refresh(artist)
    logger.info(f'Save new artist {artist} with {artist.id} id')

    if file:
        image_key = get_image_key_from_file(key=get_file_key(file=file), file=file)
        try:
            await streaming_minio_data_upload(key=image_key, content_type=file.content_type, file=file, is_public=True)
            artist.image_key = image_key
            await session.commit()
            await session.refresh(artist)
        except Exception:
            logger.error('Can\'t upload cover for artist')
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Can\'t upload cover for artist')
    
    return artist

@router.put('/artist/{id}', response_model=ArtistRead)
async def put_artist(
    request: Request,
    id: int,
    artist_obj: ArtistUpdate = Depends(artist_update_form),
    file: UploadFile = File(..., description='Cover for artist'),
    session: AsyncSession = Depends(get_async_session),
    user: CurrentUser = Depends(get_current_superuser)
):
    result = await session.execute(select(Artist).where(Artist.id == id).options(selectinload(Artist.albums), selectinload(Artist.tracks)))
    artist = result.scalar_one_or_none()
    check_object_exist(artist)
    
    name = artist_obj.name
    if not await check_unique_artist_name(name=name, session=session):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f'Artist with {name} name already exist')

    artist.name = name
    
    if artist.image_key:
        await default_minio_data_delete(key=artist.image_key, is_public=True)

    image_key = get_image_key_from_file(key=get_file_key(file=file), file=file)
    try:
        await streaming_minio_data_upload(key=image_key, content_type=file.content_type, file=file, is_public=True)
        artist.image_key = image_key
    except Exception:
        logger.error('Can\'t upload cover for artist')
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Can\'t upload cover for artist')
    
    logger.success(f'Successful update for {artist} artist with {artist.id} id')
    await session.commit()
    await session.refresh(artist)
    logger.info(f'Save updated artist {artist} with {artist.id} id')
    return artist

@router.patch('/artist/{id}', response_model=ArtistRead)
async def patch_artist(
    request: Request,
    id: int,
    artist_obj: ArtistPatch = Depends(artist_patch_form),
    file: Optional[UploadFile] = None,
    session: AsyncSession = Depends(get_async_session),
    user: CurrentUser = Depends(get_current_superuser)
):
    result = await session.execute(select(Artist).where(Artist.id == id).options(selectinload(Artist.albums), selectinload(Artist.tracks)))
    artist = result.scalar_one_or_none()
    check_object_exist(artist)
    
    if artist_obj.name:
        name = artist_obj.name
        if not await check_unique_artist_name(name=name, session=session):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f'Artist with {name} name already exist')
        artist.name = name
    
    if file:
        if artist.image_key:
            await default_minio_data_delete(key=artist.image_key, is_public=True)
        image_key = get_image_key_from_file(key=get_file_key(file=file), file=file)
        try:
            await streaming_minio_data_upload(key=image_key, content_type=file.content_type, file=file, is_public=True)
            artist.image_key = image_key
        except Exception:
            logger.error('Can\'t upload cover for artist')
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Can\'t upload cover for artist')
    
    logger.success(f'Successful patch for {artist} artist with {artist.id} id')
    await session.commit()
    await session.refresh(artist)
    logger.info(f'Save updated {artist} artist with {artist.id} id')
    return artist

@router.delete('/artist/{id}')
async def delete_artist(
    request: Request,
    id: int,
    session: AsyncSession = Depends(get_async_session),
    user: CurrentUser = Depends(get_current_superuser)
):
    result = await session.execute(select(Artist).where(Artist.id == id).options(selectinload(Artist.albums), selectinload(Artist.tracks)))
    artist = result.scalar_one_or_none()
    check_object_exist(artist)

    keys_to_delete = []
    keys_to_delete_public = []
    if artist.image_key:
        keys_to_delete_public.append(artist.image_key)
    
    for album in artist.albums:
        if album.image_key:
            keys_to_delete_public.append(album.image_key)
            
    for track in artist.tracks:
        keys_to_delete.append(track.s3_key)
        if track.image_key:
            keys_to_delete_public.append(track.image_key)

    for key in keys_to_delete:
        try:
            await default_minio_data_delete(key)
        except Exception as e:
            logger.error(f'Error while trying to delete {key}: {e}')
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Error while trying to delete {key}: {e}')
        
    for key in keys_to_delete_public:
        try:
            await default_minio_data_delete(key, is_public=True)
        except Exception as e:
            logger.error(f'Error while trying to delete {key}: {e}')
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f'Error while trying to delete {key}: {e}')

    await session.delete(artist)
    await session.commit()
    logger.success(f'Successful delete {artist} artist with {artist.id} id')

    return Response(status_code=status.HTTP_204_NO_CONTENT)