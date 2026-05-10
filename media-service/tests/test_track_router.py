import pytest
from unittest.mock import MagicMock, AsyncMock
from src.models import Track, Artist, Album
from datetime import timedelta, datetime

@pytest.mark.asyncio
async def test_get_all_tracks_success(ac, mock_session):
    fake_track = Track(
        id=1, title="Test Song", duration=timedelta(seconds=200),
        genre=["Rock"], created_at=datetime.now(), s3_key="key.mp3"
    )
    fake_track.artist = Artist(id=2, name="Test Artist", created_at=datetime.now())
    fake_track.album = Album(id=3, name="Test Album", artist_id=1, created_at=datetime.now())

    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [fake_track]
    mock_session.execute = AsyncMock(return_value=mock_result)

    response = await ac.get("/tracks")

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["title"] == "Test Song"
    assert data["items"][0]["duration_seconds"] == 200

@pytest.mark.asyncio
async def test_get_track_404(ac, mock_session):
    mock_session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=lambda: None))
    
    response = await ac.get("/track/999")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_get_track_200(ac, mock_session):
    fake_track = Track(
        id=1, title="Test Song", duration=timedelta(seconds=200),
        genre=["Rock"], created_at=datetime.now(), s3_key="key.mp3"
    )
    fake_track.artist = Artist(id=2, name="Test Artist", created_at=datetime.now())
    fake_track.album = Album(id=3, name="Test Album", artist_id=1, created_at=datetime.now())
    
    async def execute_side_effect(query, *args, **kwargs):
        params = kwargs.get('params', {})
        if hasattr(query, 'compile'):
            compiled = query.compile()
            track_id = compiled.params.get('id_1')
        
        if track_id == 1:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = fake_track
            return mock_result
        else:
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = None
            return mock_result
    
    mock_session.execute = AsyncMock(side_effect=execute_side_effect)
    
    response = await ac.get("/track/1")
    assert response.status_code == 200
    data = response.json()
    assert data['title'] == 'Test Song'
    assert data['album']['id'] == 3
    assert data['artist']['id'] == 2
    assert data['duration_seconds'] == 200

    response = await ac.get("/track/999")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_delete_track_success(ac, mock_session, mocker):
    fake_track = Track(id=1, title='song', genre=['rock'], duration=timedelta(seconds=200), s3_key="song.mp3", image_key="cover.jpg", created_at=datetime.now())
    mock_session.get = AsyncMock(return_value=fake_track)
    
    mock_del_s3 = mocker.patch("src.tracks.router.default_minio_data_delete", new_callable=AsyncMock)

    response = await ac.delete("/track/1")

    assert response.status_code == 200
    mock_del_s3.assert_awaited()
    mock_session.delete.assert_called_once()

@pytest.mark.asyncio
async def test_post_track_success(ac, mock_session, mocker):
    mocker.patch("src.tracks.router.check_file_size", return_value=None)
    mocker.patch("src.tracks.router.check_file_format", return_value=None)
    mocker.patch("src.tracks.router.check_artist_and_album_id_for_track", AsyncMock())
    mocker.patch("src.tracks.router.get_metadata_size", AsyncMock(return_value=1024))
    mocker.patch("src.tracks.router.streaming_minio_data_upload", AsyncMock())
    
    mock_audio = MagicMock()
    mock_audio.info.length = 200
    mock_audio.get.side_effect = lambda key, default=None: default
    mocker.patch("src.tracks.router.MP3", return_value=mock_audio)
    
    mocker.patch("src.tracks.router.get_track_artist_and_album_id", AsyncMock(return_value=(2, 3)))
    mocker.patch("src.tracks.router.get_track_image_key", AsyncMock(return_value="covers/test.jpg"))
    mocker.patch('src.tracks.router.get_track_title', return_value='New Song')
    mocker.patch('src.tracks.router.get_track_genre', return_value=["Rock", "Pop"])

    fake_artist = Artist(id=2, name="Test Artist", created_at=datetime.now())
    fake_album = Album(id=3, name="Test Album", artist_id=1, created_at=datetime.now())

    def mock_add(obj):
        obj.id = 1
        obj.created_at = datetime.now()

    def mock_refresh(obj, extra):
        obj.artist = fake_artist
        obj.album = fake_album

    mock_session.add = MagicMock(side_effect=mock_add)
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock(side_effect=mock_refresh)

    form_data = {
        'genre': ['Lofi']
    }
    
    files = {
        "file_track": ("test.mp3", b"fake-mp3-binary-content", "audio/mpeg")
    }
    
    response = await ac.post(
        "/track",
        data=form_data,
        files=files
    )

    assert response.status_code == 200

    data = response.json()
    assert data["title"] == "New Song"
    assert data["artist"]["id"] == 2
    assert data['album']['id'] == 3
    assert data['genre'] == ['Lofi']
    assert data['duration_seconds'] == 200
    assert data['image_key'] == "covers/test.jpg"
    
    mock_session.add.assert_called()
    mock_session.commit.assert_awaited()
    mock_session.refresh.assert_awaited()

