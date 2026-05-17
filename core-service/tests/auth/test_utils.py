import pytest
import jwt
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock, AsyncMock
from src.auth.utils import (
    hash_token, 
    gen_token, 
    check_token_expired, 
    check_token_inactive, 
    create_access_token, 
    create_refresh_token,
    clear_all_refresh_tokens, 
    set_inactive_refresh_token, 
    get_refresh_token_from_db, 
    send_reset_password_email
)
from src.models import User, RefreshToken

def test_hash_token():
    token = "test_token_123"
    expected = hashlib.sha256(token.encode()).hexdigest()
    assert hash_token(token) == expected

def test_gen_token():
    token = gen_token()
    assert isinstance(token, str)
    assert len(token) > 60 

def test_check_token_expired():
    expired_time = datetime.now(timezone.utc) - timedelta(minutes=10)
    token = RefreshToken(id=1, user_id=99, exp=expired_time)
    
    assert check_token_expired(token) is True

def test_check_token_not_expired():
    future_time = datetime.now(timezone.utc) + timedelta(minutes=10)
    token = RefreshToken(id=1, user_id=99, exp=future_time)
    
    assert check_token_expired(token) is False

def test_check_token_inactive():
    token_active = RefreshToken(id=1, is_active=True)
    token_inactive = RefreshToken(id=2, is_active=False)
    
    assert check_token_inactive(token_active) is False
    assert check_token_inactive(token_inactive) is True

@patch("src.auth.utils.settings")
def test_create_access_token(mock_settings):
    mock_settings.JWT_SECRET_KEY = "super_secret_key_that_is_at_least_32_characters_long"
    mock_settings.JWT_ALGORITHM = "HS256"
    mock_settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 15

    user = User(id=42, is_superuser=True)
    
    token_str = create_access_token(user)
    
    decoded = jwt.decode(token_str, key="super_secret_key_that_is_at_least_32_characters_long", algorithms=["HS256"])
    
    assert decoded["sub"] == "42"
    assert decoded["is_superuser"] == "True" 
    assert "exp" in decoded

@patch("src.auth.utils.settings")
def test_create_refresh_token(mock_settings):
    mock_settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS = 30
    user_id = 10
    
    raw_token, token_db = create_refresh_token(user_id)
    
    assert isinstance(raw_token, str)
    assert isinstance(token_db, RefreshToken)
    
    assert token_db.user_id == user_id
    assert token_db.hashed_token == hashlib.sha256(raw_token.encode()).hexdigest()
    
    expected_date = datetime.now(timezone.utc) + timedelta(days=30)
    assert abs((token_db.exp - expected_date).total_seconds()) < 5


@pytest.fixture
def mock_session():
    return AsyncMock()

@pytest.mark.asyncio
async def test_clear_all_refresh_tokens(mock_session):
    user_id = 1
    await clear_all_refresh_tokens(user_id, mock_session)
    
    assert mock_session.execute.called
    assert mock_session.commit.called
    
    with patch("src.auth.utils.logger.success") as mock_log:
        await clear_all_refresh_tokens(user_id, mock_session)
        mock_log.assert_called_with(f'All refresh token for user ({user_id}) delete')

@pytest.mark.asyncio
async def test_set_inactive_refresh_token(mock_session):
    token = RefreshToken(id=10, user_id=1, is_active=True)
    
    await set_inactive_refresh_token(token, mock_session)
    
    assert token.is_active is False
    assert isinstance(token.exp, datetime)
    assert mock_session.commit.called
    assert mock_session.refresh.called
    mock_session.refresh.assert_called_with(token)

@pytest.mark.asyncio
async def test_get_refresh_token_from_db_found(mock_session):
    raw_token = "some_raw_token"
    mock_token_obj = RefreshToken(id=1, hashed_token="hashed_val")
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_token_obj
    mock_session.execute.return_value = mock_result
    
    result = await get_refresh_token_from_db(raw_token, mock_session)
    
    assert result == mock_token_obj
    assert mock_session.execute.called

@pytest.mark.asyncio
async def test_get_refresh_token_from_db_not_found(mock_session):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    
    with patch("src.auth.utils.logger.warning") as mock_log:
        result = await get_refresh_token_from_db("invalid", mock_session)
        
        assert result is None
        mock_log.assert_called_once_with('Refresh token not found')

@patch("src.auth.utils.smtplib.SMTP_SSL")
@patch("src.auth.utils.settings")
def test_send_reset_password_email(mock_settings, mock_smtp_class):
    mock_settings.SMTP_USER = "admin@mray.com"
    mock_settings.SMTP_HOST = "smtp.mray.com"
    mock_settings.SMTP_PORT = 465
    mock_settings.SMTP_PASSWORD = "password123"
    
    mock_smtp_instance = MagicMock()
    mock_smtp_class.return_value.__enter__.return_value = mock_smtp_instance
    
    email_to = "user@example.com"
    token = "secret-reset-token"
    
    send_reset_password_email(email_to, token)
    
    mock_smtp_class.assert_called_once_with(host=mock_settings.SMTP_HOST, port=mock_settings.SMTP_PORT)
    
    mock_smtp_instance.login.assert_called_once_with(user=mock_settings.SMTP_USER, password=mock_settings.SMTP_PASSWORD)
    
    assert mock_smtp_instance.send_message.called
    sent_msg = mock_smtp_instance.send_message.call_args.kwargs['msg']
    
    assert sent_msg['To'] == email_to
    assert sent_msg['Subject'] == 'Reset password - MRay music app'
    assert token in sent_msg.get_content()
    assert "http://localhost:3000/auth/password/reset" in sent_msg.get_content()