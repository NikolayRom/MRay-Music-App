import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.models import Playlist
from src.common.rbac import CurrentUser
from fastapi import HTTPException, Response, UploadFile
from datetime import datetime, timezone
from src.playlists.router import (
    get_all_playlists, get_playlist, post_playlist, 
    update_playlist, patch_playlist, delete_playlist,
    append_track, remove_track
)
from src.playlists.schemas import PlaylistPost, PlaylistUpdate, PlaylistPatch, PlaylistTrackAdd

@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.add = MagicMock()
    session.delete = MagicMock()
    return session

@pytest.fixture
def mock_current_user():
    return CurrentUser(id=1, is_superuser=False)

@pytest.fixture
def mock_playlist():
    # Явная инициализация всех полей, необходимых для логики и схем
    playlist = Playlist()
    playlist.id = 10
    playlist.name = "Test Playlist"
    playlist.user_id = 1
    playlist.track_ids = [1, 2, 3] # Теперь список точно заполнен
    playlist.image_key = "old_key"
    playlist.created_at = datetime.now(timezone.utc)
    playlist.updated_at = datetime.now(timezone.utc)
    return playlist

@pytest.fixture
def mock_cover():
    mock = MagicMock(spec=UploadFile)
    mock.filename = "cover.jpg"
    return mock

@pytest.mark.asyncio
async def test_get_all_playlists_success(mock_session, mock_current_user):
    now = datetime.now(timezone.utc)
    # Создаем плейлист со всеми полями для схемы PlaylistRead
    p = Playlist(
        id=1, name="List", user_id=1, track_ids=[], 
        image_key=None, created_at=now, updated_at=now
    )
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [p]
    mock_session.execute.return_value = mock_result

    result = await get_all_playlists(MagicMock(), mock_current_user, mock_session)
    assert len(result.items) == 1
    assert result.items[0].name == "List"

@pytest.mark.asyncio
async def test_get_playlist_success(mock_session, mock_current_user, mock_playlist):
    mock_session.get.return_value = mock_playlist
    result = await get_playlist(MagicMock(), 10, mock_current_user, mock_session)
    assert result.id == 10

@pytest.mark.asyncio
async def test_post_playlist_success_with_cover(mock_session, mock_current_user, mock_cover):
    playlist_data = PlaylistPost(name="New Playlist")
    mock_session.execute.return_value = MagicMock(scalar_one_or_none=lambda: None)

    with patch("src.playlists.router.get_image_key", new_callable=AsyncMock) as mock_img, \
         patch("src.playlists.router.gen_uuid", return_value="uuid"):
        
        mock_img.return_value = "new_cover_key"
        
        # Для post_playlist нам нужен "живой" объект, который получит поля после session.add
        result = await post_playlist(MagicMock(), playlist_data, mock_cover, mock_current_user, mock_session)

        assert result.name == "New Playlist"
        # Проверяем, что созданный плейлист имеет базовые поля
        assert result.track_ids == []
        assert result.image_key == "new_cover_key"

@pytest.mark.asyncio
async def test_post_playlist_conflict(mock_session, mock_current_user):
    playlist_data = PlaylistPost(name="Duplicate")
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = Playlist(id=1)
    mock_session.execute.return_value = mock_result

    with pytest.raises(HTTPException) as exc:
        await post_playlist(MagicMock(), playlist_data, None, mock_current_user, mock_session)
    assert exc.value.status_code == 409

# 3. Тесты PUT (полное обновление)
@pytest.mark.asyncio
async def test_update_playlist_success(mock_session, mock_current_user, mock_playlist, mock_cover):
    update_data = PlaylistUpdate(name="Renamed")
    mock_session.get.return_value = mock_playlist
    
    # Мок проверки уникальности (имя свободно)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    with patch("src.playlists.router.get_image_key", new_callable=AsyncMock) as mock_img:
        mock_img.return_value = "updated_cover_key"
        
        result = await update_playlist(MagicMock(), 10, update_data, mock_cover, mock_current_user, mock_session)

        assert result.name == "Renamed"
        assert result.image_key == "updated_cover_key"

