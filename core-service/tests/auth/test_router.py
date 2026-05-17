import pytest
from fastapi import HTTPException, status, Request, BackgroundTasks
from unittest.mock import AsyncMock, patch, MagicMock
from src.auth.router import register, login, refresh, logout, forgot_password, reset_password
from src.users.schemas import UserRegister
from src.models import User, RefreshToken
from src.auth.schemas import TokenPairResponse, ResetTokenRequest, ForgotPasswordRequest
from datetime import datetime, timezone
import jwt

LONG_SECRET = "super_secret_key_at_least_32_characters_long_12345"

@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.add = MagicMock()  
    return session

@pytest.fixture
def mock_request():
    return MagicMock(spec=Request)

@pytest.fixture
def mock_bg_tasks():
    return MagicMock(spec=BackgroundTasks)

@pytest.mark.asyncio
async def test_register_success(mock_session, mock_request):
    user_data = UserRegister(username="newuser", email="test@test.com", password="password123")
    
    with patch("src.auth.router.get_user_by_username", new_callable=AsyncMock) as mock_get_name, \
         patch("src.auth.router.get_user_by_email", new_callable=AsyncMock) as mock_get_email, \
         patch("src.auth.router.pwd_context.hash") as mock_hash:
        
        mock_get_name.return_value = None
        mock_get_email.return_value = None
        mock_hash.return_value = "hashed_password"
        
        result = await register(request=mock_request, user=user_data, session=mock_session)
        
        assert result.username == "newuser"
        assert result.hashed_password == "hashed_password"
        mock_session.add.assert_called_once()
        assert mock_session.commit.called

@pytest.mark.asyncio
async def test_register_username_conflict(mock_session, mock_request):
    user_data = UserRegister(username="exists", email="test@test.com", password="password")
    
    with patch("src.auth.router.get_user_by_username", new_callable=AsyncMock) as mock_get_name:
        mock_get_name.return_value = User(id=1, username="exists")
        
        with pytest.raises(HTTPException) as exc:
            await register(request=mock_request, user=user_data, session=mock_session)
        
        assert exc.value.status_code == status.HTTP_409_CONFLICT
        assert "username already exists" in exc.value.detail

@pytest.mark.asyncio
async def test_login_success_under_limit(mock_session, mock_request):
    """Логин, когда количество сессий не превышено."""
    mock_user = User(id=1, username="testuser")
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [] 
    mock_session.execute.return_value = mock_result

    with patch("src.auth.router.create_tokens", new_callable=AsyncMock) as mock_create_tokens, \
         patch("src.auth.router.settings") as mock_settings:
        
        mock_settings.JWT_MAX_SESSIONS = 5
        mock_create_tokens.return_value = ("access_val", "refresh_val")
        
        result = await login(request=mock_request, user=mock_user, session=mock_session)
        
        assert isinstance(result, TokenPairResponse)
        assert result.access_token == "access_val"
        assert result.refresh_token == "refresh_val"

@pytest.mark.asyncio
async def test_login_session_limit_reached(mock_session, mock_request):
    """Логин, когда достигнут лимит сессий (старая должна деактивироваться)."""
    mock_user = User(id=1, username="testuser")
    
    old_token = RefreshToken(id=1, user_id=1, is_active=True, exp=None)
    
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [old_token, RefreshToken(id=2)]
    mock_session.execute.return_value = mock_result

    with patch("src.auth.router.create_tokens", new_callable=AsyncMock) as mock_create_tokens, \
         patch("src.auth.router.settings") as mock_settings:
        
        mock_settings.JWT_MAX_SESSIONS = 2
        mock_create_tokens.return_value = ("new_acc", "new_ref")
        
        await login(request=mock_request, user=mock_user, session=mock_session)
        
        assert old_token.is_active is False
        assert mock_session.commit.called

@pytest.mark.asyncio
async def test_login_exception(mock_session, mock_request):
    mock_user = User(id=1)
    mock_session.execute.side_effect = Exception("Database crash")
    
    with pytest.raises(HTTPException) as exc:
        await login(request=mock_request, user=mock_user, session=mock_session)
    
    assert exc.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "Failed login" in exc.value.detail

@pytest.mark.asyncio
async def test_refresh_success(mock_session, mock_request):
    test_token_str = "valid_old_token"
    mock_refresh_db = RefreshToken(id=1, user_id=10, hashed_token="hashed")
    mock_user = User(id=10, is_active=True)

    with patch("src.auth.router.get_refresh_token_from_db", new_callable=AsyncMock) as mock_get_db, \
         patch("src.auth.router.create_tokens", new_callable=AsyncMock) as mock_create, \
         patch("src.auth.router.set_inactive_refresh_token", new_callable=AsyncMock) as mock_set_inactive:
        
        mock_get_db.return_value = mock_refresh_db
        mock_session.get.return_value = mock_user
        mock_create.return_value = ("new_access", "new_refresh")

        result = await refresh(request=mock_request, token_data=test_token_str, session=mock_session)

        mock_get_db.assert_called_once_with(token=test_token_str, session=mock_session)
        mock_session.get.assert_called_once_with(User, 10)
        mock_set_inactive.assert_called_once_with(refresh_token=mock_refresh_db, session=mock_session)
        
        assert isinstance(result, TokenPairResponse)
        assert result.access_token == "new_access"
        assert result.refresh_token == "new_refresh"

@pytest.mark.asyncio
async def test_refresh_user_not_found_or_inactive(mock_session, mock_request):
    """Ошибка, если пользователь не найден или заблокирован."""
    mock_refresh_db = RefreshToken(id=1, user_id=10)
    
    with patch("src.auth.router.get_refresh_token_from_db", new_callable=AsyncMock) as mock_get_db:
        mock_get_db.return_value = mock_refresh_db
        mock_session.get.return_value = None

        with pytest.raises(HTTPException) as exc:
            await refresh(request=mock_request, token_data="token", session=mock_session)
        
        assert exc.value.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in exc.value.detail

