from src.playlists.schemas import PlaylistPatch, PlaylistPost, PlaylistUpdate
from fastapi import Form
from typing import List, Optional

def playlist_post_form(
    name: str = Form(...)
) -> PlaylistPost:
    return PlaylistPost(
        name=name
    )

def playlist_update_form(
    name: str = Form(...)
) -> PlaylistUpdate:
    return PlaylistUpdate(
        name=name 
    )

def playlist_patch_form(
    name: Optional[str] = Form(None)
) -> PlaylistPatch:
    return PlaylistPatch(
        name=name
    )