from fastapi import APIRouter, Depends, Request, HTTPException, status, Response, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.database import get_async_session
from src.playlists.schemas import PlaylistRead, PlaylistsAllRead, PlaylistPatch, PlaylistPost, PlaylistUpdate, PlaylistTrackAdd
from src.common.rbac import CurrentUser, get_current_user
from src.models import Playlist
from src.common.logger import logger
from typing import Optional
from src.common.image_utils import get_image_key, gen_uuid
from src.playlists.service import playlist_patch_form, playlist_post_form, playlist_update_form
from sqlalchemy.orm.attributes import flag_modified
from src.common.s3_utils import default_minio_data_delete

router = APIRouter(prefix='/playlists')

@router.get('/', response_model=PlaylistsAllRead)
async def get_all_playlists(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(select(Playlist).where(Playlist.user_id == current_user.id))
    playlists = result.scalars().all()
    return PlaylistsAllRead(
        items=playlists
    )

@router.get('/{playlist_id}', response_model=PlaylistRead)
async def get_playlist(
    request: Request,
    playlist_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    playlist = await session.get(Playlist, playlist_id)
    if not playlist or playlist.user_id != current_user.id:
        logger.error(f'Playlist with {playlist_id} id not found for user with {current_user.id} id')
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Playlist with {playlist_id} id not found for user with {current_user.id} id')
    
    return playlist

@router.post('/', response_model=PlaylistRead, status_code=status.HTTP_201_CREATED)
async def post_playlist(
    request: Request,
    playlist_data: PlaylistPost = Depends(playlist_post_form),
    cover: Optional[UploadFile] = None,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    
    result = await session.execute(select(Playlist).where(
        Playlist.user_id == current_user.id,
        Playlist.name == playlist_data.name
    ))
    
    if result.scalar_one_or_none():
        logger.error(f'Playlist with {playlist_data.name} name for user with {current_user.id} id already exists!')
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f'Playlist with {playlist_data.name} name for user with {current_user.id} id already exists!')
    
    playlist = Playlist(
        name=playlist_data.name,
        user_id=current_user.id,
        track_ids=[]
    )

    session.add(playlist)
    await session.flush()

    try:
        if cover:
            cover_key = await get_image_key(key=gen_uuid()+'_'+str(playlist.id), file=cover)
            playlist.image_key = cover_key
            await session.commit()
            await session.refresh(playlist)
    except Exception as e:
        logger.error(f'Failed to upload cover for playlist: {e}')
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=f'Failed to upload cover for playlist: {e}')

    logger.success(f'Successfully create new playlist with {playlist_data.name} name for user with {current_user.id} id')
    return playlist

@router.put('/{playlist_id}', response_model=PlaylistRead)
async def update_playlist(
    request: Request,
    playlist_id: int,
    playlist_data: PlaylistUpdate = Depends(playlist_update_form),
    cover: UploadFile = File(..., description='Cover for user\'s playlist'),
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    
    result = await session.execute(select(Playlist).where(
        Playlist.user_id == current_user.id,
        Playlist.name == playlist_data.name,
        Playlist.id != playlist_id
    ))
    
    if result.scalar_one_or_none():
        logger.error(f'Playlist with {playlist_data.name} name for user with {current_user.id} id already exists!')
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f'Playlist with {playlist_data.name} name for user with {current_user.id} id already exists!')


    playlist = await session.get(Playlist, playlist_id)
    if not playlist or playlist.user_id != current_user.id:
        logger.error(f'Playlist with {playlist_id} id not found for user with {current_user.id} id')
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Playlist with {playlist_id} id not found for user with {current_user.id} id')    
   
    try:
        cover_key = await get_image_key(key=gen_uuid()+'_'+str(playlist.id), file=cover)
    except Exception as e:
        logger.error(f'Failed to upload cover for playlist: {e}')
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=f'Failed to upload cover for playlist: {e}')

    playlist.name = playlist_data.name
    playlist.image_key = cover_key

    await session.commit()
    await session.refresh(playlist)
    logger.success(f'Successfully update playlist with {playlist_data.name} name for user with {current_user.id} id')

    return playlist