@pytest.mark.asyncio
async def test_logout_success(mock_session, mock_request):
    """Успешный логаут."""
    test_token_str = "logout_token"
    mock_refresh_db = RefreshToken(id=1, user_id=10)

    with patch("src.auth.router.get_refresh_token_from_db", new_callable=AsyncMock) as mock_get_db, \
         patch("src.auth.router.set_inactive_refresh_token", new_callable=AsyncMock) as mock_set_inactive:
        
        mock_get_db.return_value = mock_refresh_db

        result = await logout(request=mock_request, token_data=test_token_str, session=mock_session)

        assert result == {'message': 'Successful logout'}
        mock_set_inactive.assert_called_once_with(refresh_token=mock_refresh_db, session=mock_session)

@pytest.mark.asyncio
async def test_logout_token_not_found(mock_session, mock_request):
    """Ошибка, если токен не найден в базе (хотя прошел verify_refresh_token)."""
    with patch("src.auth.router.get_refresh_token_from_db", new_callable=AsyncMock) as mock_get_db:
        mock_get_db.return_value = None

        with pytest.raises(HTTPException) as exc:
            await logout(request=mock_request, token_data="unknown", session=mock_session)
        
        assert exc.value.status_code == status.HTTP_404_NOT_FOUND
        assert "Refresh token not found" in exc.value.detail

@pytest.mark.asyncio
@patch("src.auth.router.settings")
async def test_forgot_password_success(mock_settings, mock_session, mock_bg_tasks):
    mock_settings.JWT_SECRET_KEY = LONG_SECRET
    mock_settings.JWT_ALGORITHM = "HS256"
    mock_settings.JWT_RESET_TOKEN_EXPIRE_MINUTES = 15
    
    data = ForgotPasswordRequest(email="user@test.com")
    mock_user = User(id=1, email="user@test.com", is_superuser=False)

    with patch("src.auth.router.get_user_by_email", new_callable=AsyncMock) as mock_get_email:
        mock_get_email.return_value = mock_user
        
        result = await forgot_password(data, mock_bg_tasks, mock_session)
        
        assert result == {'message': 'Send reset link to email'}
        assert mock_bg_tasks.add_task.called
        _, kwargs = mock_bg_tasks.add_task.call_args
        assert kwargs['email_to'] == "user@test.com"
        assert 'token' in kwargs

@pytest.mark.asyncio
async def test_forgot_password_user_not_found(mock_session, mock_bg_tasks):
    data = ForgotPasswordRequest(email="nonexistent@test.com")
    
    with patch("src.auth.router.get_user_by_email", new_callable=AsyncMock) as mock_get_email:
        mock_get_email.return_value = None
        result = await forgot_password(data, mock_bg_tasks, mock_session)
        
        assert result == {'message': 'Send reset link to email'}
        assert not mock_bg_tasks.add_task.called

@pytest.mark.asyncio
@patch("src.auth.router.settings")
async def test_reset_password_success(mock_settings, mock_session):
    mock_settings.JWT_SECRET_KEY = LONG_SECRET
    mock_settings.JWT_ALGORITHM = "HS256"
    
    token = jwt.encode(
        {'sub': '10', 'exp': datetime.now(timezone.utc).timestamp() + 1000},
        key=LONG_SECRET,
        algorithm="HS256"
    )
    
    reset_data = ResetTokenRequest(token=token, new_password="new_secure_password")
    mock_user = User(id=10, username="testuser", is_active=True)

    with patch("src.auth.router.pwd_context.hash", return_value="new_hashed_pass"), \
         patch("src.auth.router.clear_all_refresh_tokens", new_callable=AsyncMock) as mock_clear:
        
        mock_session.get.return_value = mock_user
        
        result = await reset_password(reset_data, mock_session)
        
        assert result == {'message': 'Password updated successfully'}
        mock_clear.assert_called_once_with(user_id=10, session=mock_session)
        assert mock_session.commit.called

@pytest.mark.asyncio
@patch("src.auth.router.settings")
async def test_reset_password_expired_token(mock_settings, mock_session):
    mock_settings.JWT_SECRET_KEY = LONG_SECRET
    mock_settings.JWT_ALGORITHM = "HS256"
    
    token = jwt.encode(
        {'sub': '10', 'exp': datetime.now(timezone.utc).timestamp() - 1000},
        key=LONG_SECRET,
        algorithm="HS256"
    )
    reset_data = ResetTokenRequest(token=token, new_password="123")

    with pytest.raises(HTTPException) as exc:
        await reset_password(reset_data, mock_session)
    
    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "expired" in exc.value.detail

@pytest.mark.asyncio
@patch("src.auth.router.settings")
async def test_reset_password_user_not_found(mock_settings, mock_session):
    """
    Тест ожидает 401, так как в роутере блок except Exception перехватывает 
    404 ошибку и превращает её в 401.
    """
    mock_settings.JWT_SECRET_KEY = LONG_SECRET
    mock_settings.JWT_ALGORITHM = "HS256"
    
    token = jwt.encode({'sub': '99', 'exp': datetime.now(timezone.utc).timestamp() + 100}, key=LONG_SECRET, algorithm="HS256")
    reset_data = ResetTokenRequest(token=token, new_password="123")
    
    mock_session.get.return_value = None

    with pytest.raises(HTTPException) as exc:
        await reset_password(reset_data, mock_session)
    
    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "User with 99 not found" in exc.value.detail