# tests/artists/test_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.artists.service import (
    check_unique_artist_name, 
    artist_post_form, 
    artist_update_form, 
    artist_patch_form
)

class TestArtistsService:

    @pytest.mark.asyncio
    @patch("src.artists.service.logger")
    async def test_check_unique_artist_name_exists(self, mock_logger):
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock() 
        mock_session.execute.return_value = mock_result

        result = await check_unique_artist_name("The Weeknd", mock_session)
        assert result is False
        mock_logger.warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_unique_artist_name_free(self):
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await check_unique_artist_name("New Artist", mock_session)
        assert result is True

    @patch("src.artists.service.ArtistPost")
    def test_artist_post_form(self, mock_schema):
        artist_post_form(name="Lana Del Rey")
        mock_schema.assert_called_once_with(name="Lana Del Rey")

    @patch("src.artists.service.ArtistUpdate")
    def test_artist_update_form(self, mock_schema):
        artist_update_form(name="Dua Lipa")
        mock_schema.assert_called_once_with(name="Dua Lipa")

    @patch("src.artists.service.ArtistPatch")
    def test_artist_patch_form_none(self, mock_schema):
        # Передаем None явно
        artist_patch_form(name=None)
        mock_schema.assert_called_once_with(name=None)