import pytest
from unittest.mock import MagicMock, AsyncMock
from src.models import Album, Artist, Track
from datetime import datetime, timedelta

@pytest.mark.asyncio
async def test_get_all_albums_success(ac, mock_session):
    fake_album = Album(id=1, name="Nevermind", artist_id=2, created_at=datetime.now())
    fake_album.artist = Artist(id=2, name="Nirvana", created_at=datetime.now())
    fake_album.tracks = []
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [fake_album]
    mock_session.execute = AsyncMock(return_value=mock_result)

    response = await ac.get("/albums", params={"artist_id": 2})

    assert response.status_code == 200
    data = response.json()
    assert data["items"][0]["name"] == "Nevermind"
    assert data["items"][0]["artist"]["name"] == "Nirvana"

@pytest.mark.asyncio
async def test_post_album_success(ac, mock_session, mocker):
    mock_artist = Artist(id=10, name="Artist Name", created_at=datetime.now())
    mock_session.get = AsyncMock(return_value=mock_artist)
    
    mocker.patch("src.albums.router.get_image_key_from_file", return_value="covers/album1.jpg")
    mock_s3 = mocker.patch("src.albums.router.streaming_minio_data_upload", AsyncMock())

    async def mock_refresh(obj, fields=None):
        obj.id = 1
        obj.created_at = datetime.now()
        obj.artist = mock_artist
        obj.tracks = []
    mock_session.refresh = AsyncMock(side_effect=mock_refresh)
    mock_session.add = MagicMock()

    form_data = {"name": "New Album", "artist_id": 10}
    response = await ac.post("/album", data=form_data)

    assert response.status_code == 200
    assert response.json()["name"] == "New Album"
    assert response.json()["artist_id"] == 10
    mock_session.add.assert_called()

@pytest.mark.asyncio
async def test_post_album_artist_not_found(ac, mock_session):
    mock_session.get = AsyncMock(return_value=None)
    response = await ac.post("/album", data={"name": "Album", "artist_id": 999})
    assert response.status_code == 404
    assert "Object not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_put_album_success(ac, mock_session, mocker):
    existing_album = Album(id=1, name="Old", artist_id=5, image_key=None, created_at=datetime.now())
    mock_session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=lambda: existing_album))
    mock_session.get = AsyncMock(return_value=MagicMock(id=6))

    async def mock_refresh(obj, fields=None):
        obj.artist = Artist(id=6, name="New Art", created_at=datetime.now())
        obj.tracks = []
    mock_session.refresh = AsyncMock(side_effect=mock_refresh)

    data = {
        "name": "New",
        "artist_id": 6
    }
    files = {"file": ("new_cover.jpg", b"fake_img", "image/jpeg")}
    response = await ac.put("/album/1", data=data, files=files)
    
    assert response.status_code == 200
    assert response.json()["name"] == "New"
    assert response.json()["artist_id"] == 6
    mock_session.commit.assert_awaited()

@pytest.mark.asyncio
async def test_patch_album_success(ac, mock_session, mocker):
    existing_album = Album(id=1, name="Old", artist_id=5, image_key=None, created_at=datetime.now())
    mock_session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=lambda: existing_album))
    mock_session.get = AsyncMock(return_value=MagicMock(id=6))

    async def mock_refresh(obj, fields=None):
        obj.artist = Artist(id=6, name="New Art", created_at=datetime.now())
        obj.tracks = []
    mock_session.refresh = AsyncMock(side_effect=mock_refresh)

    data = {
        "name": "New",
    }

    response = await ac.patch("/album/1", data=data)
    
    assert response.status_code == 200
    assert response.json()["name"] == "New"
    assert response.json()["artist_id"] == 5
    mock_session.commit.assert_awaited()

@pytest.mark.asyncio
async def test_delete_album_cleanup(ac, mock_session, mocker):
    fake_album = Album(id=1, artist_id=1, name="To Delete", image_key="alb.jpg", created_at=datetime.now())
    fake_track = Track(id=1, title='track', duration=timedelta(seconds=200), genre=['Test Genre'], s3_key="track.mp3", image_key="track.jpg", created_at=datetime.now())
    fake_album.tracks = [fake_track]
    
    mock_session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=lambda: fake_album))
    mock_del_s3 = mocker.patch("src.albums.router.default_minio_data_delete", AsyncMock())

    response = await ac.delete("/album/1")

    assert response.status_code == 200
    assert mock_del_s3.await_count == 3
    mock_session.delete.assert_called_once_with(fake_album)