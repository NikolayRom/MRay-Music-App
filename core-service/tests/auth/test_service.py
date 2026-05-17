import pytest
import jwt
from fastapi import HTTPException, status
from fastapi.security import HTTPBasicCredentials, HTTPAuthorizationCredentials
from unittest.mock import AsyncMock, patch, MagicMock
from src.auth.service import authenticate, create_tokens, verify_refresh_token
from src.models import User, RefreshToken

@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.add = MagicMock()
    return session

@pytest.mark.asyncio
async def test_authenticate_success(mock_session):
    credentials = HTTPBasicCredentials(username="testuser", password="password123")
    mock_user = User(id=1, username="testuser", hashed_password="hashed_val")

    with patch("src.auth.service.get_user_by_username", new_callable=AsyncMock) as mock_get_user:
        mock_get_user.return_value = mock_user
        
        with patch("src.auth.service.pwd_context.verify") as mock_verify:
            mock_verify.return_value = True
            
            result = await authenticate(credentials, mock_session)
            
            assert result == mock_user
            mock_get_user.assert_called_once_with(username="testuser", session=mock_session)

@pytest.mark.asyncio
async def test_authenticate_user_not_found(mock_session):
    credentials = HTTPBasicCredentials(username="ghost", password="password")
    
    with patch("src.auth.service.get_user_by_username", new_callable=AsyncMock) as mock_get_user:
        mock_get_user.return_value = None
        
        with pytest.raises(HTTPException) as exc:
            await authenticate(credentials, mock_session)
        
        assert exc.value.status_code == status.HTTP_404_NOT_FOUND
        assert "User not found" in exc.value.detail

@pytest.mark.asyncio
async def test_authenticate_wrong_password(mock_session):
    credentials = HTTPBasicCredentials(username="user", password="wrong_password")
    mock_user = User(id=1, username="user", hashed_password="hashed_val")

    with patch("src.auth.service.get_user_by_username", new_callable=AsyncMock) as mock_get_user:
        mock_get_user.return_value = mock_user
        
        with patch("src.auth.service.pwd_context.verify") as mock_verify:
            mock_verify.return_value = False
            
            with pytest.raises(HTTPException) as exc:
                await authenticate(credentials, mock_session)
            
            assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Incorrect password" in exc.value.detail

@pytest.mark.asyncio
async def test_create_tokens(mock_session):
    user = User(id=1, is_superuser=False)
    
    with patch("src.auth.service.create_access_token") as mock_access, \
         patch("src.auth.service.create_refresh_token") as mock_refresh:
        
        mock_access.return_value = "access_token_str"
        mock_refresh_obj = RefreshToken(id=1, user_id=1)
        mock_refresh.return_value = ("refresh_token_str", mock_refresh_obj)
        
        access, refresh = await create_tokens(user, mock_session)
        
        assert access == "access_token_str"
        assert refresh == "refresh_token_str"
        
        mock_session.add.assert_called_once_with(mock_refresh_obj)
        assert mock_session.commit.called
        assert mock_session.refresh.called

@pytest.mark.asyncio
async def test_verify_refresh_token_success(mock_session):
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="valid_token")
    mock_token_data = RefreshToken(id=1, user_id=1)

    with patch("src.auth.service.get_refresh_token_from_db", new_callable=AsyncMock) as mock_get_db:
        mock_get_db.return_value = mock_token_data
        
        with patch("src.auth.service.check_token_inactive", return_value=False), \
             patch("src.auth.service.check_token_expired", return_value=False):
            
            result = await verify_refresh_token(creds, mock_session)
            assert result == "valid_token"

@pytest.mark.asyncio
async def test_verify_refresh_token_not_found(mock_session):
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="unknown_token")

    with patch("src.auth.service.get_refresh_token_from_db", new_callable=AsyncMock) as mock_get_db:
        mock_get_db.return_value = None  
        
        with pytest.raises(HTTPException) as exc:
            await verify_refresh_token(creds, mock_session)
        
        assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Refresh token not found" in exc.value.detail

@pytest.mark.asyncio
async def test_verify_refresh_token_theft_suspicion(mock_session):
    """Тест критического сценария: токен уже неактивен (подозрение на кражу)."""
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="stolen_token")
    mock_token_data = RefreshToken(id=1, user_id=99)

    with patch("src.auth.service.get_refresh_token_from_db", new_callable=AsyncMock) as mock_get_db:
        mock_get_db.return_value = mock_token_data
        
        with patch("src.auth.service.check_token_inactive", return_value=True), \
             patch("src.auth.service.clear_all_refresh_tokens", new_callable=AsyncMock) as mock_clear_all:
            
            with pytest.raises(HTTPException) as exc:
                await verify_refresh_token(creds, mock_session)
            
            assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
            mock_clear_all.assert_called_once_with(user_id=99, session=mock_session)

@pytest.mark.asyncio
async def test_verify_refresh_token_expired(mock_session):
    """Тест сценария истечения срока действия токена."""
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="expired_token")
    mock_token_data = RefreshToken(id=1, user_id=1)

    with patch("src.auth.service.get_refresh_token_from_db", new_callable=AsyncMock) as mock_get_db:
        mock_get_db.return_value = mock_token_data
        
        with patch("src.auth.service.check_token_inactive", return_value=False), \
             patch("src.auth.service.check_token_expired", return_value=True), \
             patch("src.auth.service.set_inactive_refresh_token", new_callable=AsyncMock) as mock_set_inactive:
            
            with pytest.raises(HTTPException) as exc:
                await verify_refresh_token(creds, mock_session)
            
            assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
            mock_set_inactive.assert_called_once_with(refresh_token=mock_token_data, session=mock_session)