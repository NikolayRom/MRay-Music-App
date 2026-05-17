import pytest
from fastapi import HTTPException, status, Response
from unittest.mock import AsyncMock, MagicMock, patch
from src.likes.router import get_all_likes, get_like, toggle_like
from src.models import Like
from src.common.rbac import CurrentUser
from src.likes.schemas import LikeData
from datetime import datetime, timezone

@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.add = MagicMock()    # Синхронный метод
    session.delete = MagicMock() # Синхронный метод
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    return session

@pytest.fixture
def mock_current_user():
    return CurrentUser(id=1, is_superuser=False)

@pytest.fixture
def mock_request():
    return MagicMock()

# 1. Тест GET / (get_all_likes)
@pytest.mark.asyncio
async def test_get_all_likes_success(mock_session, mock_current_user, mock_request):
    # Создаем список фейковых лайков
    fake_likes = [
        Like(id=1, user_id=1, track_id=101, created_at=datetime.now(timezone.utc)),
        Like(id=2, user_id=1, track_id=102, created_at=datetime.now(timezone.utc))
    ]
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = fake_likes
    mock_session.execute.return_value = mock_result

    result = await get_all_likes(mock_request, mock_current_user, mock_session)

    assert len(result.items) == 2
    assert result.items[0].track_id == 101
    assert mock_session.execute.called

# 2. Тесты GET /{track_id} (get_like)
@pytest.mark.asyncio
async def test_get_like_found(mock_session, mock_current_user, mock_request):
    fake_like = Like(id=1, user_id=1, track_id=555)
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = fake_like
    mock_session.execute.return_value = mock_result

    result = await get_like(mock_request, 555, mock_current_user, mock_session)

    assert result.track_id == 555
    assert result.user_id == 1

@pytest.mark.asyncio
async def test_get_like_not_found(mock_session, mock_current_user, mock_request):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    with pytest.raises(HTTPException) as exc:
        await get_like(mock_request, 999, mock_current_user, mock_session)
    
    assert exc.value.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in exc.value.detail

# 3. Тесты POST / (toggle_like)
@pytest.mark.asyncio
async def test_toggle_like_create(mock_session, mock_current_user, mock_request):
    """Сценарий: лайка нет, он должен создаться (201 Created)."""
    like_data = LikeData(track_id=777)
    
    # Имитируем, что лайк в базе не найден
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    result = await toggle_like(mock_request, like_data, mock_current_user, mock_session)

    # Проверяем создание
    assert isinstance(result, Like)
    assert result.track_id == 777
    mock_session.add.assert_called_once()
    assert mock_session.commit.called
    assert mock_session.refresh.called

@pytest.mark.asyncio
async def test_toggle_like_delete(mock_session, mock_current_user, mock_request):
    """Сценарий: лайк уже есть, он должен удалиться (204 No Content)."""
    like_data = LikeData(track_id=777)
    existing_like = Like(id=10, user_id=1, track_id=777)
    
    # Имитируем, что лайк найден
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing_like
    mock_session.execute.return_value = mock_result

    result = await toggle_like(mock_request, like_data, mock_current_user, mock_session)

    # Проверяем удаление
    assert isinstance(result, Response)
    assert result.status_code == status.HTTP_204_NO_CONTENT
    mock_session.delete.assert_called_once_with(existing_like)
    assert mock_session.commit.called

@pytest.mark.asyncio
async def test_toggle_like_db_exception(mock_session, mock_current_user, mock_request):
    """Проверка устойчивости при ошибке БД."""
    like_data = LikeData(track_id=777)
    mock_session.execute.side_effect = Exception("DB Error")

    with pytest.raises(Exception):
        await toggle_like(mock_request, like_data, mock_current_user, mock_session)