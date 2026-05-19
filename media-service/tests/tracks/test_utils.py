import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.tracks.utils import get_id3_size, get_or_create_artist, get_or_create_album
from src.models import Artist, Album

class TestTracksUtils:

    def test_get_id3_size_calculation(self):
        
        header = bytearray(10)
        header[6] = 0x00
        header[7] = 0x00
        header[8] = 0x02
        header[9] = 0x01
        
        result = get_id3_size(header)
        assert result == 267

    def test_get_id3_size_max_synchsafe(self):
        
        header = bytearray(10)
        
        for i in range(6, 10):
            header[i] = 0x7F 
            
        
        
        result = get_id3_size(header)
        assert result == 268435465

    @pytest.mark.asyncio
    async def test_get_or_create_artist_exists(self):
        
        mock_session = AsyncMock()
        mock_session.add = MagicMock() 
        
        existing_artist = Artist(id=1, name="Existing")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_artist
        mock_session.execute.return_value = mock_result

        result = await get_or_create_artist(mock_session, "Existing")

        assert result == existing_artist
        mock_session.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_or_create_artist_new(self):
        
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await get_or_create_artist(mock_session, "New Artist")

        assert isinstance(result, Artist)
        assert result.name == "New Artist"
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_or_create_album_exists(self):
        
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        
        existing_album = Album(id=1, name="Old Album", artist_id=10)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_album
        mock_session.execute.return_value = mock_result

        result = await get_or_create_album(mock_session, "Old Album", 10)

        assert result == existing_album
        mock_session.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_or_create_album_new(self):
        
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await get_or_create_album(mock_session, "New Album", 20)

        assert isinstance(result, Album)
        assert result.name == "New Album"
        assert result.artist_id == 20
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()