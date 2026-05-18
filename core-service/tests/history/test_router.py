import pytest
from datetime import datetime, timezone
from fastapi import HTTPException, status, Response
from unittest.mock import AsyncMock, MagicMock, patch
from src.history.router import get_all_history, get_history, post_history, delete_history
from src.models import UserHistory
from src.common.rbac import CurrentUser
from src.history.schemas import HistoryPost, HistoryDelete

@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.add = MagicMock()
    session.delete = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    return session

@pytest.fixture
def mock_current_user():
    return CurrentUser(id=1, is_superuser=False)

@pytest.fixture
def mock_request():
    return MagicMock()

@pytest.mark.asyncio
async def test_get_all_history_success(mock_session, mock_current_user, mock_request):
    now = datetime.now(timezone.utc)
    fake_history = [
        UserHistory(id=1, user_id=1, track_id=10, created_at=now),
        UserHistory(id=2, user_id=1, track_id=20, created_at=now)
    ]
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = fake_history
    mock_session.execute.return_value = mock_result

    result = await get_all_history(mock_request, mock_current_user, mock_session)

    assert len(result.items) == 2
    assert result.items[0].track_id == 10
    assert isinstance(result.items[0].created_at, datetime)

@pytest.mark.asyncio
async def test_get_history_found(mock_session, mock_current_user, mock_request):
    now = datetime.now(timezone.utc)
    fake_item = UserHistory(id=1, user_id=1, track_id=100, created_at=now)
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = fake_item
    mock_session.execute.return_value = mock_result

    result = await get_history(mock_request, 100, mock_current_user, mock_session)
    assert result.track_id == 100

@pytest.mark.asyncio
async def test_get_history_not_found(mock_session, mock_current_user, mock_request):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    with pytest.raises(HTTPException) as exc:
        await get_history(mock_request, 999, mock_current_user, mock_session)
    assert exc.value.status_code == 404

@pytest.mark.asyncio
async def test_post_history_new_item(mock_session, mock_current_user, mock_request):
    history_data = HistoryPost(track_id=50)
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    result = await post_history(mock_request, history_data, mock_current_user, mock_session)

    assert isinstance(result, UserHistory)
    assert result.track_id == 50
    mock_session.add.assert_called_once()
    assert mock_session.commit.called

@pytest.mark.asyncio
async def test_post_history_update_existing(mock_session, mock_current_user, mock_request):
    history_data = HistoryPost(track_id=50)
    old_time = datetime(2020, 1, 1, tzinfo=timezone.utc)
    existing_item = UserHistory(id=1, user_id=1, track_id=50, created_at=old_time)
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing_item
    mock_session.execute.return_value = mock_result

    result = await post_history(mock_request, history_data, mock_current_user, mock_session)

    assert result.track_id == 50
    assert result.created_at > old_time
    mock_session.add.assert_not_called()
    assert mock_session.commit.called

@pytest.mark.asyncio
async def test_delete_history_success(mock_session, mock_current_user, mock_request):
    history_data = HistoryDelete(track_id=50)
    existing_item = UserHistory(id=1, user_id=1, track_id=50)
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing_item
    mock_session.execute.return_value = mock_result

    result = await delete_history(mock_request, history_data, mock_current_user, mock_session)

    assert isinstance(result, Response)
    assert result.status_code == 204
    mock_session.delete.assert_called_once_with(existing_item)
    assert mock_session.commit.called

@pytest.mark.asyncio
async def test_delete_history_not_found(mock_session, mock_current_user, mock_request):
    history_data = HistoryDelete(track_id=50)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    with pytest.raises(HTTPException) as exc:
        await delete_history(mock_request, history_data, mock_current_user, mock_session)
    assert exc.value.status_code == 404