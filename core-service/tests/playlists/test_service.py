import pytest
from src.playlists.service import playlist_post_form, playlist_update_form, playlist_patch_form
from src.playlists.schemas import PlaylistPost, PlaylistUpdate, PlaylistPatch

def test_playlist_post_form():
    result = playlist_post_form(name="My Playlist")
    assert isinstance(result, PlaylistPost)
    assert result.name == "My Playlist"

def test_playlist_update_form():
    result = playlist_update_form(name="Updated Name")
    assert isinstance(result, PlaylistUpdate)
    assert result.name == "Updated Name"

def test_playlist_patch_form():
    result = playlist_patch_form(name="Patched Name")
    assert isinstance(result, PlaylistPatch)
    assert result.name == "Patched Name"

def test_playlist_patch_form_none():
    result = playlist_patch_form(name=None)
    assert isinstance(result, PlaylistPatch)
    assert result.name is None