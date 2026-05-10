import pytest
from unittest.mock import MagicMock, AsyncMock
from src.models import Artist, Album, Track
from datetime import datetime, timedelta

@pytest.mark.asyncio
async def test_get_all_artists_success(ac, mock_session):
    fake_artist = Artist(id=1, name="Linkin Park", created_at=datetime.now())
    fake_artist.albums = []
    fake_artist.tracks = []
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [fake_artist]
    mock_session.execute = AsyncMock(return_value=mock_result)

    response = await ac.get("/artists")

    assert response.status_code == 200
    data = response.json()
    assert data["items"][0]["name"] == "Linkin Park"
    assert data["has_more"] is False

@pytest.mark.asyncio
async def test_get_artist_404(ac, mock_session):
    mock_session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=lambda: None))
    response = await ac.get("/artist/999")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_post_artist_success(ac, mock_session, mocker):
    mocker.patch("src.artists.router.check_unique_artist_name", AsyncMock(return_value=True))
    mocker.patch("src.artists.router.get_image_key_from_file", return_value="covers/1.jpg")
    mock_s3 = mocker.patch("src.artists.router.streaming_minio_data_upload", AsyncMock())

    async def mock_refresh(obj, fields=None):
        obj.id = 1
        obj.created_at = datetime.now()
        obj.albums = []
        obj.tracks = []
    mock_session.refresh = AsyncMock(side_effect=mock_refresh)
    mock_session.add = MagicMock()
    response = await ac.post(
        "/artist",
        data={"name": "New Artist"},
        files={"file": ("avatar.jpg", b"fake_img", "image/jpeg")}
    )

    assert response.status_code == 200
    assert response.json()["name"] == "New Artist"
    assert response.json()["image_key"] == "covers/1.jpg"
    mock_s3.assert_awaited_once()

@pytest.mark.asyncio
async def test_post_artist_duplicate_error(ac, mocker):
    mocker.patch("src.artists.router.check_unique_artist_name", AsyncMock(return_value=False))
    
    response = await ac.post("/artist", data={"name": "Existing Artist"})
    assert response.status_code == 400
    assert "already exist" in response.json()["detail"]

@pytest.mark.asyncio
async def test_put_artist_success(ac, mock_session, mocker):
    existing_artist = Artist(id=1, name="Old Name", image_key=None, created_at=datetime.now())
    mock_session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=lambda: existing_artist))
    mocker.patch("src.artists.router.check_unique_artist_name", AsyncMock(return_value=True))
    
    async def mock_refresh(obj, fields=None):
        obj.albums = []
        obj.tracks = []
    mock_session.refresh = AsyncMock(side_effect=mock_refresh)
    data = {
        "name": "Patched Name"
    }
    files = {"file": ("new_cover.jpg", b"fake_img", "image/jpeg")}
    response = await ac.put("/artist/1", data=data, files=files)
    
    assert response.status_code == 200
    assert response.json()["name"] == "Patched Name"
    mock_session.commit.assert_awaited()

@pytest.mark.asyncio
async def test_patch_artist_success(ac, mock_session, mocker):
    existing_artist = Artist(id=1, name="Old Name", image_key=None, created_at=datetime.now())
    mock_session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=lambda: existing_artist))
    mocker.patch("src.artists.router.check_unique_artist_name", AsyncMock(return_value=True))
    
    async def mock_refresh(obj, fields=None):
        obj.albums = []
        obj.tracks = []
    mock_session.refresh = AsyncMock(side_effect=mock_refresh)

    response = await ac.patch("/artist/1", data={})
    
    assert response.status_code == 200
    assert response.json()["name"] == "Old Name"
    mock_session.commit.assert_awaited()

@pytest.mark.asyncio
async def test_delete_artist_full_cleanup(ac, mock_session, mocker):
    
    fake_artist = Artist(id=1, name="Art", image_key="art.jpg", created_at=datetime.now())
    fake_album = Album(id=1, artist_id=1, name='Fake album', image_key="alb.jpg", created_at=datetime.now())
    fake_track = Track(id=1, title='track', s3_key="track.mp3", image_key="track.jpg", created_at=datetime.now(), duration=timedelta(seconds=200), genre=['Test Genre'])
    
    fake_artist.albums = [fake_album]
    fake_artist.tracks = [fake_track]
    
    mock_session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=lambda: fake_artist))
    
    mock_delete_s3 = mocker.patch("src.artists.router.default_minio_data_delete", AsyncMock())

    response = await ac.delete("/artist/1")

    assert response.status_code == 200
    
    assert mock_delete_s3.await_count == 4
    mock_session.delete.assert_called_once_with(fake_artist)