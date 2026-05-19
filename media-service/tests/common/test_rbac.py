import pytest
import jwt
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from unittest.mock import patch, MagicMock
from src.common.rbac import parse_bool, verify_access_token, get_current_superuser, CurrentUser, get_current_user

@pytest.mark.parametrize("value, expected", [
    (True, True),
    (False, False),
    ("true", True),
    ("TRUE", True),
    ("1", True),
    ("yes", True),
    ("on", True),
    ("false", False),
    ("0", False),
    (1, True),
    (0, False),
    (None, False),
    ([], False),
])
def test_parse_bool(value, expected):
    assert parse_bool(value) is expected


@pytest.fixture
def mock_credentials():
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials="fake_token")

@patch("src.common.rbac.jwt.decode")
@patch("src.common.rbac.settings")
def test_verify_access_token_success(mock_settings, mock_decode, mock_credentials):
    mock_settings.JWT_SECRET_KEY = "secret"
    mock_settings.JWT_ALGORITHM = "HS256"
    mock_decode.return_value = {"sub": "123", "is_superuser": "true"}

    result = verify_access_token(mock_credentials)

    assert isinstance(result, CurrentUser)
    assert result.id == 123
    assert result.is_superuser is True
    mock_decode.assert_called_once()

@patch("src.common.rbac.jwt.decode")
@patch("src.common.rbac.settings")
def test_verify_access_token_no_sub(mock_settings, mock_decode, mock_credentials):
    mock_decode.return_value = {"is_superuser": True} 

    with pytest.raises(HTTPException) as exc:
        verify_access_token(mock_credentials)
    
    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "field not found" in exc.value.detail

@patch("src.common.rbac.jwt.decode")
def test_verify_access_token_expired(mock_decode, mock_credentials):
    mock_decode.side_effect = jwt.ExpiredSignatureError("Token expired")

    with pytest.raises(HTTPException) as exc:
        verify_access_token(mock_credentials)
    
    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "expired" in exc.value.detail

@patch("src.common.rbac.jwt.decode")
def test_verify_access_token_invalid(mock_decode, mock_credentials):
    mock_decode.side_effect = jwt.InvalidTokenError("Invalid token")

    with pytest.raises(HTTPException) as exc:
        verify_access_token(mock_credentials)
    
    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED

@patch("src.common.rbac.jwt.decode")
def test_verify_access_token_general_exception(mock_decode, mock_credentials):
    mock_decode.side_effect = Exception("Unknown error")

    with pytest.raises(HTTPException) as exc:
        verify_access_token(mock_credentials)
    
    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_get_current_superuser_success():
    user = CurrentUser(id=1, is_superuser=True)
    result = await get_current_superuser(current_user=user)
    assert result == user

@pytest.mark.asyncio
async def test_get_current_superuser_denied():
    user = CurrentUser(id=1, is_superuser=False)
    
    with pytest.raises(HTTPException) as exc:
        await get_current_superuser(current_user=user)
    
    assert exc.value.status_code == status.HTTP_403_FORBIDDEN
    assert "Access denied" in exc.value.detail


@pytest.mark.asyncio
async def test_get_current_user_passthrough():
    user = CurrentUser(id=1, is_superuser=False)
    result = await get_current_user(current_user=user, session=MagicMock())
    assert result == user