@pytest.mark.asyncio
async def test_put_track_success(ac, mock_session, mocker):
    existing_track = Track(
        id=1, 
        title="Old Title", 
        s3_key="old_key.mp3", 
        image_key="covers/old_image.jpg",
        duration=timedelta(seconds=100),
        genre=["Old Genre"],
        created_at=datetime.now()
    )
    
    mock_session.get = AsyncMock(return_value=existing_track)
    mocker.patch("src.tracks.router.check_artist_and_album_id_for_track", AsyncMock())
    mocker.patch("src.tracks.router.get_image_key_from_file", return_value="covers/new_image.jpg")
    mock_del_s3 = mocker.patch("src.tracks.router.default_minio_data_delete", AsyncMock())
    mock_up_s3 = mocker.patch("src.tracks.router.streaming_minio_data_upload", AsyncMock())

    async def mock_refresh(obj, fields=None):
        obj.artist = Artist(id=10, name="New Artist", created_at=datetime.now())
        obj.album = Album(id=20, name="New Album", artist_id=10, created_at=datetime.now())
    
    mock_session.refresh = AsyncMock(side_effect=mock_refresh)
    mock_session.commit = AsyncMock()

    form_data = {
        "title": "Updated Title",
        "artist_id": "10",
        "album_id": "20",
        "genre": ["Rock", "Metal"]
    }
    files = {"file": ("new_cover.jpg", b"fake_img", "image/jpeg")}

    response = await ac.put("/track/1", data=form_data, files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["image_key"] == "covers/new_image.jpg"
    assert data["artist"]["id"] == 10
    
    mock_del_s3.assert_awaited_once_with(key="covers/old_image.jpg")
    mock_up_s3.assert_awaited_once()
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_patch_track_success(ac, mock_session, mocker):
    existing_track = Track(
        id=1, title="Original", s3_key="k.mp3", duration=timedelta(seconds=50),
        genre=["Pop"], created_at=datetime.now(), image_key=None
    )
    mock_session.get = AsyncMock(return_value=existing_track)
    mocker.patch("src.tracks.router.check_artist_and_album_id_for_track", AsyncMock())

    async def mock_refresh(obj, fields=None):
        obj.artist = None
        obj.album = None
    mock_session.refresh = AsyncMock(side_effect=mock_refresh)

    form_data = {"title": "Patched Title"}
    
    response = await ac.patch("/track/1", data=form_data)

    assert response.status_code == 200
    assert response.json()["title"] == "Patched Title"
    assert response.json()["genre"] == ["Pop"] 
    mock_session.commit.assert_awaited_once()


class AsyncIterator:
    def __init__(self, seq):
        self.iter = iter(seq)

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self.iter)
        except StopIteration:
            raise StopAsyncIteration

    def close(self):
        pass

@pytest.mark.asyncio
async def test_stream_track_success_200(ac, mock_session, mocker):
    # 1. Готовим фейковый трек
    fake_track = Track(id=1, s3_key="test_song.mp3")
    mock_session.get = AsyncMock(return_value=fake_track)

    # 2. Мокаем S3 клиент и его метод get_object
    mock_s3_client = AsyncMock()
    
    # Имитируем ответ от S3
    mock_s3_body = AsyncIterator([b"chunk1", b"chunk2"])
    mock_s3_response = {
        "Body": mock_s3_body,
        "ContentType": "audio/mpeg",
        "ContentLength": 12,
    }
    mock_s3_client.get_object.return_value = mock_s3_response
    
    # Мокаем контекстный менеджер s3_storage.get_client().__aenter__()
    mock_ctx = MagicMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_s3_client)
    mocker.patch("src.tracks.router.s3_storage.get_client", return_value=mock_ctx)

    # 3. Делаем запрос
    response = await ac.get("/stream/1")

    # 4. Проверки
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/mpeg"
    assert response.headers["accept-ranges"] == "bytes"
    # Собираем все чанки из ответа
    content = b""
    async for chunk in response.aiter_bytes():
        content += chunk
    assert content == b"chunk1chunk2"

@pytest.mark.asyncio
async def test_stream_track_range_206(ac, mock_session, mocker):
    # 1. Трек в базе
    fake_track = Track(id=1, s3_key="test_song.mp3")
    mock_session.get = AsyncMock(return_value=fake_track)

    # 2. Мокаем S3 ответ для Range-запроса
    mock_s3_client = AsyncMock()
    mock_s3_body = AsyncIterator([b"partial_data"])
    mock_s3_response = {
        "Body": mock_s3_body,
        "ContentType": "audio/mpeg",
        "ContentLength": 12,
        "ContentRange": "bytes 0-11/100" # S3 возвращает это, если был Range
    }
    mock_s3_client.get_object.return_value = mock_s3_response
    
    mock_ctx = MagicMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_s3_client)
    mocker.patch("src.tracks.router.s3_storage.get_client", return_value=mock_ctx)

    # 3. Делаем запрос с заголовком Range
    headers = {"Range": "bytes=0-11"}
    response = await ac.get("/stream/1", headers=headers)

    # 4. Проверки
    assert response.status_code == 206
    assert response.headers["content-range"] == "bytes 0-11/100"
    mock_s3_client.get_object.assert_called_once_with(
        Bucket=mocker.ANY,
        Key="test_song.mp3",
        Range="bytes=0-11"
    )

@pytest.mark.asyncio
async def test_stream_track_s3_error_500(ac, mock_session, mocker):
    # 1. Трек в базе
    fake_track = Track(id=1, s3_key="bad_song.mp3")
    mock_session.get = AsyncMock(return_value=fake_track)

    # 2. Имитируем падение S3 (например, ошибка сети)
    mock_s3_client = AsyncMock()
    mock_s3_client.get_object.side_effect = Exception("S3 Connection Lost")
    
    mock_ctx = MagicMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_s3_client)
    mock_ctx.__aexit__ = AsyncMock() # Не забываем про закрытие
    mocker.patch("src.tracks.router.s3_storage.get_client", return_value=mock_ctx)

    # 3. Запрос
    response = await ac.get("/stream/1")

    # 4. Проверки
    assert response.status_code == 500
    assert "Can't stream this mp3 file" in response.json()["detail"]