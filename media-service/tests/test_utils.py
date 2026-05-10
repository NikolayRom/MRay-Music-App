import pytest
from unittest.mock import AsyncMock, MagicMock
from src.tracks.utils import get_or_create_artist, get_id3_size, gen_uuid, get_or_create_album
from src.models import Artist, Album

@pytest.mark.asyncio
async def test_mock_get_or_create_artist_exists(mock_session):
    mock_artist = Artist(id=1, name="Linkin Park")
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_artist
    mock_session.execute.return_value = mock_result

    artist = await get_or_create_artist(session=mock_session, name="Linkin Park")
    
    assert artist.name == "Linkin Park"
    mock_session.add.assert_not_called()

@pytest.mark.asyncio
async def test_mock_get_or_create_artist_not_exists(mock_session):
    mock_session.add = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    artist = await get_or_create_artist(session=mock_session, name="Linkin Park")
    
    assert artist.name == "Linkin Park"
    mock_session.add.assert_called_once()
    mock_session.flush.assert_called_once()

@pytest.mark.asyncio
async def test_mock_get_or_create_album_exists(mock_session):
    mock_album = Album(id=1, name="Test Album", artist_id=2)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_album
    mock_session.execute.return_value = mock_result

    album = await get_or_create_album(session=mock_session, name="Test Album", artist_id=2)

    assert album.name == "Test Album"
    mock_session.add.assert_not_called()

@pytest.mark.asyncio
async def test_mock_get_or_create_album_not_exists(mock_session):
    mock_session.add = MagicMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    album = await get_or_create_album(session=mock_session, name="Test Album", artist_id=2)

    assert album.name == "Test Album"
    mock_session.add.assert_called_once()
    mock_session.flush.assert_called_once()

def test_get_id3_size_calculation():
    header = b'ID3\x03\x00\x00\x00\x00\x02\x01' 
    size = get_id3_size(header)
    assert isinstance(size, int)
    assert size > 10

def test_get_uuid():
    test_uuid = gen_uuid()
    assert type(test_uuid) == str