@router.patch('/{playlist_id}', response_model=PlaylistRead)
async def patch_playlist(
    request: Request,
    playlist_id: int,
    playlist_data: PlaylistPatch = Depends(playlist_patch_form),
    cover: Optional[UploadFile] = None,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    if playlist_data.name:
        result = await session.execute(select(Playlist).where(
            Playlist.user_id == current_user.id,
            Playlist.name == playlist_data.name,
            Playlist.id != playlist_id
        ))
        
        if result.scalar_one_or_none():
            logger.error(f'Playlist with {playlist_data.name} name for user with {current_user.id} id already exists!')
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f'Playlist with {playlist_data.name} name for user with {current_user.id} id already exists!')

    playlist = await session.get(Playlist, playlist_id)
    if not playlist or playlist.user_id != current_user.id:
        logger.error(f'Playlist with {playlist_id} id not found for user with {current_user.id} id')
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Playlist with {playlist_id} id not found for user with {current_user.id} id')
   
    try:
        if cover:
            cover_key = await get_image_key(key=gen_uuid()+'_'+str(playlist.id), file=cover)
    except Exception as e:
        logger.error(f'Failed to upload cover for playlist: {e}')
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=f'Failed to upload cover for playlist: {e}')

    if cover:
        playlist.image_key = cover_key
    if playlist_data.name:
        playlist.name = playlist_data.name
    
    await session.commit()
    await session.refresh(playlist)
    logger.success(f'Successfully update playlist with {playlist_data.name} name for user with {current_user.id} id')

    return playlist

@router.delete('/{playlist_id}')
async def delete_playlist(
    request: Request,
    playlist_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    
    playlist = await session.get(Playlist, playlist_id)
    if not playlist or playlist.user_id != current_user.id:
        logger.error(f'Playlist with {playlist_id} id not found for user with {current_user.id} id')
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Playlist with {playlist_id} id not found for user with {current_user.id} id')

    await default_minio_data_delete(key=playlist.image_key)

    session.delete(playlist)
    await session.commit()
    logger.success(f'Successfully delete playlist with {playlist_id} id for user with {current_user.id} id')

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post('/{playlist_id}/', response_model=PlaylistRead, status_code=status.HTTP_201_CREATED)
async def append_track(
    request: Request,
    playlist_id: int,
    track_data: PlaylistTrackAdd,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    playlist = await session.get(Playlist, playlist_id)
    if not playlist or playlist.user_id != current_user.id:
        logger.error(f'Playlist with {playlist_id} id not found for user with {current_user.id} id')
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Playlist with {playlist_id} id not found for user with {current_user.id} id')    

    if track_data.track_id in playlist.track_ids:
        playlist.track_ids.remove(track_data.track_id)

    playlist.track_ids.append(track_data.track_id)

    flag_modified(playlist, 'track_ids')
    await session.commit()
    await session.refresh(playlist)
    logger.success(f'Successfully add track with {track_data.track_id} id to playlist with {playlist_id} id for user with {current_user.id} id')

    return playlist

@router.delete('/{playlist_id}/{track_id}')
async def remove_track(
    request: Request,
    playlist_id: int,
    track_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session)
):
    playlist = await session.get(Playlist, playlist_id)
    if not playlist or playlist.user_id != current_user.id:
        logger.error(f'Playlist with {playlist_id} id not found for user with {current_user.id} id')
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Playlist with {playlist_id} id not found for user with {current_user.id} id')    
    
    if track_id not in playlist.track_ids:
        logger.error(f'Track with {track_id} id in playlist with {playlist_id} id by user with {current_user.id} id not found')
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Track with {track_id} id in playlist with {playlist_id} id by user with {current_user.id} id not found')
    
    playlist.track_ids.remove(track_id)

    flag_modified(playlist, 'track_ids')
    await session.commit()
    await session.refresh(playlist)
    logger.success(f'Successfully remove track with {track_id} id from playlist with {playlist_id} id by user with {current_user.id} id')

    return Response(status_code=status.HTTP_204_NO_CONTENT)