# 4. Тесты PATCH (частичное обновление)
@pytest.mark.asyncio
async def test_patch_playlist_only_name(mock_session, mock_current_user, mock_playlist):
    patch_data = PlaylistPatch(name="Patched Name")
    mock_session.get.return_value = mock_playlist
    
    # Имитируем отсутствие конфликтов имен
    mock_session.execute.return_value = MagicMock(scalar_one_or_none=lambda: None)

    result = await patch_playlist(MagicMock(), 10, patch_data, None, mock_current_user, mock_session)
    
    assert result.name == "Patched Name"
    assert result.image_key == "old_key" # Не изменилось

@pytest.mark.asyncio
async def test_patch_playlist_s3_error(mock_session, mock_current_user, mock_playlist, mock_cover):
    patch_data = PlaylistPatch()
    mock_session.get.return_value = mock_playlist

    with patch("src.playlists.router.get_image_key", side_effect=Exception("S3 Down")):
        with pytest.raises(HTTPException) as exc:
            await patch_playlist(MagicMock(), 10, patch_data, mock_cover, mock_current_user, mock_session)
        assert exc.value.status_code == 415

@pytest.mark.asyncio
async def test_delete_playlist_success(mock_session, mock_current_user, mock_playlist):
    mock_session.get.return_value = mock_playlist
    
    # Мокаем и удаление из S3, и удаление из БД
    with patch("src.playlists.router.default_minio_data_delete", new_callable=AsyncMock) as mock_s3_del:
        result = await delete_playlist(MagicMock(), 10, mock_current_user, mock_session)

        assert result.status_code == 204
        mock_s3_del.assert_called_once_with(key="old_key")
        mock_session.delete.assert_called_once_with(mock_playlist)

@pytest.mark.asyncio
async def test_append_track_new_success(mock_session, mock_current_user, mock_playlist):
    track_data = PlaylistTrackAdd(track_id=4)
    mock_session.get.return_value = mock_playlist

    with patch("src.playlists.router.flag_modified") as mock_flag:
        result = await append_track(MagicMock(), 10, track_data, mock_current_user, mock_session)

        # Теперь 4 добавится к [1, 2, 3], и длина станет 4
        assert 4 in result.track_ids
        assert len(result.track_ids) == 4
        assert mock_flag.called

@pytest.mark.asyncio
async def test_append_track_existing_moves_to_end(mock_session, mock_current_user, mock_playlist):
    track_data = PlaylistTrackAdd(track_id=1) # 1 уже есть
    mock_session.get.return_value = mock_playlist

    with patch("src.playlists.router.flag_modified"):
        result = await append_track(MagicMock(), 10, track_data, mock_current_user, mock_session)

        assert result.track_ids == [2, 3, 1] # 1 удалился и встал в конец
        assert len(result.track_ids) == 3


@pytest.mark.asyncio
async def test_append_track_playlist_not_found(mock_session, mock_current_user):
    """Плейлист не найден или принадлежит другому пользователю."""
    mock_session.get.return_value = None
    
    with pytest.raises(HTTPException) as exc:
        await append_track(MagicMock(), 99, PlaylistTrackAdd(track_id=1), mock_current_user, mock_session)
    assert exc.value.status_code == 404

@pytest.mark.asyncio
async def test_remove_track_success(mock_session, mock_current_user, mock_playlist):
    mock_session.get.return_value = mock_playlist

    with patch("src.playlists.router.flag_modified") as mock_flag:
        result = await remove_track(MagicMock(), 10, 2, mock_current_user, mock_session)

        assert isinstance(result, Response)
        assert result.status_code == 204
        assert 2 not in mock_playlist.track_ids

@pytest.mark.asyncio
async def test_remove_track_not_in_playlist(mock_session, mock_current_user, mock_playlist):
    """Ошибка, если трека нет в этом плейлисте."""
    mock_session.get.return_value = mock_playlist

    with pytest.raises(HTTPException) as exc:
        await remove_track(MagicMock(), 10, 999, mock_current_user, mock_session)
    
    assert exc.value.status_code == 404
    assert "not found" in exc.value.detail

@pytest.mark.asyncio
async def test_remove_track_access_denied(mock_session, mock_current_user):
    """Плейлист принадлежит другому пользователю."""
    other_playlist = Playlist(id=10, user_id=99, track_ids=[1])
    mock_session.get.return_value = other_playlist

    with pytest.raises(HTTPException) as exc:
        await remove_track(MagicMock(), 10, 1, mock_current_user, mock_session)
    assert exc.value.status_code == 404