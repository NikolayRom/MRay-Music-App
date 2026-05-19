# tests/albums/test_service.py
import pytest
from unittest.mock import patch
from src.albums.service import album_post_form, album_update_form, album_patch_form

class TestAlbumsService:

    @patch("src.albums.service.AlbumPost")
    def test_album_post_form(self, mock_schema):
        album_post_form(name="After Hours", artist_id=1)
        mock_schema.assert_called_once_with(name="After Hours", artist_id=1)

    @patch("src.albums.service.AlbumUpdate")
    def test_album_update_form(self, mock_schema):
        album_update_form(name="Dawn FM", artist_id=1)
        mock_schema.assert_called_once_with(name="Dawn FM", artist_id=1)

    @patch("src.albums.service.AlbumPatch")
    def test_album_patch_form_full(self, mock_schema):
        album_patch_form(name="Starboy", artist_id=2)
        mock_schema.assert_called_once_with(name="Starboy", artist_id=2)

    @patch("src.albums.service.AlbumPatch")
    def test_album_patch_form_partial(self, mock_schema):
        # ПЕРЕДАЕМ None ЯВНО, чтобы перекрыть объект Form(None)
        album_patch_form(name="Only Name", artist_id=None)
        mock_schema.assert_called_once_with(name="Only Name", artist_id=None)