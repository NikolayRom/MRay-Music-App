import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.users.utils import get_user_by_username, get_user_by_email
from src.models import User

@pytest.fixture
def mock_session():
    return AsyncMock()

@pytest.mark.asyncio
async def test_get_user_by_username_success(mock_session):
    mock_user = User(id=1, username="test_user")
    
    # Мокаем результат execute().scalar_one_or_none()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_session.execute.return_value = mock_result

    # Проверяем вызов
    result = await get_user_by_username("test_user", mock_session)
    
    assert result == mock_user
    assert mock_session.execute.called
    # Проверка, что в запросе участвует фильтр по username
    args, _ = mock_session.execute.call_args
    query_str = str(args[0])
    assert "users.username = :username_1" in query_str

@pytest.mark.asyncio
async def test_get_user_by_username_not_found(mock_session):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    with patch("src.users.utils.logger.warning") as mock_log:
        result = await get_user_by_username("ghost", mock_session)
        
        assert result is None
        mock_log.assert_called_once_with('User with ghost username not found')

@pytest.mark.asyncio
async def test_get_user_by_email_success(mock_session):
    mock_user = User(id=1, email="test@test.com")
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_session.execute.return_value = mock_result

    result = await get_user_by_email("test@test.com", mock_session)
    
    assert result == mock_user
    assert mock_session.execute.called
    # Проверка, что в запросе участвует фильтр по email
    args, _ = mock_session.execute.call_args
    assert "users.email = :email_1" in str(args[0])

@pytest.mark.asyncio
async def test_get_user_by_email_not_found(mock_session):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    with patch("src.users.utils.logger.warning") as mock_log:
        result = await get_user_by_email("wrong@test.com", mock_session)
        
        assert result is None
        mock_log.assert_called_once()