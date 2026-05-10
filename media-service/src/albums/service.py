from fastapi import Form
from src.albums.schemas import AlbumPatch, AlbumPost, AlbumUpdate
from typing import Optional

def album_post_form(
    name: str = Form(...),
    artist_id: int = Form(...)
) -> AlbumPost:
    return AlbumPost(name=name, artist_id=artist_id)

def album_update_form(
    name: str = Form(...),
    artist_id: int = Form(...)
) -> AlbumUpdate:
    return AlbumUpdate(name=name, artist_id=artist_id)

def album_patch_form(
    name: Optional[str] = Form(None),
    artist_id: Optional[int] = Form(None)  
) -> AlbumPatch:
    return AlbumPatch(name=name, artist_id=artist_id)